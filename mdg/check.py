"""Every built value against what the publishers printed, and every method quote against its document. The only
module that reads `mdg.answers`."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from athena.check import compare, summary
from mdg import answers, readers
from mdg.build import Built, Project

TEXT = {"html": readers.html_text, "annex-pdf": lambda d: " ".join(readers.pdf_pages(d)),
        "groupings-doc": readers.doc_text}


@dataclass
class Checked:
    scoreboard: pd.DataFrame
    divergences: pd.DataFrame
    quote_problems: list[str]


def _normal(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def quotes(project: Project) -> list[str]:
    """Each quote on a method must appear verbatim in the document it cites."""
    problems, texts = [], {}
    for row in project.catalogue["indicator"]:
        for step in row.get("method", []):
            key = step["source"]
            if key not in texts:
                texts[key] = _normal(TEXT[project.sources[key]["kind"]](project.get(key)))
            if _normal(step["quote"]) not in texts[key]:
                problems.append(f"{row['id']}: not found verbatim in {key}: {step['quote'][:60]!r}")
    return problems


def check(project: Project, built: Built) -> Checked:
    groups = set(built.members["group"])
    annex_rows = {}
    board, divergences = [], []

    def record(row: dict, year: int, name: str, compared: pd.DataFrame) -> None:
        board.append({"indicator": row["id"], "year": year, "check": name, "class": row["class"]} | summary(compared))
        wrong = compared[~compared["match"] & compared["published"].notna()]
        for key, r in wrong.iterrows():
            divergences.append({"indicator": row["id"], "year": year, "check": name, "key": key,
                                "ours": r["ours"], "rounded": r["rounded"], "published": r["published"]})

    for row in project.catalogue["indicator"]:
        ours_all = built.outputs[built.outputs["INDICATOR"] == row["id"]]
        for year in row["years"]:
            ours = ours_all[ours_all["TIME_PERIOD"] == year].set_index("REF_AREA")["OBS_VALUE"]
            is_group = ours.index.isin(groups)

            if row["annex"] not in annex_rows:
                annex_rows[row["annex"]] = readers.annex(project.get("annex-2015"), row["annex"])
            published = answers.regional(annex_rows[row["annex"]], row.get("part", ""), year)
            record(row, year, "regions", compare(ours[is_group], published, row["decimals"]))

            source = project.sources[row["countries"]]
            if source["kind"] == "ipu-classification":
                published = answers.ipu_countries(project.get(row["countries"]), built.coder)
            else:
                published = answers.series(project.get(row["countries"]), built.coder, year)
            record(row, year, "countries", compare(ours[~is_group], published, row["decimals"]))

            if "world_totals" in row:
                world = built.sums[(row["id"], year)].loc["world"]
                printed = answers.ipu_world_totals(project.get(row["world_totals"]))
                record(row, year, "world totals", compare(world[printed.index].astype(float), printed, 0))
    built.coder.done()
    return Checked(pd.DataFrame(board), pd.DataFrame(divergences), quotes(project))
