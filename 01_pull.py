"""
01_pull.py — Data acquisition.

Pulls raw time-series data from World Bank API (WDI db=2, WGI db=3) for all
54 AU member states. One series at a time so failed codes are skipped cleanly
without losing the rest of the pull.

Year window pulled: min(year_start) - 5yr buffer to max(year_end), computed
dynamically from indicator definitions. The per-indicator windows are applied
in 02_clean.py — this module just acquires the full raw range.

Requires internet access. Run from the project root:
    python 01_pull.py

Output: data/01_raw_pull.xlsx
  coverage_report  — per-indicator data availability, sorted by coverage asc
  raw_data         — long-format {iso3, variable_name, year, value}
  pull_log         — per-series status, timing, error messages
"""

import sys
import os
import logging
import time as _time

# Windows SSL fix: patch requests.Session before wbgapi loads so that all
# API calls in this process skip certificate verification.
# Needed when a corporate/system proxy replaces certificates with a local CA
# that Python's ssl module doesn't recognise.
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
_orig_merge = requests.Session.merge_environment_settings
def _no_ssl_merge(self, url, proxies, stream, verify, cert):
    settings = _orig_merge(self, url, proxies, stream, verify, cert)
    settings["verify"] = False
    return settings
requests.Session.merge_environment_settings = _no_ssl_merge

import wbgapi as wb
import pandas as pd
from pathlib import Path

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-8s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── Imports ───────────────────────────────────────────────────────────────────

from asi.core.registry import (
    PillarRegistry, IndicatorRegistry,
    COVERAGE_WARN_THRESHOLD, COVERAGE_ALERT_THRESHOLD,
)
from asi.core.countries import COUNTRIES

OUTPUT_DIR  = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "01_raw_pull.xlsx"

# Transient API error handling: 502/504/524 are World Bank rate-limiting or
# infrastructure errors unrelated to the series code. Three retries with
# exponential backoff give the server time to recover.
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 15  # seconds; doubles each attempt (15 → 30 → 60)

# ── Registry ──────────────────────────────────────────────────────────────────

pr = PillarRegistry()
ir = IndicatorRegistry(pr)

if not ir.validate_all():
    logger.error("Registry validation failed — run pytest tests/ to diagnose.")
    sys.exit(1)

indicators = ir.build_indicators()
iso3_list  = list(COUNTRIES.keys())   # 54 AU member states

wdi_inds = {k: v for k, v in indicators.items() if v.database == "wdi"}
wgi_inds = {k: v for k, v in indicators.items() if v.database == "wgi"}

# Pull window: earliest year_start - 5yr buffer (supports Stage 1 fill in 02_clean)
def _pull_window(inds: dict) -> tuple[int, int]:
    return (
        min(v.year_start for v in inds.values()) - 5,
        max(v.year_end   for v in inds.values()),
    )

wdi_start, wdi_end = _pull_window(wdi_inds)
wgi_start, wgi_end = _pull_window(wgi_inds)

