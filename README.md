# Affinity Director

Affinity Director is an agentic cultural-planning prototype for the Qloo Agentic Hackathon. It starts from a small set of taste signals and a location, explores several cultural domains, ranks candidates, removes cross-domain duplication, and exposes why each recommendation is connected to the input signals.

The core product thesis is simple: a planning agent should not guess cultural fit from language-model priors alone. Qloo is intended to provide the cultural grounding and affinity evidence; the agent provides orchestration, scoring, coherence and product UX around that evidence.

## Current status

Public demo: https://affinity-director-qloo.onrender.com

Public source: https://github.com/NumeriaiOS/affinity-director

The public Render deployment is running in verified live Qloo mode. A clearly labeled synthetic-fixture path remains available for offline development and tests; synthetic results are never presented as Qloo data. Live mode is gated by both `QLOO_API_KEY` and `QLOO_LIVE_ENABLED`.

Current local capabilities:

- cross-domain agent orchestration across music, venues, brands and film;
- Qloo API v2 request builder and client;
- explicit preservation of raw affinity separately from the product-level Cultural Fit Score;
- deterministic coherence/deduplication;
- explainability graph generation from explicit per-result contribution metadata only;
- conservative Qloo signal resolution: exact name matches use explicit entity IDs, while non-exact phrases stay on Qloo's native named-query path;
- generic baseline vs grounded-pipeline comparison surface;
- deterministic synthetic evaluation harness;
- container deployment definition and submission preflight.

### Verified live state

On 2026-10-09 the public deployment passed real-Qloo canaries on music, venue, brand and film. Both validation scenarios returned complete four-domain selections with zero provider failures. The explainability graph reached `1.0` candidate evidence coverage using only contributions that could be tied to explicitly resolved signal IDs; ambiguous phrases were left on Qloo's named-query path rather than force-mapped to a fuzzy search result. The baseline comparison's evidence metric matched the graph coverage. See `reports/live_validation.json`.

This is an integration/orchestration validation, not a human-preference benchmark and not a claim that the product outperforms a generic model on recommendation quality.

## Architecture

```text
Taste signals + location
        |
        v
Agent task planner
        |
        +--> artist discovery
        +--> place discovery
        +--> brand discovery
        +--> movie discovery
        |
        v
Qloo affinity + explainability
        |
        v
Cultural Fit scoring
        |
        v
Cross-domain coherence / dedupe
        |
        +--> recommendation cards
        +--> explainability graph
        +--> baseline comparison
```

Qloo is the intended grounding/ranking source. The app is designed to materially lose evidence and cultural specificity if Qloo is removed.

## Local development

Requirements: Python 3.14+.

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/pytest -q
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8090
```

Open `http://127.0.0.1:8090`.

Without a Qloo key, the UI runs in synthetic demo mode and labels that state explicitly.

## Live Qloo mode

Never commit credentials. Configure the key in the runtime environment:

```bash
export QLOO_API_KEY='...'
PYTHONPATH=backend .venv/bin/python tools/live_validation.py
```

The public deployment has passed the live-validation gate. For a new environment or after parser changes, rerun the gate before enabling live mode. See `docs/LIVE_VALIDATION.md`.

## Evaluation

Synthetic orchestration evaluation:

```bash
PYTHONPATH=backend .venv/bin/python tools/evaluate_agent.py
```

Submission readiness:

```bash
.venv/bin/python tools/submission_preflight.py
```

The baseline comparison currently measures structural diagnostics only. It does not claim that fixture data demonstrates real Qloo superiority.

## Container deployment

A generic `Dockerfile` is included. Any external hosting service capable of running a container and supplying environment variables can host the app.

```bash
# Example shape only; Docker is not required for local development.
docker build -t affinity-director .
docker run --rm -p 8000:8000 -e QLOO_API_KEY='...' -e QLOO_LIVE_ENABLED=true affinity-director
```

## Repository map

- `backend/app/` — API, orchestration and UI
- `backend/tests/` — unit/contract tests
- `tools/evaluate_agent.py` — synthetic deterministic evaluation
- `tools/live_validation.py` — real-Qloo validation gate
- `tools/submission_preflight.py` — local submission checks
- `docs/` — architecture, live gate and submission checklist
- `submission/` — draft judge-facing submission materials

## Security and integrity

- API keys are environment-only and ignored by Git.
- Requests are bounded by Pydantic validation.
- Mock and live modes are deliberately distinct.
- Missing affinity/explainability is not fabricated.
- The explainability graph emits edges only when explicit numeric evidence exists.

## License

Affinity Director is released under the [MIT License](LICENSE).

## Reproducible development checks

From the repository root:

```bash
make test
make eval
make check
```

`make test` uses the repository-level pytest configuration, so imports resolve consistently from any shell. The synthetic evaluation validates orchestration invariants only; it does not make claims about real Qloo recommendation quality.
