# Judge testing instructions — draft

## Goal

Evaluate whether Affinity Director uses Qloo as a meaningful cultural-intelligence layer rather than as a superficial integration.

## Suggested test

1. Open the public demo URL.
2. Enter three taste signals from different categories, for example an artist, a film/film studio and a fashion/design preference.
3. Add a city.
4. Run **Build direction**.
5. Confirm that results span multiple cultural domains and display affinity separately from Cultural Fit.
6. Inspect the agent trace and evidence/explainability information.
7. Run **Compare baseline**.
8. Compare the generic baseline with the Qloo-grounded path and inspect evidence coverage.

## What to look for

- Qloo materially affects candidate discovery and ranking.
- Results remain diverse across domains rather than collapsing into one category.
- The product does not invent evidence when Qloo does not provide it.
- Raw affinity remains distinguishable from Affinity Director's own score.
- The evidence graph makes signal-to-recommendation relationships inspectable.

## Access

Public demo URL: `PENDING`

Public source repository: `https://github.com/NumeriaiOS/affinity-director`

No paid account should be required for judge testing.
