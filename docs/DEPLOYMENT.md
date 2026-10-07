# Deployment notes

The hackathon requires a fully published external demo. The repository therefore includes a generic container definition rather than binding the project to one hosting vendor before credentials are available.

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
