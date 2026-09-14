# AGENTS.md — athena-core

Read this whole file before doing anything.

## 1. What this repository is

The shared backend of Athena. **It holds only parts proven by two projects.** It is empty until the first extraction (section S06 in `Oscarsb2004/athena-data`).

## 2. Before any change

1. Read the umbrella's `AGENTS.md`; its start protocol applies here.
2. Your section brief must be `ready` or `in-progress` and must name this repository.
3. **The only way code enters this repository is an extraction pull request.** It moves a part out of a project, and it keeps both consuming projects' checks passing.

## 3. Rules specific to this repository

- **Never import a project repository.** Projects depend on this one, not the reverse.
- **Every part arrives with its own tests**, including a negative control for each check.
- **Every part has a card** in the umbrella's `registry/`; the card's status changes to proven only with owner approval.
- **Breaking a part's contract** is a major version change.
- **Dependencies are pinned.**

## 4. When something is unclear

Write a Finding in the pull request and take the conservative reading. Never guess a design decision; the owner makes those.
