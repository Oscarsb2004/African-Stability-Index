# AGENTS.md — athena-core

Read this whole file before doing anything.

## 1. What this repository is

The shared backend of Athena. It holds two kinds of code, under different rules:

- **The contracts** (`src/athena/`): the definitions and base classes every project is built on - ids, sources, method cards, frames, steps, validation, runs. They exist before any project because every project needs them from its first line (decision P16).
- **Shared shells**: steps used unchanged by two projects (decision P6, `std:MOD-01`). None yet. A shell enters only through an extraction pull request that keeps both consuming projects' checks passing.

## 2. Before any change

1. Read the umbrella's `AGENTS.md`; its start protocol applies here.
2. Your section brief must be `ready` or `in-progress` and must name this repository.
3. A change to a contract is a change every project feels. It needs a recorded decision in the umbrella.

## 3. Rules specific to this repository

- **Definitions are data; behaviour is in a few small base classes.** A definition is an immutable, validated record that refuses unknown fields. Behaviour lives in `FormatReader` and `Step`.
- **Steps are pure.** They receive frames and parameters and return a frame, with no network and no clock. Only a reader's `fetch` touches the network, and only through the transport it is given.
- **The answer key is sealed.** Pipeline code never reads published values; it can only compare against them.
- **Never import a project repository.** Projects depend on this one, not the reverse.
- **Every check has a negative control** that fails it.
- **Every part has a card** in the umbrella's `registry/`; the card's status changes to proven only with owner approval.
- **Breaking a contract** is a major version change.
- **Dependencies are pinned** in `pyproject.toml` and `requirements.lock`.

## 4. Commands

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.lock
.venv/Scripts/python -m pytest -q
```

## 5. When something is unclear

Write a Finding in the pull request and take the conservative reading. Never guess a design decision; the owner makes those.
