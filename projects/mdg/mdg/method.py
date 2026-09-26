"""The method card for MDG indicator 3.3, and the indicator itself.

Every quote below is copied from a stored snapshot. `verify_quotes` checks that each is found verbatim, so the card
cannot drift from its sources.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from athena.citations import Citation
from athena.indicators import Indicator
from athena.method import MethodCard, MethodStep, PublishedValue, Reading
from athena.rounding import Rounding
from athena.vocab import Origin, ReproClass

META = "source:un-mdg-archive-documents"
IPU = "source:ipu-women-in-parliament-archive"
REPORT = "source:un-mdg-report-2015"
META_557 = "MDG metadata, series 557"
GROUPINGS_DOC = "Regional groupings.doc"
IPU_PAGE = "IPU world classification, 1 February 2015"
IPU_WORLD = "IPU world and regional averages, 1 February 2015"
ANNEX = "MDG 2015 statistical annex, page 18"

CARD = MethodCard(
    id="method:mdg-3-3", title="MDG 3.3 - Proportion of seats held by women in national parliament",
    subject="indicator:mdg-3-3", origin=Origin.PUBLISHED,
    steps=(
        MethodStep(number=1, name="Count seats and women", shell="shell:mdg-ratio-by-country",
                   action="For each country, take the seats filled and the seats held by women in the single or "
                          "lower chamber.",
                   citation=Citation(document=META, locator=f"{META_557}, Definition",
                                     quote="This indicator covers the single chamber in unicameral parliaments and "
                                           "the lower chamber in bicameral parliaments.")),
        MethodStep(number=2, name="Group countries", shell="shell:mdg-code-members",
                   action="Place each country in its MDG regional groupings.",
                   citation=Citation(document=META, locator=f"{GROUPINGS_DOC}, section 2",
                                     quote="MDG regional groupings: List of countries in each grouping")),
        MethodStep(number=3, name="Divide totals per group", shell="shell:mdg-sum-ratio-by-group",
                   action="Sum women and seats over each group's members, then divide.",
                   citation=Citation(document=META, locator=f"{META_557}, Regional and Global estimates",
                                     quote="Regional averages are determined by dividing the total number of women "
                                           "members by the total number of seats filled in single or lower "
                                           "chambers of parliament per region.")),
        MethodStep(number=4, name="Leave missing values out", shell="shell:mdg-sum-ratio-by-group",
                   action="A country without both counts is left out of its group's totals; nothing is imputed.",
                   citation=Citation(document=META, locator=f"{META_557}, Treatment of missing values",
                                     quote="No adjustments are made for missing values.")),
    ),
    published_values=(
        PublishedValue(name="country percentages", after_step=1,
                       description="The IPU prints each country's percentage of women, to one decimal.",
                       citation=Citation(document=IPU, locator=IPU_PAGE, quote="% W")),
        PublishedValue(name="world totals", after_step=3,
                       description="The IPU prints world totals of seats, seats with gender known, and women.",
                       citation=Citation(document=IPU, locator=IPU_WORLD, quote="Gender breakdown known for")),
        PublishedValue(name="regional table", after_step=3,
                       description="The annex prints the share for each MDG grouping, to one decimal.",
                       citation=Citation(document=REPORT, locator=ANNEX,
                                         quote="Proportion of seats held by women in national")),
    ),
    readings=(
        Reading(step=2, sentence=Citation(document=META, locator=f"{GROUPINGS_DOC}, section 3",
                                          quote="Other groupings: Least Developed Countries as of 1 January 2011"),
                options=("The list as the official groupings document gives it (as of 1 January 2011)",
                         "The list of least developed countries in force in January 2015"),
                adopted="The list of least developed countries in force in January 2015",
                reason="Owner ruling of 2026-09-26: use the lists in force in 2015. The list is the UN DESA list "
                       "captured on 2014-01-13; it already reflects Samoa's graduation on 1 January 2014, and its "
                       "footnote places the next graduations after 2015.",
                owner_ruled=True),
        Reading(step=2, sentence=Citation(document=META, locator=f"{GROUPINGS_DOC}, section 4",
                                          quote="Other groupings: Landlocked developing countries"),
                options=("The list as the official groupings document gives it (undated)",
                         "The list of landlocked developing countries in force in January 2015"),
                adopted="The list of landlocked developing countries in force in January 2015",
                reason="Owner ruling of 2026-09-26, the same rule as for least developed countries. The list is the "
                       "UN-OHRLLS country-profiles page captured on 2014-12-31.",
                owner_ruled=True),
    ),
    rounding=Rounding(decimals=1),
)

INDICATOR = Indicator(
    id="indicator:mdg-3-3", title="Proportion of seats held by women in national parliament",
    framework="MDG", code="3.3", unit="percent", method=CARD.id,
    sources=(IPU, META, REPORT), repro_class=ReproClass.A,
)


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def verify_quotes(card: MethodCard, texts: Mapping[str, str]) -> list[str]:
    """Every citation's quote must appear verbatim in the text of the document at its locator.

    `texts` maps a locator's document name (the part before the first comma) to that document's text.
    """
    citations = [s.citation for s in card.steps if s.citation]
    citations += [v.citation for v in card.published_values] + [r.sentence for r in card.readings]
    problems = []
    for c in citations:
        document = c.locator.split(",")[0]
        if document not in texts:
            problems.append(f"{c.locator}: no stored text for {document!r}")
        elif normalise(c.quote) not in normalise(texts[document]):
            problems.append(f"{c.locator}: quote not found verbatim - {c.quote[:60]!r}")
    return problems


# ── Goal 3: indicators 3.1 and 3.2 (section S43) ───────────────────────────────────────────────────────────

META_611 = "MDG metadata series 611"
META_722 = "MDG metadata series 722"
SERIES_611 = "MDG database series 611"
SERIES_722 = "MDG database series 722"
ANNEX_31 = "MDG 2015 statistical annex, pages 16 and 17"
ANNEX_32 = "MDG 2015 statistical annex, page 18"

CARD_31 = MethodCard(
    id="method:mdg-3-1", title="MDG 3.1 - Ratios of girls to boys in primary, secondary and tertiary education",
    subject="indicator:mdg-3-1", origin=Origin.PUBLISHED,
    steps=(
        MethodStep(number=1, name="Gross enrolment ratios by sex", shell="shell:mdg-ger-by-country",
                   action="For each country, sex and level, divide enrolment by the school-age population.",
                   citation=Citation(document=META, locator=f"{META_611}, Method of computation",
                                     quote="is divided by the population of official school age for that level of "
                                           "education")),
        MethodStep(number=2, name="Ratio of girls to boys", shell="shell:mdg-parity-by-country",
                   action="Divide the female gross enrolment ratio by the male one.",
                   citation=Citation(document=META, locator=f"{META_611}, Definition",
                                     quote="the Gender Parity Index (GPI) of the Gross Enrolment Ratio (GER) for each "
                                           "level of education is used")),
        MethodStep(number=3, name="Weight by school-age population per group", shell="shell:mdg-parity-by-group",
                   action="Average over each group's countries, weighted by school-age population.",
                   citation=Citation(document=META, locator=f"{META_611}, Regional and Global estimates",
                                     quote="Averages are produced using the appropriate school-age populations as "
                                           "weights.")),
        MethodStep(number=4, name="Fill gaps with unpublished estimates", shell=None,
                   action="The publisher fills missing countries with estimates it does not release. We cannot, so "
                          "a group is built only from countries with published counts.",
                   citation=Citation(document=META, locator=f"{META_611}, Regional and Global estimates",
                                     quote="using the best possible non-publishable estimates where no publishable "
                                           "data exist")),
    ),
    published_values=(
        PublishedValue(name="UIS gross enrolment ratios by sex", after_step=1,
                       description="UIS publishes each country's gross enrolment ratio by sex (current edition).",
                       citation=Citation(document=META, locator=f"{META_611}, Method of computation",
                                         quote="is divided by the population of official school age")),
        PublishedValue(name="country ratios, 2015 edition", after_step=2,
                       description="The MDG database's final country values, last updated 6 July 2015.",
                       citation=Citation(document=META, locator=f"{SERIES_611}, table",
                                         quote="Last updated: 06 Jul 2015")),
        PublishedValue(name="regional table", after_step=3,
                       description="The annex prints each grouping's ratio for 1991, 2000 and 2015, to two decimals.",
                       citation=Citation(document=REPORT, locator=ANNEX_31,
                                         quote="Ratios of girls to boys in primary, secondary")),
    ),
    readings=(
        Reading(step=3, sentence=Citation(document=META, locator=f"{META_611}, Regional and Global estimates",
                                          quote="Averages are produced using the appropriate school-age populations "
                                                "as weights."),
                options=("A group's female gross enrolment ratio over its male one, each summed over the group's "
                         "countries, so each sex is weighted by its own school-age population",
                         "The average of the countries' ratios, weighted by total school-age population"),
                adopted="A group's female gross enrolment ratio over its male one, each summed over the group's "
                        "countries, so each sex is weighted by its own school-age population",
                reason="The sentence weights averages by school-age populations, and a gross enrolment ratio is "
                       "defined per sex over its own population. Taking the ratio of the two group ratios keeps that "
                       "definition at group level. Adopted before any comparison; awaiting the owner."),
    ),
    rounding=Rounding(decimals=2),
)

CARD_32 = MethodCard(
    id="method:mdg-3-2", title="MDG 3.2 - Share of women in wage employment in the non-agricultural sector",
    subject="indicator:mdg-3-2", origin=Origin.PUBLISHED,
    steps=(
        MethodStep(number=1, name="Share per country", shell=None,
                   action="Women in non-agricultural paid employment over all persons in it, per country.",
                   citation=Citation(document=META, locator=f"{META_722}, Method of computation",
                                     quote="The indicator is calculated as the number of women in non-agricultural "
                                           "paid employment divided by the total number of persons in paid "
                                           "employment in the non-agricultural sector.")),
        MethodStep(number=2, name="Weight by 1990 non-agricultural labour force", shell=None,
                   action="Average over each group, weighted by each country's economically active population in "
                          "the non-agricultural sector in 1990.",
                   citation=Citation(document=META, locator=f"{META_722}, Regional and Global estimates",
                                     quote="in the benchmark year 1990")),
        MethodStep(number=3, name="Impute missing countries", shell=None,
                   action="The publisher imputes missing countries with models it does not release.",
                   citation=Citation(document=META, locator=f"{META_722}, Treatment of missing values",
                                     quote="These imputed values are used solely for the production of the regional "
                                           "and global estimates of the indicator.")),
    ),
    published_values=(
        PublishedValue(name="country shares, 2015 edition", after_step=1,
                       description="The MDG database's final country values, last updated 6 July 2015.",
                       citation=Citation(document=META, locator=f"{SERIES_722}, table",
                                         quote="Last updated: 06 Jul 2015")),
        PublishedValue(name="regional table", after_step=2,
                       description="The annex prints each region's share for 1990, 2000, 2005 and 2013.",
                       citation=Citation(document=REPORT, locator=ANNEX_32,
                                         quote="Share of women in wage employment in the")),
    ),
    rounding=Rounding(decimals=1),
)

INDICATOR_31 = Indicator(
    id="indicator:mdg-3-1", title="Ratios of girls to boys in primary, secondary and tertiary education",
    framework="MDG", code="3.1", unit="ratio", method=CARD_31.id,
    sources=(META, REPORT, "source:uis-api"), repro_class=ReproClass.B,
)
INDICATOR_32 = Indicator(
    id="indicator:mdg-3-2", title="Share of women in wage employment in the non-agricultural sector",
    framework="MDG", code="3.2", unit="percent", method=CARD_32.id,
    sources=(META, REPORT), repro_class=ReproClass.C,
)
