# Affinity Director — Qloo Agentic Hackathon

Working repository for the Qloo Agentic Hackathon.

## Product direction

**Affinity Director** turns a small set of cultural taste signals into a coherent cross-domain experience direction. The agent fans out across music, venue/place, brand and film discovery, then ranks and reconciles candidates instead of relying on a single generic LLM answer.

Qloo is designed as the grounding layer. The product keeps Qloo affinity separate from its own transparent **Cultural Fit Score** so the demo never presents a derived score as if it came directly from Qloo.

## Current runtime

- FastAPI backend in `backend/`
- Demo UI served by the backend
- Qloo API v2 client and query preview
- Cross-domain orchestrator
- Affinity normalization, explainability diagnostics and coherence selection
- Deterministic synthetic fixture mode while registration/API credentials are unavailable
- Live Qloo mode automatically becomes available when `QLOO_API_KEY` is configured

## Run

```bash
cd /mnt/seagate/Projects/Qloo/backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8090
```

Tests:

```bash
cd /mnt/seagate/Projects/Qloo/backend
/mnt/seagate/Projects/Qloo/.venv/bin/python -m pytest -q
```

Offline orchestration evaluation:

```bash
cd /mnt/seagate/Projects/Qloo
/mnt/seagate/Projects/Qloo/.venv/bin/python tools/evaluate_agent.py
```

The evaluation report is written to `reports/demo_eval.json`. It validates deterministic orchestration invariants only; it is not evidence of real Qloo recommendation quality.

## Security

Do not commit API keys. Copy `.env.example` to `.env` locally when credentials are available.
