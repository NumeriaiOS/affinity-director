PYTHON ?= .venv/bin/python
PYTEST ?= .venv/bin/pytest

.PHONY: test eval secret-scan live-validate preflight preflight-strict check run

test:
	$(PYTEST) -q

eval:
	$(PYTHON) tools/evaluate_agent.py

secret-scan:
	$(PYTHON) tools/secret_scan.py

live-validate:
	$(PYTHON) tools/live_validation.py

preflight:
	$(PYTHON) tools/submission_preflight.py

preflight-strict:
	$(PYTHON) tools/submission_preflight.py --strict

check: test eval secret-scan
	git diff --check

run:
	cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --log-level warning