logger.info("Pull plan:")
logger.info("  WDI (%d indicators): years %d-%d", len(wdi_inds), wdi_start, wdi_end)
logger.info("  WGI (%d indicators): years %d-%d", len(wgi_inds), wgi_start, wgi_end)
logger.info("  Countries: %d", len(iso3_list))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _coerce_year_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    wbgapi may return columns as 'YR2015' strings, Time objects, or plain ints.
    Normalise all to plain Python int.
    """
    mapping = {}
    for col in df.columns:
        s = str(col)
        candidate = s[2:] if s.startswith("YR") else s
        try:
            mapping[col] = int(float(candidate))
        except (ValueError, TypeError):
            pass   # non-year column — leave as-is
    return df.rename(columns=mapping)


def pull_series(
    series_code: str,
    variable_name: str,
    db_id: int,
    year_start: int,
    year_end: int,
    iso3_list: list[str],
) -> tuple[pd.DataFrame | None, str]:
    """
    Pull one series with retry logic. Returns (long_df, status_message).
    long_df columns: iso3, variable_name, year, value.
    NaN rows are dropped — only country-years with actual data are kept.
    Sets wb.db internally so the caller does not need to manage database state.

    Retries on 502, 504, and 524 HTTP errors (World Bank transient failures).
    Other exceptions (invalid series code, JSON decode error) fail immediately.
    """
    _TRANSIENT_CODES = ("502", "504", "524", "timeout")

    for attempt in range(MAX_RETRIES + 1):
        wb.db = db_id
        try:
            df = wb.data.DataFrame(
                series_code,
                economy=iso3_list,
                time=range(year_start, year_end + 1),
            )
            break  # success — exit retry loop
        except Exception as exc:
            msg = str(exc)
            is_transient = any(code in msg for code in _TRANSIENT_CODES)
            if is_transient and attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_BASE * (2 ** attempt)
                logger.warning(
                    "  RETRY %d/%d %s (%.0fs): %s",
                    attempt + 1, MAX_RETRIES, variable_name, wait, msg[:120],
                )
                _time.sleep(wait)
                continue
            return None, msg
    else:
        return None, f"failed after {MAX_RETRIES} retries"

    if df is None or df.empty:
        return None, "no data returned by API"

    df.index.name = "iso3"
    df = _coerce_year_columns(df)

    year_cols = [c for c in df.columns if isinstance(c, int)]
    if not year_cols:
        return None, "no integer year columns after coercion — check series code"

    long = (
        df[year_cols]
          .reset_index()
          .melt(id_vars="iso3", var_name="year", value_name="value")
    )
    long["variable_name"] = variable_name
    long["year"]          = pd.to_numeric(long["year"], errors="coerce").astype("Int64")
    long = long.dropna(subset=["value"])

    if long.empty:
        return None, "all values are NaN for this series"

    return long[["iso3", "variable_name", "year", "value"]], "OK"


# ── Execute pulls ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows  = []
    pull_logs = []
    t_total   = _time.perf_counter()

    for db_id, inds, y_start, y_end, db_label in [
        (2, wdi_inds, wdi_start, wdi_end, "WDI"),
        (3, wgi_inds, wgi_start, wgi_end, "WGI"),
    ]:
        logger.info("")
        logger.info("-- %s (wbgapi db=%d) %d-%d --", db_label, db_id, y_start, y_end)

        for var_name, ind in inds.items():
            t0      = _time.perf_counter()
            df, st  = pull_series(ind.series_code, var_name, db_id, y_start, y_end, iso3_list)
            elapsed = _time.perf_counter() - t0

            if st == "OK" and df is not None:
                all_rows.append(df)
                n_obs  = len(df)
                n_ctry = df["iso3"].nunique()
                logger.info(
                    "  OK   %-36s %5d obs  %2d/%d countries  (%.1fs)",
                    var_name, n_obs, n_ctry, len(iso3_list), elapsed,
                )
            else:
                n_obs  = 0
                n_ctry = 0
                logger.warning("  SKIP %-36s %s", var_name, st)

            pull_logs.append({
                "variable_name": var_name,
                "series_code":   ind.series_code,
                "database":      db_label,
                "status":        "OK" if st == "OK" else "FAILED",
                "n_obs":         n_obs,
                "n_countries":   n_ctry,
                "error":         "" if st == "OK" else st,
                "pull_seconds":  round(elapsed, 2),
            })

    # ── Assemble raw DataFrame ────────────────────────────────────────────────

    if not all_rows:
        logger.error("No data pulled at all. Check internet connection and series codes.")
        sys.exit(1)

    raw_df      = pd.concat(all_rows, ignore_index=True)
    pull_log_df = pd.DataFrame(pull_logs)
    n_failed    = int((pull_log_df["status"] == "FAILED").sum())

    logger.info("")
    logger.info("Total observations: %d", len(raw_df))
    logger.info(
        "Series: %d pulled OK, %d skipped",
        len(pull_logs) - n_failed, n_failed,
    )

    # ── Coverage report ───────────────────────────────────────────────────────

    n_total  = len(iso3_list)
    cov_rows = []

    for var_name, ind in indicators.items():
        subset = raw_df[raw_df["variable_name"] == var_name]
        n_ctry = int(subset["iso3"].nunique())
        pct    = n_ctry / n_total

        flag = ""
        if pct < COVERAGE_ALERT_THRESHOLD:
            flag = "VERY SPARSE"
        elif pct < COVERAGE_WARN_THRESHOLD:
            flag = "SPARSE"

        cov_rows.append({
            "variable_name":  var_name,
            "display_name":   ind.display_name,
            "pillars":        ",".join(ind.pillars),
            "database":       ind.database,
            "n_countries":    n_ctry,
            "pct_coverage":   round(pct, 3),
            "flag":           flag,
            "n_obs_total":    len(subset),
            "year_min_avail": int(subset["year"].min()) if n_ctry else None,
            "year_max_avail": int(subset["year"].max()) if n_ctry else None,
        })

    coverage_df = pd.DataFrame(cov_rows).sort_values("pct_coverage", ascending=True)

    logger.info("")
    logger.info("[COVERAGE REPORT] — will also be Sheet 1 of output file")

    very_sparse = coverage_df[coverage_df["flag"] == "VERY SPARSE"]
    sparse      = coverage_df[coverage_df["flag"] == "SPARSE"]
    full_cov    = coverage_df[coverage_df["flag"] == ""]

    if not very_sparse.empty:
        logger.warning("  VERY SPARSE (< %.0f%%): %d indicator(s)",
                       COVERAGE_ALERT_THRESHOLD * 100, len(very_sparse))
        for _, r in very_sparse.iterrows():
            logger.warning("    %-36s  %3.0f%%  (%d countries)",
                           r["variable_name"], r["pct_coverage"] * 100, r["n_countries"])

    if not sparse.empty:
        logger.warning("  SPARSE      (< %.0f%%): %d indicator(s)",
                       COVERAGE_WARN_THRESHOLD * 100, len(sparse))
        for _, r in sparse.iterrows():
            logger.warning("    %-36s  %3.0f%%  (%d countries)",
                           r["variable_name"], r["pct_coverage"] * 100, r["n_countries"])

    logger.info("  Full coverage (>= %.0f%%): %d indicator(s)",
                COVERAGE_WARN_THRESHOLD * 100, len(full_cov))

    # ── Write checkpoint ──────────────────────────────────────────────────────

    logger.info("")
    logger.info("Writing %s ...", OUTPUT_FILE)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        coverage_df.to_excel(writer, sheet_name="coverage_report", index=False)
        raw_df.to_excel(writer,      sheet_name="raw_data",        index=False)
        pull_log_df.to_excel(writer, sheet_name="pull_log",        index=False)

    elapsed_total = _time.perf_counter() - t_total
    logger.info("Done in %.0fs.", elapsed_total)
    logger.info("Output: %s", OUTPUT_FILE.resolve())
    logger.info("Sheets: coverage_report | raw_data | pull_log")
    logger.info("Next step: python 02_clean.py")
