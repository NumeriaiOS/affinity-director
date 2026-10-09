# Live Qloo validation gate

## Current verified state

The public Render deployment passed the live gate on 2026-10-09 with `QLOO_LIVE_ENABLED=true`. Two real-Qloo scenarios completed all four target domains with zero provider failures and `verification.status=complete`. Candidate evidence coverage was `1.0` after mapping explainability only through exact Qloo entity resolutions. Non-exact phrases remained on the native named-query path and were not assigned a guessed entity ID. A sanitized proof report is tracked at `reports/live_validation.json`.

This gate validates integration, schema handling and orchestration. It does not by itself establish human preference or recommendation superiority.

## Reproducing the gate
This gate must pass before making recommendation-quality claims from Qloo data.

1. Obtain a Qloo API key through the official hackathon developer flow.
2. Export `QLOO_API_KEY` locally; never commit it.
3. Run `make live-validate` from the repository root.
4. Inspect `reports/live_validation.json`.
5. Inspect raw response samples under `reports/live_samples/` only when adapting parsers. That directory is ignored by Git; remove temporary samples after inspection.
6. Confirm each target domain returns identifiable entities and the final verifier is `complete`.
7. Inspect observed raw affinity values instead of assuming a response scale.
8. Check per-result `query.explainability` and top-level `query.explainability`; explainability absence is diagnostic because Qloo may return a warning when it cannot be computed.
9. For the location-scoped venue query, inspect locality metadata and the returned place entities.
10. Update parsers only from observed Qloo responses; never weaken validation merely to force a pass.
11. Freeze the resulting evaluation set before comparing the grounded path with the generic baseline.
12. Only after this gate passes, set `QLOO_LIVE_ENABLED=true` and restart the app. Merely configuring `QLOO_API_KEY` does not enable live recommendations.

The live validator captures each domain response once and replays those exact responses through the full orchestrator. This avoids consuming duplicate API calls while validating the end-to-end normalization, scoring, coherence, blueprint, graph and verifier path.

Synthetic fixtures validate orchestration invariants only; they do not measure real Qloo recommendation quality.
