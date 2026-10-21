---
type: "project-page"
project: "African Stability Index"
section: "04 Methods"
status: "built"
created: "2026-10-18"
updated: 2026-10-18
---

# ASI Method Transformations

> [!abstract] Goal
> Transform a skewed indicator only when a stated test says so, by a stated formula.

## Why it exists

Edition 1 flagged five indicators for logs without ever applying a rule, while unflagged ones were as skewed.

## Precise objectives

1. Skew test: z = skew / SE(skew), significant beyond ±1.96, after outlier treatment.
2. Log by Osborne's rule, with a constant that makes the minimum 1.
3. Total GDP is scored on a log scale (P50).

## Inputs and outputs

- **In:** indicator distributions
- **Out:** a transformation flag and formula per indicator

## Where it stands

Built (edition 2, step 4, athena-core #14). The skew test runs on each state's latest observed value; 12 indicators are logged (edition 1: 5), mort_infant no longer. Five significantly left-skewed indicators (the two parity distances, primary enrolment, youth literacy, learning poverty) are not logged: whether to reflect and log them is the owner's ruling. Composites moved 1.57 points on average; rank correlation .988.

## Open questions

- Reflect and log the five left-skewed indicators, or leave them as they are?

## Related

ASI next edition plan (athena-data)
