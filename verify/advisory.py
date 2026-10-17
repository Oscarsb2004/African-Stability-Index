"""
verify/advisory.py — design diagnostics. Reports; never blocks.

These are judgement calls, not arithmetic. Whether Pillar A leaning heavily on
one source family is acceptable is a decision for a person; failing a build over
it would only train people to ignore the gate. Everything here therefore prints
and exits 0.

Ported to the panel in Phase C. The previous version read the legacy snapshot
files, which no longer exist.

This layer used to import `asi.dashboard.data` — the results loader the
interface uses — which broke the rule the other three layers keep: verification
that imports the code it checks inherits that code's bugs. A filter dropped in
that loader would have silently narrowed what the diagnostics saw, and the
diagnostics would have reported the narrowed picture as the whole one. It now
reads `data/panel/` with plain json and pandas, as `verify/panel.py` does.

Run:  python verify/advisory.py
"""

import json as _json
import math
import sys as _sys
from dataclasses import dataclass
from pathlib import Path as _Path

_REPO = _Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_REPO))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from scipy.stats import t as t_dist

from asi.core.constants import PILLAR_DEFS, MIN_CRONBACH_ALPHA

from verify import stats

PANEL_DIR = _REPO / "data" / "panel"

# Mo Ibrahim Foundation, IIAG 2023 — an external sanity check, not a target.
#
# Both sets are Africa-only by construction, so "4 of 5 agree" says nothing
# about whether the index would place an African state correctly against a
# non-African one. Stage 4 (B39-B42) is where the benchmark work belongs; this
# note is here so the limitation travels with the numbers it qualifies.
IIAG_TOP5    = {"MUS", "CPV", "SYC", "BWA", "ZAF"}
IIAG_BOTTOM5 = {"SSD", "SOM", "ERI", "SDN", "COD"}

NOTES: list[str] = []


def _pooled_indicator_frame(panel: "_Panel") -> pd.DataFrame:
    """
    Every country-year as a row, indicators as columns.

    Used only where a single year has too few complete cases to support a factor
    model. Rows are not independent observations and the caller must say so.
    """
    scoring_rows = panel.observations[panel.observations["role"] == "scoring"]
    return scoring_rows.pivot_table(
        index=["iso3", "year"], columns="variable_name",
        values="score", aggfunc="first",
    )


def _residuals(frame: pd.DataFrame, control: pd.Series) -> pd.DataFrame:
    """Each column with a covariate regressed out (least squares, complete rows): what is left once the covariate
    is held constant."""
    data = frame.join(control.rename("_control"), how="inner").dropna()
    x = np.column_stack([np.ones(len(data)), data.pop("_control").to_numpy()])
    fitted = x @ np.linalg.lstsq(x, data.to_numpy(dtype=float), rcond=None)[0]
    return pd.DataFrame(data.to_numpy(dtype=float) - fitted, index=data.index, columns=data.columns)


def _kmo_label(value: float) -> str:
    """Kaiser's own labels for sampling adequacy."""
    for floor, label in ((0.90, "marvellous"), (0.80, "meritorious"),
                         (0.70, "middling"), (0.60, "mediocre"),
                         (0.50, "miserable")):
        if value >= floor:
            return label
    return "unacceptable"


@dataclass(slots=True)
class _Panel:
    """
    The stored panel, read directly rather than through the results loader.

    Deliberately a plain container with no filtering: every field is exactly
    what is on disk. Anything this layer wants to exclude, it excludes visibly
    at the point of use.
    """

    meta: dict
    indicators: dict
    pillars: dict
    observations: pd.DataFrame
    pillar_scores: pd.DataFrame
    composites: pd.DataFrame

    @property
    def reference_year(self) -> int:
        return int(self.meta["run"]["reference_year"])


