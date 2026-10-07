# Deployment notes

The public demo is deployed on Render at `https://affinity-director-qloo.onrender.com` from the public GitHub repository `https://github.com/NumeriaiOS/affinity-director`. The repository also retains a generic Docker definition so the service remains portable.

Runtime requirements:

- Python 3.14-compatible container/runtime
- `PORT` environment variable supported (defaults to 8000)
- `QLOO_API_KEY` supplied as a secret environment variable
- `QLOO_LIVE_ENABLED=true` only after live validation passes
- outbound HTTPS access to the Qloo API
- public HTTPS URL

Before exposing the demo publicly:

1. run the unit tests;
2. run the real Qloo live-validation gate;
3. run submission preflight;
4. confirm public `/health` reports `qloo_configured: true` and public `/ready` reports `qloo_live_ready: true`;
5. verify the UI never displays synthetic-fixture wording in live mode;
6. verify the public service can be used without paid access or private-network dependencies.


## Render Blueprint

The repository includes `render.yaml` for a Docker-based Render web service on the free plan in Frankfurt. The Blueprint keeps `QLOO_API_KEY` as a dashboard-supplied secret (`sync: false`) and starts with `QLOO_LIVE_ENABLED=false`.

Create/sync the Blueprint from the public repository, provide the Qloo API key only in Render, and keep live mode disabled until `make live-validate` passes against the real API. After validation, set `QLOO_LIVE_ENABLED=true` in Render and redeploy. The service health check is `/ready`.
