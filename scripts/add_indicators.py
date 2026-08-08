import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
logging.basicConfig(level=logging.INFO)

from asi.core.registry import PillarRegistry, IndicatorRegistry

pr = PillarRegistry()
ir = IndicatorRegistry(pr)


def add_if_missing(ir, **kwargs):
    """Skips silently if the indicator already exists. Safe to re-run."""
    try:
        ir.add_indicator(**kwargs)
        logging.info("Added: %s", kwargs["variable_name"])
    except ValueError as e:
        if "already exists" in str(e):
            pass
        else:
            raise


# =============================================================================
# PILLAR A — Political / Governance
# WGI estimated scores are defined here with their full cross-pillar lists.
# They are NOT re-defined in B, C, E, or G.
#
# SERIES CODE NOTE: WGI codes in wbgapi require source=3 (the WGI database).
# The short-form codes below (VA.EST, PV.EST etc.) are correct for that source.
# Verify against: wbgapi.series.list(db=3) before building 01_pull.py.
# =============================================================================

add_if_missing(ir,
    variable_name = "va_estimate",
    display_name  = "Voice and Accountability, WGI estimated score",
    source        = "wb_api",
    series_code   = "GOV_WGI_VA.EST",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["A", "C"],
    year_start    = 2015,
    year_end      = 2023,
    aggregation   = "most_recent",
    database      = "wgi",
    log_transform = False,
    justification = "Measures the degree to which citizens can participate in government and exercise freedom of expression and association. Used in Pillar C as a proxy for civic openness and social freedom.",
)

add_if_missing(ir,
    variable_name = "pv_estimate",
    display_name  = "Political Stability and Absence of Violence / Terrorism, WGI estimated score",
    source        = "wb_api",
    series_code   = "GOV_WGI_PV.EST",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["A", "E"],
    year_start    = 2015,
    year_end      = 2023,
    aggregation   = "most_recent",
    database      = "wgi",
    log_transform = False,
    justification = "Measures the likelihood of political instability and politically motivated violence including terrorism. Cross-listed in Pillar E as a governance-side signal of security fragility.",
)

add_if_missing(ir,
    variable_name = "ge_estimate",
    display_name  = "Government Effectiveness, WGI estimated score",
    source        = "wb_api",
    series_code   = "GOV_WGI_GE.EST",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["A", "G"],
    year_start    = 2015,
    year_end      = 2023,
    aggregation   = "most_recent",
    database      = "wgi",
    log_transform = False,
    justification = "Captures quality of public services and the credibility of government commitment to policies. Cross-listed in Pillar G because effective government is the prerequisite for infrastructure delivery.",
)

add_if_missing(ir,
    variable_name = "rq_estimate",
    display_name  = "Regulatory Quality, WGI estimated score",
    source        = "wb_api",
    series_code   = "GOV_WGI_RQ.EST",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["A", "B", "G"],
    year_start    = 2015,
    year_end      = 2023,
    aggregation   = "most_recent",
    database      = "wgi",
    log_transform = False,
    justification = "Measures the government's ability to formulate sound policies that permit private sector development. Cross-listed in Pillar B for its economic dimension and Pillar G for its role in enabling infrastructure markets.",
)

add_if_missing(ir,
    variable_name = "rl_estimate",
    display_name  = "Rule of Law, WGI estimated score",
    source        = "wb_api",
    series_code   = "GOV_WGI_RL.EST",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["A", "E"],
    year_start    = 2015,
    year_end      = 2023,
    aggregation   = "most_recent",
    database      = "wgi",
    log_transform = False,
    justification = "Captures confidence in societal rules including property rights, contract enforcement, and courts. Cross-listed in Pillar E as a systemic driver of security — weak rule of law enables violent actors.",
)

add_if_missing(ir,
    variable_name = "cc_estimate",
    display_name  = "Control of Corruption, WGI estimated score",
    source        = "wb_api",
    series_code   = "GOV_WGI_CC.EST",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["A", "G"],
    year_start    = 2015,
    year_end      = 2023,
    aggregation   = "most_recent",
    database      = "wgi",
    log_transform = False,
    justification = "Measures the extent to which public power is exercised for private gain. Cross-listed in Pillar G because corruption directly degrades infrastructure delivery and public service quality.",
)


# =============================================================================
# PILLAR B — Economic
# rq_estimate already defined above (pillars: ["A", "B", "G"])
# =============================================================================

