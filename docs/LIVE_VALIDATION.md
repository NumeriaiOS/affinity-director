# Live Qloo validation gate

This gate must be completed before making any recommendation-quality claim.

1. Obtain a Qloo API key through the official hackathon developer flow.
2. Export `QLOO_API_KEY` locally; never commit it.
3. Run `PYTHONPATH=backend .venv/bin/python tools/live_validation.py`.
4. Inspect `reports/live_validation.json`.
5. Confirm all target domains return non-empty results.
6. Inspect real response shapes, raw affinity values and per-result explainability.
7. Update parsers only from observed Qloo responses; do not weaken validation to force a pass.
8. Freeze a small evaluation set and compare the Qloo-grounded path against the generic baseline.
9. Only after this gate passes should UI copy switch from synthetic/demo wording to live claims.

Synthetic fixtures validate orchestration, scoring, diversity and explainability plumbing only.
