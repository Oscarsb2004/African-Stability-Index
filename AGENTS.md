# AGENTS.md: athena-core

Start with the umbrella's `AGENTS.md` and `Athena Data/Plan.md` in `athena-data`. The rules there apply here. In
particular: reuse permissively licensed libraries first, keep the code minimal, and never build one indicator on
its own.

## Rules specific to this repository

- **Three layers (P37).** Adapters read one database each. Shells never name a subject. Projects are configuration.
- **Nothing is dropped silently.** A reader that meets a row, heading or name it does not recognise stops with an
  error. Unmapped names are reported together.
- **Fetch once.** Every source goes through `athena.fetch`, and its hash is locked in git. A changed source is refused.
- **The answer key is sealed.** Only the check reads published values; a test enforces it.
- **Precision.** The math runs in full precision. A comparison rounds once, half up, to the publisher's decimals.
- **Tests use synthetic fixtures,** and every check has a negative control. Dependencies are pinned in
  `pyproject.toml` and `requirements.lock`.
