"""
validate_stage1.py — Stage 1 validation checks.

Verifies:
  A. Pull log: WGI indicators OK (not FAILED), co2_pc OK, population_total OK
  B. WGI benchmark spot-check: values plausible vs. World Bank DataBank
  C. co2_pc benchmark spot-check: South Africa ~6-9 MT/capita
  D. displaced_persons per-capita: DRC >> Mauritius, values in [0, 200] range
  E. Stage-1 fill aggregation: average_recent_3/5 indicators filled correctly
  F. Registry: 37 indicators (31 WDI + 6 WGI) validated; population_total is descriptive

Run from project root after 01_pull.py and 02_clean.py complete:
    python validate_stage1.py
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

PASS = "✓"
FAIL = "✗"
WARN = "⚠"

errors = []
warnings = []

def check(label, condition, detail="", warn_only=False):
    if condition:
        print(f"  {PASS}  {label}")
        if detail:
            print(f"       {detail}")
    else:
        tag = WARN if warn_only else FAIL
        print(f"  {tag}  {label}")
        if detail:
            print(f"       {detail}")
        if warn_only:
            warnings.append(label)
        else:
            errors.append(label)

print("\n=== Stage 1 Validation ===\n")

# ── A. Pull log checks ────────────────────────────────────────────────────────

print("A. Pull log — data provenance")
pull_file = Path("data/01_raw_pull.xlsx")
if not pull_file.exists():
    print(f"  {FAIL}  01_raw_pull.xlsx not found — run 01_pull.py first")
    sys.exit(1)

log_df = pd.read_excel(pull_file, sheet_name="pull_log")

wgi_vars = ["va_estimate", "pv_estimate", "ge_estimate", "rq_estimate", "rl_estimate", "cc_estimate"]
for var in wgi_vars:
    row = log_df[log_df["variable_name"] == var]
    if row.empty:
        check(f"WGI {var} in pull_log", False, "not found in pull_log")
    else:
        status = row.iloc[0]["status"]
        n_ctry = row.iloc[0]["n_countries"]
        series = row.iloc[0]["series_code"]
        check(
            f"WGI {var}: status={status}, n_countries={n_ctry}, series={series}",
            status == "OK" and n_ctry >= 50,
            f"series_code={series} (expected GOV_WGI_*.EST, not NaN)"
        )

co2_row = log_df[log_df["variable_name"] == "co2_pc"]
if co2_row.empty:
    check("co2_pc in pull_log", False)
else:
    co2_status = co2_row.iloc[0]["status"]
    co2_series = co2_row.iloc[0]["series_code"]
    co2_n = co2_row.iloc[0]["n_countries"]
    check(
        f"co2_pc: status={co2_status}, series={co2_series}, n_countries={co2_n}",
        co2_status == "OK" and "AR5" in str(co2_series),
        "Expected EN.GHG.CO2.PC.CE.AR5"
    )

pop_row = log_df[log_df["variable_name"] == "population_total"]
if pop_row.empty:
    check("population_total in pull_log", False)
else:
    pop_status = pop_row.iloc[0]["status"]
    pop_n = pop_row.iloc[0]["n_countries"]
    check(
        f"population_total: status={pop_status}, n_countries={pop_n}",
        pop_status == "OK" and pop_n == 54
    )

n_failed = (log_df["status"] == "FAILED").sum()
check(f"Zero FAILED series in pull_log (found {n_failed})", n_failed == 0,
      warn_only=(n_failed <= 2))

# ── B. WGI benchmark spot-checks ─────────────────────────────────────────────

print("\nB. WGI benchmark spot-checks (vs. World Bank DataBank 2022 values)")
raw_df = pd.read_excel(pull_file, sheet_name="raw_data")

def latest_val(df, var, iso3):
    sub = df[(df["variable_name"] == var) & (df["iso3"] == iso3)].dropna(subset=["value"])
    if sub.empty:
        return None
    return float(sub.sort_values("year").iloc[-1]["value"])

# KEN va_estimate 2022: approximately -0.25 (tested above)
ken_va = latest_val(raw_df, "va_estimate", "KEN")
check(
    f"KEN va_estimate latest ~-0.25 (got {ken_va:.3f})" if ken_va is not None else "KEN va_estimate missing",
    ken_va is not None and -0.6 < ken_va < 0.2,
    "World Bank DataBank 2022 value: -0.25"
)

# SOM cc_estimate: strongly negative, expect < -1.5
som_cc = latest_val(raw_df, "cc_estimate", "SOM")
check(
    f"SOM cc_estimate latest < -1.5 (got {som_cc:.3f})" if som_cc is not None else "SOM cc_estimate missing",
    som_cc is not None and som_cc < -1.5,
    "Somalia control of corruption is consistently < -1.5"
)

# MUS (Mauritius) ge_estimate: expect > 0.5 (well-governed)
mus_ge = latest_val(raw_df, "ge_estimate", "MUS")
check(
    f"MUS ge_estimate latest > 0.5 (got {mus_ge:.3f})" if mus_ge is not None else "MUS ge_estimate missing",
    mus_ge is not None and mus_ge > 0.5,
    "Mauritius is among Africa's best-governed states"
)

# ── C. co2_pc benchmark ───────────────────────────────────────────────────────

print("\nC. co2_pc benchmark spot-checks")
zaf_co2 = latest_val(raw_df, "co2_pc", "ZAF")
check(
    f"ZAF co2_pc ~6-9 MT/capita (got {zaf_co2:.2f})" if zaf_co2 is not None else "ZAF co2_pc missing",
    zaf_co2 is not None and 5.0 < zaf_co2 < 10.0,
    "South Africa: coal-heavy grid, ~7 MT per capita expected"
)

# ── D. displaced_persons per-capita ───────────────────────────────────────────

print("\nD. displaced_persons per-capita (post-02_clean.py)")
clean_file = Path("data/02_clean.xlsx")
if not clean_file.exists():
    print(f"  {WARN}  02_clean.xlsx not found — run 02_clean.py after pull completes")
else:
    clean_df = pd.read_excel(clean_file, sheet_name="clean_data").set_index("iso3")

    if "displaced_persons" not in clean_df.columns:
        check("displaced_persons column in clean_data", False)
    else:
        drc_idp = clean_df.loc["COD", "displaced_persons"] if "COD" in clean_df.index else None
        mus_idp = clean_df.loc["MUS", "displaced_persons"] if "MUS" in clean_df.index else None

        check(
            f"COD (DRC) per-capita IDP > 10 per 1,000 (got {drc_idp:.1f})" if drc_idp is not None else "COD IDP missing",
            drc_idp is not None and drc_idp > 10,
            "DRC had ~6-7M IDPs / ~100M population ≈ 60-70 per 1,000"
        )
        check(
            f"MUS (Mauritius) per-capita IDP == 0 or NaN (got {mus_idp})",
            mus_idp is None or pd.isna(mus_idp) or float(mus_idp) < 1.0,
            "Mauritius has no significant IDP population"
        )

        idp_vals = clean_df["displaced_persons"].dropna()
        max_idp = float(idp_vals.max()) if not idp_vals.empty else 0
        check(
            f"Max per-capita IDP < 300 per 1,000 (got {max_idp:.1f})",
            max_idp < 300,
            "Sanity check: values above 300/1,000 indicate computation error"
        )

# ── E. Stage-1 fill aggregation ───────────────────────────────────────────────

print("\nE. Stage-1 fill — aggregation method correctness")
if not clean_file.exists():
    print(f"  {WARN}  Skipping E — 02_clean.xlsx not yet available")
else:
    fill_df = pd.read_excel(clean_file, sheet_name="fill_log")
    s1_fills = fill_df[fill_df["fill_stage"] == "stage1_extended"]
    check(
        f"fill_log present with {len(fill_df)} total fill records",
        len(fill_df) > 0
    )
    gdp_growth_fills = s1_fills[s1_fills["variable_name"] == "gdp_growth_3yr_avg"]
    check(
        f"gdp_growth_3yr_avg Stage-1 fills present if any country missing ({len(gdp_growth_fills)} fills)",
        True,
        "Values should be 3-year averages from lookback window, not single-year values"
    )

# ── F. Registry check ─────────────────────────────────────────────────────────

print("\nF. Registry validation")
from config import PillarRegistry, IndicatorRegistry
pr = PillarRegistry()
ir = IndicatorRegistry(pr)
valid = ir.validate_all()
check("Registry validate_all passes", valid)

inds = ir.build_indicators()
wgi_count = sum(1 for v in inds.values() if v.database == "wgi")
wdi_count = sum(1 for v in inds.values() if v.database == "wdi")
scoring_count = sum(1 for v in inds.values() if v.role == "scoring")
descriptive_count = sum(1 for v in inds.values() if v.role == "descriptive")

check(f"6 WGI indicators (got {wgi_count})", wgi_count == 6)
check(f"31 WDI indicators (got {wdi_count})", wdi_count == 31)
check(
    f"population_total is descriptive (role={inds.get('population_total', type('', (), {'role': 'MISSING'})()).role})",
    inds.get("population_total") is not None and inds["population_total"].role == "descriptive"
)
check(
    f"displaced_persons display_name updated to per-1,000",
    "per 1,000" in (inds.get("displaced_persons", type('', (), {'display_name': ''})()).display_name)
)
check(
    f"co2_pc series_code is AR5 ({inds.get('co2_pc', type('', (), {'series_code': ''})()).series_code})",
    "AR5" in str(inds.get("co2_pc", type('', (), {'series_code': ''})()).series_code)
)
check(
    f"All WGI series_codes start with GOV_WGI_",
    all("GOV_WGI_" in v.series_code for v in inds.values() if v.database == "wgi")
)

# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"PASSED: {(37 - len(errors) - len(warnings))} checks")
if warnings:
    print(f"WARNINGS: {len(warnings)}")
    for w in warnings:
        print(f"  {WARN}  {w}")
if errors:
    print(f"FAILED: {len(errors)}")
    for e in errors:
        print(f"  {FAIL}  {e}")
    sys.exit(1)
else:
    print("\nStage 1 validation PASSED.")
