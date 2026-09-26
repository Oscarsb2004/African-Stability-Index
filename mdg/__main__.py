"""python -m mdg fetch | build | check

fetch  downloads every source once (then it is served from the cache) and records its hash in sources.lock
build  builds every catalogue row and writes the common-format table to a run folder in the store
check  builds, then compares with the publishers and writes the scoreboard and the divergences
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone

from athena.fetch import STORE
from athena.table import canonical_hash, round_half_up
from mdg.build import HERE, build, open_project

OUTPUT_DECIMALS = 3  # P33: full precision in the math; outputs stored at three decimals


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True).stdout.strip()


def fetch(project) -> None:
    for key, source in project.sources.items():
        if "{" not in source["url"]:
            project.get(key)
    for row in project.catalogue["indicator"]:
        years = ";".join(f"YR{y}" for y in row["years"])
        for ref in row["inputs"].values():
            key, series = ref.split("/", 1)
            if project.sources[key]["kind"] == "wdi-archive":
                project.get(key, series=series, years=years)
    print(f"{len(project.fetcher.lock)} addresses fetched and locked in {project.fetcher.lock_path.name}")


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("fetch", "build", "check"):
        print(__doc__)
        return 2
    project = open_project()
    if argv[0] == "fetch":
        fetch(project)
        return 0

    built = build(project)
    commit = _git("rev-parse", "HEAD")
    locked = _git("status", "--porcelain", "catalogue.toml") == ""
    run = STORE / "runs" / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{commit[:7]}"
    run.mkdir(parents=True)
    stored = built.outputs.assign(OBS_VALUE=[round_half_up(v, OUTPUT_DECIMALS) for v in built.outputs["OBS_VALUE"]])
    stored.to_csv(run / "outputs.csv", index=False)
    record = {"commit": commit, "catalogue_committed": locked, "rows": len(built.outputs),
              "outputs_hash": canonical_hash(built.outputs)}

    if argv[0] == "check":
        from mdg.check import check

        checked = check(project, built)
        checked.scoreboard.to_csv(run / "scoreboard.csv", index=False)
        checked.divergences.to_csv(run / "divergences.csv", index=False)
        record |= {"quote_problems": checked.quote_problems}
        print(checked.scoreboard.to_string(index=False))
        for problem in checked.quote_problems:
            print("quote:", problem)
    (run / "run.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"{record['rows']} rows, {record['outputs_hash']}")
    if not locked:
        print("catalogue.toml has uncommitted changes: this run is not locked to a commit")
    print(f"written to {run}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