def _load(panel_dir: _Path | None = None) -> _Panel:
    d = _Path(panel_dir or PANEL_DIR)
    required = ["bundle.json", "observations.csv", "pillar_scores.csv",
                "composites.csv"]
    missing = [f for f in required if not (d / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Panel incomplete in {d}: missing {missing}. Run: python 02_panel.py")

    meta = _json.loads((d / "bundle.json").read_text(encoding="utf-8"))
    return _Panel(
        meta=meta,
        indicators=meta["indicators"],
        pillars=meta["pillars"],
        observations=pd.read_csv(d / "observations.csv"),
        pillar_scores=pd.read_csv(d / "pillar_scores.csv"),
        composites=pd.read_csv(d / "composites.csv"),
    )


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def note(text: str) -> None:
    NOTES.append(text)
    print(f"  {text}")


def main() -> int:
    panel = _load()
    year = panel.reference_year
    print("=" * 78)
    print(f"ADVISORY -- design diagnostics at {year} (report only)")
    print("=" * 78)

    scoring = {v: m for v, m in panel.indicators.items() if m.get("role") == "scoring"}

    # ── effective weights ─────────────────────────────────────────────────────
    section("Effective weight per indicator")
    sizes = {p: len(panel.pillars[p]["indicators"]) for p in PILLAR_DEFS}
    eff = {
        v: sum((1 / len(PILLAR_DEFS)) / sizes[p] for p in m["pillars"] if sizes.get(p))
        for v, m in scoring.items()
    }
    even = 1 / len(scoring)
    ranked = sorted(eff.items(), key=lambda kv: -kv[1])
    note(f"pillar sizes: {sizes}")
    for v, w in ranked[:4]:
        note(f"{v}: {w*100:.2f}% ({w/even:.2f}x an even share) "
             f"pillars={'+'.join(scoring[v]['pillars'])}")
    note(f"lowest: {ranked[-1][0]} at {ranked[-1][1]*100:.2f}% "
         f"({ranked[-1][1]/even:.2f}x)")
    spread = ranked[0][1] / ranked[-1][1]
    note(f"heaviest indicator carries {spread:.1f}x the lightest — equal pillar "
         f"weights are not equal indicator weights")

    # ── source concentration ──────────────────────────────────────────────────
    section("Source concentration")
    by_db: dict[str, float] = {}
    for v, m in scoring.items():
        by_db[m.get("database", "?")] = by_db.get(m.get("database", "?"), 0) + eff[v]
    for db, w in sorted(by_db.items(), key=lambda kv: -kv[1]):
        n = sum(1 for m in scoring.values() if m.get("database") == db)
        note(f"{db.upper()}: {n} indicators carrying {w*100:.1f}% of composite weight")

    # ── within-pillar redundancy ──────────────────────────────────────────────
    section("Within-pillar redundancy (|rho| > 0.80 at the reference year)")
    obs = panel.observations
    at_year = obs[(obs["year"] == year) & (obs["role"] == "scoring")]
    wide = at_year.pivot_table(index="iso3", columns="variable_name",
                               values="score", aggfunc="first")
    found = 0
    for pid, meta in panel.pillars.items():
        members = [v for v in meta["indicators"] if v in wide.columns]
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                pair = wide[[a, b]].dropna()
                if len(pair) < 10:
                    continue
                rho = spearmanr(pair[a], pair[b]).statistic
                if abs(rho) > 0.80:
                    found += 1
                    note(f"{pid}: {a} x {b} rho={rho:+.2f}")
    if not found:
        note("none")

    # ── cross-pillar redundancy ───────────────────────────────────────────────
    section("Cross-pillar redundancy (|rho| > 0.80, different pillars)")
    cols = [c for c in wide.columns if c in scoring]
    found = 0
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            if set(scoring[a]["pillars"]) & set(scoring[b]["pillars"]):
                continue
            pair = wide[[a, b]].dropna()
            if len(pair) < 10:
                continue
            rho = spearmanr(pair[a], pair[b]).statistic
            if abs(rho) > 0.80:
                found += 1
                note(f"{a} ({'+'.join(scoring[a]['pillars'])}) x "
                     f"{b} ({'+'.join(scoring[b]['pillars'])}): rho={rho:+.2f}")
    if not found:
        note("none")

    # ── internal consistency ──────────────────────────────────────────────────
    # OECD step 4. Computed on the `score` column, which normalisation has
    # already inverted for negative-polarity indicators — so the items are
    # polarity-aligned by construction. The retired pre-panel implementation ran
    # on raw mixed-polarity values, which deflates alpha mechanically and is why
    # its warnings were uninterpretable.
    section(f"Internal consistency: Cronbach's alpha (threshold {MIN_CRONBACH_ALPHA})")
    note("alpha rises with item count and with redundancy — a pillar measuring "
         "one thing six times scores well. Read it beside item-rest below.")
    for pid, meta in panel.pillars.items():
        members = [v for v in meta["indicators"] if v in wide.columns]
        result = stats.cronbach_alpha(wide[members])
        if not result.defined:
            note(f"{pid}: undefined ({result.note})")
            continue
        flag = "" if result.alpha >= MIN_CRONBACH_ALPHA else "  << below threshold"
        note(f"{pid}: alpha={result.alpha:+.3f}  k={result.k}  n={result.n}{flag}")

    all_items = [v for v in wide.columns if v in scoring]
    whole = stats.cronbach_alpha(wide[all_items])
    if whole.defined:
        note(f"all {whole.k} scoring indicators as ONE scale: alpha={whole.alpha:+.3f} "
             f"(n={whole.n}) — high here means the pillars are less distinct than "
             f"the structure claims")

    # ── item-rest correlations ────────────────────────────────────────────────
    section("Item-rest correlation (item vs the sum of its pillar's others)")
    note("negative: check polarity first. below +0.30: the item may belong elsewhere.")
    flagged = 0
    for pid, meta in panel.pillars.items():
        members = [v for v in meta["indicators"] if v in wide.columns]
        if len(members) < 2:
            continue
        for v, r in sorted(stats.item_rest_correlations(wide[members]).items(),
                           key=lambda kv: (kv[1] is not None, kv[1])):
            if r is None:
                note(f"{pid}: {v} undefined (no variance)")
                flagged += 1
            elif r < 0.30:
                note(f"{pid}: {v} r={r:+.3f}")
                flagged += 1
    if not flagged:
        note("every indicator correlates at least +0.30 with the rest of its pillar")

    # ── dimensionality ────────────────────────────────────────────────────────
    # Both levels, each labelled. Two eigenvalue figures in this repository read
    # as contradictory only because neither stated which level it described.
    section("Dimensionality (eigenvalues of the correlation matrix)")
    indicator_dim = stats.pca_dimensionality(wide[all_items], level="32 indicators")
    note(indicator_dim.summary())

    pillar_wide = (panel.pillar_scores[panel.pillar_scores["year"] == year]
                   .pivot_table(index="iso3", columns="pillar_id", values="score",
                                aggfunc="first"))
    pillar_dim = stats.pca_dimensionality(pillar_wide, level="7 pillar scores")
    note(pillar_dim.summary())
    note("the pipeline's PCA weighting acts at the pillar level; reporting only "
         "the indicator-level figure beside it would compare unlike things")

    # ── structural validation ─────────────────────────────────────────────────
    # Does the declared grouping match the structure the data shows? Written
    # against a {group: members} mapping rather than against pillars, so the same
    # check evaluates any later index framework.
    section("Structural validation (declared pillars vs recovered factors)")
    declared = {pid: list(meta["indicators"]) for pid, meta in panel.pillars.items()}

    for label, frame in (
        (f"reference year {year}", wide),
        # Pooling every country-year is the only way to reach a non-singular
        # correlation matrix here. The rows are not independent — the same 54
        # countries recur for 25 years and indicator series are highly
        # autocorrelated — so the effective sample is far below the nominal one.
        # Reported because it is the closest thing to an answer available, and
        # labelled because it must not be read as 147 independent observations.
        ("pooled country-years", _pooled_indicator_frame(panel)),
    ):
        structure = stats.structure_agreement(frame, declared)
        note(f"[{label}]")
        if structure.note:
            note(f"   not computed: {structure.note}")
            continue

        note(f"   {structure.n} complete observations x {structure.k} indicators "
             f"= {structure.obs_per_variable:.2f} per variable "
             f"(correlation matrix rank {structure.rank} of {structure.k})")

        if not structure.reportable:
            note(f"   NOT REPORTABLE: {structure.inadequacy}")
            note(f"   a factor routine still returns a solution on this data, and "
                 f"that solution would carry an adjusted Rand index of "
                 f"{structure.agreement:+.3f}. It is not evidence about the pillar "
                 f"structure and must not be quoted as though it were.")
            continue

        if structure.kmo is not None:
            note(f"   KMO sampling adequacy: {structure.kmo:.3f} "
                 f"({_kmo_label(structure.kmo)})")
        chi2, df = stats.bartlett_sphericity(frame[[c for c in frame.columns
                                                    if c in scoring]])
        if chi2 is not None:
            note(f"   Bartlett sphericity: chi2={chi2:.0f} on {df} df "
                 f"(a floor, not evidence of a good solution)")
        note(f"   adjusted Rand index vs the declared pillars: "
             f"{structure.agreement:+.3f} (1.0 identical, 0.0 chance)")
        for pid, share in sorted(structure.cohesion.items()):
            note(f"      {pid}: {share*100:.0f}% of members land on one factor")
        if structure.cross_listed:
            note(f"   cross-listed, assigned to their first pillar: "
                 f"{list(structure.cross_listed)}")

    note("a formative index need not recover cleanly — pillars that jointly "
         "define stability are not required to be alternative measures of it. "
         "Whether this index is formative or reflective has never been stated, "
         "and that decision governs how these numbers should be read.")

    # ── correlations, each with its sample ────────────────────────────────────
    # Real values only: an imputed cell is the pipeline's guess, and correlating
    # guesses measures the imputation. `score` is already polarity-aligned, so a
    # positive r means both indicators point to more stability.
    section("Correlations between indicators, each with its sample (n, 95% CI, p)")
    real = at_year[at_year["provenance"].isin(["observed", "carried_forward"])]
    real_wide = real.pivot_table(index="iso3", columns="variable_name", values="score", aggfunc="first")
    gdp = real[real["variable_name"] == "gdp_pc_ppp"].set_index("iso3")["raw_value"]
    log_gdp = gdp[gdp > 0].map(math.log)
    names = [c for c in real_wide.columns if c in scoring]
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pair = real_wide[[a, b]].dropna()
            n = len(pair)
            if n < 5:
                continue
            r = float(pair[a].corr(pair[b]))
            _, p = stats.r_significance(r, n)
            low, high = stats.r_interval(r, n)
            row = {"a": a, "b": b, "n": n, "r": r, "p": p, "low": low, "high": high}
            triple = pair.join(log_gdp.rename("gdp"), how="inner")
            if "gdp_pc_ppp" not in (a, b) and len(triple) >= 6:
                c = triple.corr()
                row["partial"] = stats.partial_r(c.loc[a, b], c.loc[a, "gdp"], c.loc[b, "gdp"])
                row["n_partial"] = len(triple)
                row["p_partial"] = stats.r_significance(row["partial"], len(triple) - 1)[1]
            rows.append(row)
    pairs = pd.DataFrame(rows)
    note(f"{len(pairs)} pairs with at least 5 countries reporting both; n from {pairs.n.min()} to "
         f"{pairs.n.max()}, median {pairs.n.median():.0f}")
    note(f"significant at .05: {(pairs.p < 0.05).sum()}; |r| >= .50: {(pairs.r.abs() >= 0.5).sum()}; "
         f"median 95% CI width {(pairs.high - pairs.low).median():.2f}")
    note(f"|r| >= .40 yet not significant, because n < 25: "
         f"{((pairs.r.abs() >= 0.4) & (pairs.p >= 0.05) & (pairs.n < 25)).sum()}")
    thin = real_wide[names].notna().sum().sort_values()
    note("fewest countries reporting: " + ", ".join(f"{v} {n}" for v, n in thin.head(6).items()))

    # ── the third variable ────────────────────────────────────────────────────
    # Development lifts most indicators together. Partialling it out separates a
    # relationship between two indicators from their shared dependence on it.
    section("The third variable: log GDP per capita held constant (partial r)")
    with_gdp = pairs[(pairs.a == "gdp_pc_ppp") | (pairs.b == "gdp_pc_ppp")].copy()
    with_gdp["other"] = with_gdp.a.where(with_gdp.a != "gdp_pc_ppp", with_gdp.b)
    strongest = with_gdp.reindex(with_gdp.r.abs().sort_values(ascending=False).index).head(6)
    note("most dependent on GDP per capita: " + "; ".join(
        f"{x.other} {x.r:+.2f} (n={x.n})" for x in strongest.itertuples()))
    partials = pairs.dropna(subset=["partial"]) if "partial" in pairs else pd.DataFrame()
    strong = partials[(partials.r.abs() >= 0.5) & (partials.p < 0.05)]
    note(f"{len(strong)} strong pairs (|r| >= .50, p < .05); with GDP held constant "
         f"{(strong.p_partial >= 0.05).sum()} lose significance and {(strong.partial.abs() < 0.3).sum()} fall "
         f"below |.30|")
    drops = strong.assign(drop=strong.r.abs() - strong.partial.abs()).sort_values("drop", ascending=False)
    for x in drops.head(4).itertuples():
        note(f"   {x.a} x {x.b}: r {x.r:+.2f} -> {x.partial:+.2f} (n={int(x.n_partial)})")
    note(f"suppression (partial larger than r by more than .15): "
         f"{(partials.partial.abs() > partials.r.abs() + 0.15).sum()} pairs; correlation is not causation "
         f"in an observational design, and an Africa-only sample restricts the range")

    # ── pillars: reliability-corrected correlations and factors ───────────────
    section("Pillars: correlations corrected for attenuation, and factor analysis")
    alphas = {pid: stats.cronbach_alpha(wide[[v for v in meta["indicators"] if v in wide.columns]]).alpha
              for pid, meta in panel.pillars.items()}
    pillar_r = pillar_wide.corr()
    n_pillar = len(pillar_wide.dropna())
    merged = []
    for i, a in enumerate(pillar_r.index):
        for b in pillar_r.columns[i + 1:]:
            if alphas.get(a) and alphas.get(b) and alphas[a] > 0 and alphas[b] > 0:
                corrected = stats.disattenuated_r(pillar_r.loc[a, b], alphas[a], alphas[b])
                if abs(corrected) >= 0.90:
                    merged.append(f"{a}-{b} {pillar_r.loc[a, b]:+.2f} -> {corrected:+.2f}")
    note(f"n = {n_pillar}; pairs whose corrected r reaches |.90| (not distinguishable at their reliability): "
         + (", ".join(merged) if merged else "none"))
    note("alpha is a lower bound on reliability, so a corrected r is an upper bound; above 1 means the two "
         "pillars are one measurement within error")
    k_overall, _ = stats.kmo(pillar_wide)
    chi2, df = stats.bartlett_sphericity(pillar_wide)
    if k_overall is not None and chi2 is not None:
        note(f"KMO {k_overall:.3f} ({_kmo_label(k_overall)}); Bartlett chi2 {chi2:.1f} on {df} df; "
             f"{n_pillar / pillar_wide.shape[1]:.1f} countries per pillar")
    for label, frame in (("as scored", pillar_wide.dropna()),
                         ("log GDP per capita held constant", _residuals(pillar_wide, log_gdp))):
        eigen = np.linalg.eigvalsh(frame.corr().to_numpy())[::-1]
        chance = stats.parallel_analysis(len(frame), frame.shape[1])
        keep = int(np.argmin(eigen > chance)) if (eigen <= chance).any() else len(eigen)
        note(f"[{label}, n = {len(frame)}] eigenvalues {', '.join(f'{e:.2f}' for e in eigen[:3])}; parallel "
             f"analysis {', '.join(f'{c:.2f}' for c in chance[:3])}; factors to keep: {keep}")
    loadings = stats.factor_loadings(pillar_wide.dropna(), 2)
    note("two-factor loadings (ML, varimax): " + "; ".join(
        f"{pid} {row.F1:+.2f}/{row.F2:+.2f}" for pid, row in loadings.iterrows()))

    # ── composite intervals and rank bands ────────────────────────────────────
    # Each country's composite is the mean of a sample of k pillar scores, so it
    # has a standard error, SD / sqrt(k), and a t interval on k - 1 degrees of
    # freedom. Two countries differ only if the z test on their difference passes.
    section("Composite confidence intervals and rank bands (equal weights)")
    k = pillar_wide.notna().sum(axis=1)
    mean = pillar_wide.mean(axis=1)
    se = pillar_wide.std(axis=1, ddof=1) / k.pow(0.5)
    half = se * k.map(lambda size: float(t_dist.ppf(0.975, size - 1)) if size > 1 else float("nan"))
    bands = stats.rank_bands(mean, se)
    note(f"standard error of each composite: median {se.median():.2f} points ({se.min():.2f} to {se.max():.2f}); "
         f"95% half-width median {half.median():.2f}")
    note(f"rank bands: median {bands.width.median():.0f} places wide ({bands.width.min()} to {bands.width.max()}) "
         f"of {len(bands)} — the data separate a handful of tiers, not {len(bands)} ranks")
    for iso3, row in bands.sort_values("score", ascending=False).head(3).iterrows():
        note(f"   {iso3}: {row.score:.1f} +/- {half[iso3]:.1f}, ranks {int(row.best)}-{int(row.worst)}")

    # ── data quality ──────────────────────────────────────────────────────────
    section("Data quality at the reference year")
    prov = at_year["provenance"].value_counts()
    total = int(prov.sum())
    for kind, n in prov.items():
        note(f"{kind}: {n} cells ({n/total*100:.1f}%)")
    weakest = (
        at_year.assign(real=at_year["provenance"].eq("observed"))
        .groupby("variable_name")["real"].mean().sort_values().head(5)
    )
    note("least directly measured indicators:")
    for v, share in weakest.items():
        note(f"   {v}: {share*100:.0f}% measured")

    pil = panel.pillar_scores
    tiers = pil[pil["year"] == year]["reliability"].value_counts()
    note(f"pillar tiers: {dict(tiers)}")

    # ── external plausibility ─────────────────────────────────────────────────
    section("External plausibility (IIAG 2023)")
    comp = panel.composites
    eq = comp[(comp["year"] == year) & (comp["method"] == "equal")
              & comp["rank"].notna()].sort_values("rank")
    top10 = set(eq.head(10)["iso3"])
    bottom10 = set(eq.tail(10)["iso3"])
    note(f"IIAG top-5 appearing in our top-10:    {len(IIAG_TOP5 & top10)}/5 "
         f"{sorted(IIAG_TOP5 & top10)}")
    note(f"IIAG bottom-5 appearing in our bottom-10: {len(IIAG_BOTTOM5 & bottom10)}/5 "
         f"{sorted(IIAG_BOTTOM5 & bottom10)}")
    missing = IIAG_BOTTOM5 - set(eq["iso3"])
    if missing:
        note(f"not rankable this year (insufficient data): {sorted(missing)}")

    print()
    print("-" * 78)
    print(f"advisory: {len(NOTES)} observations. Judgement, not arithmetic — "
          f"this layer never blocks a release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
