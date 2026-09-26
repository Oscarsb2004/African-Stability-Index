"""The sources and recipes phase 1 reads. The ids match the source cards in the athena-data registry."""

from __future__ import annotations

from datetime import date

from athena.sources import Recipe, SourceCard, Terms
from athena.vocab import Access, Redistribution

READ_ON = date(2026, 9, 25)
WAYBACK = "https://web.archive.org/web/{stamp}id_/{url}"

IPU = SourceCard(
    id="source:ipu-women-in-parliament-archive", title="IPU archive - Women in national parliaments",
    publisher="Inter-Parliamentary Union", access=Access.WEB,
    terms=Terms(url="https://www.ipu.org/terms-use", read_on=READ_ON, redistribution=Redistribution.FORBIDDEN,
                summary="Research or personal use only; not for sale or commercial purposes."),
    readers=("reader:ipu-classification-html", "reader:ipu-world-html"),
)
MDG_DOCS = SourceCard(
    id="source:un-mdg-archive-documents", title="Archived MDG metadata and regional groupings",
    publisher="UNSD for the IAEG on MDG Indicators, via the Internet Archive", access=Access.WEB,
    terms=Terms(url="https://www.un.org/en/about-us/terms-of-use", read_on=READ_ON,
                redistribution=Redistribution.FORBIDDEN, summary="Personal, non-commercial use only."),
    readers=("reader:mdg-groupings-doc", "reader:html-text"),
)
MDG_REPORT = SourceCard(
    id="source:un-mdg-report-2015", title="The MDG Report 2015 and its statistical annex",
    publisher="United Nations", access=Access.DOCUMENT,
    terms=Terms(url="https://www.un.org/en/about-us/terms-of-use", read_on=READ_ON,
                redistribution=Redistribution.FORBIDDEN, summary="Personal, non-commercial use only."),
    readers=("reader:mdg-annex-pdf",),
)
M49 = SourceCard(
    id="source:un-m49", title="UN M49 standard country or area codes",
    publisher="United Nations Statistics Division", access=Access.WEB,
    terms=Terms(url="https://www.un.org/en/about-us/terms-of-use", read_on=READ_ON,
                redistribution=Redistribution.FORBIDDEN, summary="Personal, non-commercial use only."),
    readers=("reader:m49-html",),
)

LDC_LIST = SourceCard(
    id="source:un-desa-ldc-list", title="UN DESA list of least developed countries",
    publisher="UN DESA, Committee for Development Policy secretariat, via the Internet Archive",
    access=Access.DOCUMENT,
    terms=Terms(url="https://www.un.org/en/about-us/terms-of-use", read_on=date(2026, 9, 26),
                redistribution=Redistribution.FORBIDDEN, summary="Personal, non-commercial use only."),
    readers=("reader:ldc-list-pdf",),
)
LLDC_LIST = SourceCard(
    id="source:un-ohrlls-lldc-list", title="UN-OHRLLS list of landlocked developing countries",
    publisher="UN-OHRLLS, via the Internet Archive", access=Access.WEB,
    terms=Terms(url="https://www.un.org/en/about-us/terms-of-use", read_on=date(2026, 9, 26),
                redistribution=Redistribution.FORBIDDEN, summary="Personal, non-commercial use only."),
    readers=("reader:lldc-profiles-html",),
)

SOURCES = {s.id: s for s in (IPU, MDG_DOCS, MDG_REPORT, M49, LDC_LIST, LLDC_LIST)}


def recipe(slug: str, title: str, source: SourceCard, reader: str, url: str) -> Recipe:
    return Recipe(id=f"recipe:{slug}", title=title, source=source.id, reader=reader, parameters={"url": url})


IPU_CLASSIFICATION = recipe(
    "ipu-classification-2015-02-01", "IPU world classification, 1 February 2015", IPU,
    "reader:ipu-classification-html", "http://archive.ipu.org/wmn-e/arc/classif010215.htm")
IPU_WORLD = recipe(
    "ipu-world-2015-02-01", "IPU world and regional averages, 1 February 2015", IPU,
    "reader:ipu-world-html", "http://archive.ipu.org/wmn-e/arc/world010215.htm")
GROUPINGS = recipe(
    "mdg-regional-groupings-doc", "Official MDG regional groupings (capture of 2014-10-20)", MDG_DOCS,
    "reader:mdg-groupings-doc",
    WAYBACK.format(stamp="20141020095627",
                   url="http://mdgs.un.org/unsd/mdg/Resources/Static/Data/Regional%20groupings.doc"))
METADATA_557 = recipe(
    "mdg-metadata-series-557", "MDG metadata, series 557 (capture of 2017-03-15)", MDG_DOCS, "reader:html-text",
    WAYBACK.format(stamp="20170315064103",
                   url="https://mdgs.un.org/unsd/mdg/Metadata.aspx?IndicatorId=0&SeriesId=557"))
ANNEX = recipe(
    "mdg-annex-2015", "MDG 2015 statistical annex (capture of 2015-09-12)", MDG_REPORT, "reader:mdg-annex-pdf",
    WAYBACK.format(stamp="20150912043121",
                   url="http://unstats.un.org/unsd/mdg/Resources/Static/Products/Progress2015/Statannex.pdf"))
M49_OVERVIEW = recipe(
    "m49-overview", "M49 overview table", M49, "reader:m49-html",
    "https://unstats.un.org/unsd/methodology/m49/overview/")

LDC_2014 = recipe(
    "un-ldc-list-2014-01", "List of least developed countries (capture of 2014-01-13)", LDC_LIST,
    "reader:ldc-list-pdf",
    WAYBACK.format(stamp="20140113124748", url="http://www.un.org/en/development/desa/policy/cdp/ldc/ldc_list.pdf"))
LLDC_2014 = recipe(
    "un-lldc-list-2014-12", "UN-OHRLLS LLDC country profiles (capture of 2014-12-31)", LLDC_LIST,
    "reader:lldc-profiles-html",
    WAYBACK.format(stamp="20141231235304", url="http://unohrlls.org:80/about-lldcs/country-profiles/"))

RECIPES = (IPU_CLASSIFICATION, IPU_WORLD, GROUPINGS, METADATA_557, ANNEX, M49_OVERVIEW, LDC_2014, LLDC_2014)