add_if_missing(ir,
    variable_name = "gdp_pc_ppp",
    display_name  = "GDP per capita, PPP (current international $)",
    source        = "wb_api",
    series_code   = "NY.GDP.PCAP.PP.CD",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["B"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = True,
    justification = "PPP-adjusted GDP per capita is the primary measure of material living standards, controlling for price differences across countries. The most direct single indicator of economic resilience.",
)

add_if_missing(ir,
    variable_name = "gdp_growth_3yr_avg",
    display_name  = "GDP growth, annual % (3-year average)",
    source        = "wb_api",
    series_code   = "NY.GDP.MKTP.KD.ZG",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["B"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "average_recent_3",
    database      = "wdi",
    log_transform = False,
    justification = "A 3-year average smooths single-year volatility and reflects the recent growth trajectory. Sustained growth signals economic momentum; contraction or stagnation signals structural fragility.",
)

add_if_missing(ir,
    variable_name = "inflation_5yr_avg",
    display_name  = "Inflation, consumer prices, annual % (5-year average)",
    source        = "wb_api",
    series_code   = "FP.CPI.TOTL.ZG",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["B"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "average_recent_5",
    database      = "wdi",
    log_transform = False,
    justification = "Chronic high inflation erodes real wages, destroys savings, and destabilises governments. A 5-year average captures structural monetary instability rather than isolated supply shocks.",
)

add_if_missing(ir,
    variable_name = "gini",
    display_name  = "Gini index",
    source        = "wb_api",
    series_code   = "SI.POV.GINI",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["B"],
    year_start    = 2010,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Income inequality is a structural driver of social tension and political instability that GDP alone conceals. Year range extended to 2010 because Gini is survey-based and reported infrequently.",
)

add_if_missing(ir,
    variable_name = "firm_foreign_owned",
    display_name  = "Firms with at least 10% foreign ownership (% of firms)",
    source        = "wb_api",
    series_code   = "IC.FRM.FO.ZS",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["B"],
    year_start    = 2010,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Foreign ownership signals that the investment climate is sufficiently stable and open to attract external capital. Extended year range used because this is drawn from enterprise surveys conducted every few years.",
)


# =============================================================================
# PILLAR C — Social / Human Capital
# va_estimate already defined above (pillars: ["A", "C"])
# =============================================================================

add_if_missing(ir,
    variable_name = "youth_literacy",
    display_name  = "Literacy rate, youth total (% of people ages 15-24)",
    source        = "wb_api",
    series_code   = "SE.ADT.1524.LT.ZS",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["C"],
    year_start    = 2010,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Youth literacy reflects the effectiveness of basic education for the generation currently entering adulthood. Extended year range used because literacy data is survey-based and reported infrequently.",
)

add_if_missing(ir,
    variable_name = "adult_literacy",
    display_name  = "Literacy rate, adult total (% of people ages 15 and above)",
    source        = "wb_api",
    series_code   = "SE.ADT.LITR.ZS",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["C"],
    year_start    = 2010,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Adult literacy captures the cumulative education stock of the working-age population. Low adult literacy constrains economic participation, civic engagement, and institutional trust.",
)

add_if_missing(ir,
    variable_name = "primary_enroll",
    display_name  = "School enrollment, primary, net (%)",
    source        = "wb_api",
    series_code   = "SE.PRM.NENR",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["C"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Net primary enrollment is the most direct measure of whether children access foundational education. Gaps here compound into long-term human capital deficits and higher youth unemployment.",
)

add_if_missing(ir,
    variable_name = "secondary_enroll",
    display_name  = "School enrollment, secondary, net (%)",
    source        = "wb_api",
    series_code   = "SE.SEC.NENR",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["C"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Secondary enrollment captures progression beyond basic schooling, shaping the skilled labour pool and reducing youth vulnerability to recruitment by armed groups.",
)

add_if_missing(ir,
    variable_name = "primary_oos",
    display_name  = "Children out of school, primary (% of primary school age)",
    source        = "wb_api",
    series_code   = "SE.PRM.UNER.ZS",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["C"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Out-of-school children represent the population excluded from foundational education. High rates correlate with child labour, poverty cycles, and long-run instability.",
)

add_if_missing(ir,
    variable_name = "learning_poverty",
    display_name  = "Learning poverty: share of children below minimum reading proficiency, adjusted for out-of-school (%)",
    source        = "wb_api",
    series_code   = "SE.LPV.PRIM",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["C"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Learning poverty combines enrollment gaps and quality gaps, measuring not just who attends school but whether attendance translates into functional literacy.",
)
# VERIFY: series code SE.LPV.PRIM needs confirmation against wbgapi. Original
# source was World Bank Data360 (WB_WDI_SE_LPV_PRIM). If not pullable via
# standard WDI, this will need manual import before 01_pull.py.

add_if_missing(ir,
    variable_name = "primary_gpi",
    display_name  = "School enrollment, primary, gender parity index (GPI)",
    source        = "wb_api",
    series_code   = "SE.ENR.PRIM.FM.ZS",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["C"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "GPI equals girls enrolled divided by boys enrolled. Values near 1.0 indicate parity; values below 1.0 signal systematic exclusion of girls from primary education.",
)

add_if_missing(ir,
    variable_name = "secondary_gpi",
    display_name  = "School enrollment, secondary, gender parity index (GPI)",
    source        = "wb_api",
    series_code   = "SE.ENR.SECO.FM.ZS",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["C"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Secondary GPI captures whether girls progress beyond primary schooling at the same rate as boys. Persistent gaps signal structural gender inequality with compounding social consequences.",
)

add_if_missing(ir,
    variable_name = "femicide",
    display_name  = "Intentional homicides, female (per 100,000 female population)",
    source        = "wb_api",
    series_code   = "VC.IHR.PSRC.FE.P5",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["C"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Female homicide rates measure gendered violence and social cohesion failure. High rates indicate systemic failure to protect women and deep structural inequality beyond what aggregate homicide rates reveal.",
)


# =============================================================================
# PILLAR D — Health
# =============================================================================

add_if_missing(ir,
    variable_name = "life_expect_tot",
    display_name  = "Life expectancy at birth, total (years)",
    source        = "wb_api",
    series_code   = "SP.DYN.LE00.IN",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["D"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Life expectancy is the single most comprehensive summary of population health, integrating disease burden, healthcare access, nutrition, and conflict mortality into one number.",
)

add_if_missing(ir,
    variable_name = "mort_infant",
    display_name  = "Mortality rate, infant (per 1,000 live births)",
    source        = "wb_api",
    series_code   = "SP.DYN.IMRT.IN",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["D"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = True,
    justification = "Infant mortality is highly sensitive to healthcare access, maternal health, nutrition, and sanitation quality. It reflects health system performance at the point of greatest biological vulnerability.",
)

add_if_missing(ir,
    variable_name = "managed_water_percent",
    display_name  = "People using safely managed drinking water services (% of population)",
    source        = "wb_api",
    series_code   = "SH.H2O.SMDW.ZS",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["D"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Safely managed water requires on-premises access, availability when needed, and freedom from contamination — a stronger standard than basic access that more accurately captures disease prevention capacity.",
)

add_if_missing(ir,
    variable_name = "hand_washing_facil",
    display_name  = "People with basic handwashing facilities including soap and water (% of population)",
    source        = "wb_api",
    series_code   = "SH.STA.HYGN.ZS",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["D"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Basic handwashing is a frontline communicable disease barrier. Low coverage accelerates transmission of cholera, typhoid, and respiratory infections and reflects underlying sanitation infrastructure gaps.",
)

add_if_missing(ir,
    variable_name = "modsev_food_insec",
    display_name  = "Prevalence of moderate or severe food insecurity (% of population)",
    source        = "wb_api",
    series_code   = "SN.ITK.MSFI.ZS",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["D"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = True,
    justification = "Moderate-to-severe food insecurity captures the share of the population with uncertain or inadequate food access, integrating agricultural output, income, distribution failures, and conflict disruption.",
)

add_if_missing(ir,
    variable_name = "sev_food_insec",
    display_name  = "Prevalence of severe food insecurity (% of population)",
    source        = "wb_api",
    series_code   = "SN.ITK.SVFI.ZS",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["D"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = True,
    justification = "Severe food insecurity — going entire days without eating — is a direct measure of acute deprivation and a documented precursor to displacement, social breakdown, and political violence.",
)


# =============================================================================
# PILLAR E — Security / Conflict
# pv_estimate and rl_estimate already defined above (pillars: ["A", "E"])
# =============================================================================

add_if_missing(ir,
    variable_name = "intent_homicide",
    display_name  = "Intentional homicides (per 100,000 people)",
    source        = "wb_api",
    series_code   = "VC.IHR.PSRC.P5",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["E"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = True,
    justification = "Homicide rates are the most consistently measured proxy for violent crime and societal security. High rates signal rule of law breakdown, gang or militia activity, and personal safety failure.",
)

add_if_missing(ir,
    variable_name = "displaced_persons",
    display_name  = "Internally displaced persons, total (number)",
    source        = "wb_api",
    series_code   = "SM.POP.IDPC",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["E"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = True,
    justification = "Internal displacement is a direct consequence of active conflict, persecution, or disaster. High IDP counts signal ongoing destabilisation and compound strain on receiving communities.",
)


# =============================================================================
# PILLAR F — Environmental
# =============================================================================

add_if_missing(ir,
    variable_name = "co2_pc",
    display_name  = "CO2 emissions (metric tons per capita)",
    source        = "wb_api",
    series_code   = "EN.GHG.CO2.PC.CE.AR5",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["F"],
    year_start    = 2015,
    year_end      = 2023,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Per capita CO2 emissions capture fossil-fuel dependence and contribution to long-run climate stress. Year end set to 2023 because emissions data is typically released with a one-to-two year lag.",
)

add_if_missing(ir,
    variable_name = "freshwater_withdraw",
    display_name  = "Annual freshwater withdrawals, total (% of internal resources)",
    source        = "wb_api",
    series_code   = "ER.H2O.FWTL.ZS",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["F"],
    year_start    = 2010,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Withdrawal rates above renewable capacity signal water stress and long-term resource depletion. Year range extended to 2010 because this indicator is reported very infrequently, sometimes only once per decade.",
)

add_if_missing(ir,
    variable_name = "nonrenew_elec",
    display_name  = "Electricity production from oil, gas, and coal sources (% of total)",
    source        = "wb_api",
    series_code   = "EG.ELC.FOSL.ZS",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["F"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "High fossil fuel dependence for electricity exposes economies to supply disruptions and price shocks, and signals slow progress on the energy transition needed to reduce long-run climate exposure.",
)

add_if_missing(ir,
    variable_name = "agri_land",
    display_name  = "Agricultural land (% of land area)",
    source        = "wb_api",
    series_code   = "AG.LND.AGRI.ZS",
    role          = "scoring",
    polarity      = "negative",
    pillars       = ["F"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "In the environmental pillar, high agricultural land share is treated as a proxy for land conversion pressure, deforestation, and ecosystem loss. REVIEW: change polarity to positive if intent is to measure food production capacity instead.",
)


# =============================================================================
# PILLAR G — Structural / Infrastructure
# ge_estimate, rq_estimate, cc_estimate already defined above (pillars include "G")
# =============================================================================

add_if_missing(ir,
    variable_name = "elec_access_tot",
    display_name  = "Access to electricity (% of population)",
    source        = "wb_api",
    series_code   = "EG.ELC.ACCS.ZS",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["G"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Electricity access is the most fundamental infrastructure indicator. It enables healthcare delivery, education, communications, and economic activity. Low access is a binding constraint on all other development.",
)

add_if_missing(ir,
    variable_name = "water_access_pop",
    display_name  = "People using at least basic drinking water services (% of population)",
    source        = "wb_api",
    series_code   = "SH.H2O.BASW.ZS",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["G"],
    year_start    = 2015,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Basic water access measures the infrastructure delivery side of water availability. Differs from Pillar D's managed water entry, which measures the health-outcome side of the same system.",
)

add_if_missing(ir,
    variable_name = "social_safetynet_pop",
    display_name  = "Coverage of social safety net programs (% of population)",
    source        = "wb_api",
    series_code   = "per_sa_allsa.cov_pop_tot",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["G"],
    year_start    = 2010,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Safety net coverage indicates state capacity to protect vulnerable populations from shocks. Low coverage leaves citizens without institutional buffers, amplifying the destabilising effect of economic downturns.",
)

add_if_missing(ir,
    variable_name = "social_protection_labour_pop",
    display_name  = "Coverage of social protection and labor programs (% of population)",
    source        = "wb_api",
    series_code   = "per_allsp.cov_pop_tot",
    role          = "scoring",
    polarity      = "positive",
    pillars       = ["G"],
    year_start    = 2010,
    year_end      = 2024,
    aggregation   = "most_recent",
    database      = "wdi",
    log_transform = False,
    justification = "Broader than safety nets alone, this captures all formal social protection and labour program coverage, reflecting the overall institutional reach of the state in protecting its citizens.",
)


print("\nAll indicators processed.")
print(f"Total indicators in registry: {len(ir.list_indicators())}")
print("\nBreakdown by pillar (scoring only):")
for key in ["A", "B", "C", "D", "E", "F", "G"]:
    count = len(ir.list_indicators(pillar=key, role="scoring"))
    print(f"  Pillar {key}: {count} scoring indicators")
