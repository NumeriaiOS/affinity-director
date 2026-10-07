PYTHON ?= .venv/bin/python
PYTEST ?= .venv/bin/pytest

.PHONY: test eval live-validate preflight preflight-strict check run

test:
	$(PYTEST) -q

eval:
	$(PYTHON) tools/evaluate_agent.py

live-validate:
	$(PYTHON) tools/live_validation.py

preflight:
	$(PYTHON) tools/submission_preflight.py

preflight-strict:
	$(PYTHON) tools/submission_preflight.py --strict

check: test eval
	git diff --check

run:
	cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8090 --log-level warning
