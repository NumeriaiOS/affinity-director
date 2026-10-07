#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def exists(*names): return any((ROOT/name).exists() for name in names)
def main():
    checks={'dockerfile':exists('Dockerfile'),'readme':exists('README.md'),'license':exists('LICENSE','LICENSE.md','LICENSE.txt'),'env_example':exists('.env.example'),'backend_requirements':exists('backend/requirements.txt'),'submission_checklist':exists('docs/SUBMISSION_CHECKLIST.md')}
    blockers=[name for name,ok in checks.items() if not ok]
    print(json.dumps({'checks':checks,'local_blockers':blockers,'external_blockers':['Qloo API key/live validation','external demo URL','public repository URL'],'ready_for_submission':False},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
