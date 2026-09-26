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
                adopted="The list as the official groupings document gives it (as of 1 January 2011)",
                reason="It is the list the IAEG published as its grouping. The later list would be our choice, "
                       "not the publisher's. Any divergence in this row is expected and will be classed."),
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
