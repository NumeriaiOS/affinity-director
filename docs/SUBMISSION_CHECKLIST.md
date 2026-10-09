# Submission checklist

## Required
- Functional end-to-end demo application.
- Demo hosted externally and fully published; localhost-only does not qualify.
- Public GitHub, GitLab or Bitbucket repository.
- Repository contains source code, assets and run instructions.
- Open-source license file visible/detectable on the repository page.
- English project description explaining features and why the project is Qloo-powered.
- Project genuinely integrates the Qloo API and is agentic.
- Free judge access through the end of judging.

## Affinity Director readiness
- [x] Agent orchestration skeleton
- [x] Qloo API v2 client
- [x] Cross-domain fan-out
- [x] Cultural Fit scoring with raw affinity retained
- [x] Coherence/deduplication
- [x] Explainability graph plumbing
- [x] Generic baseline comparison surface
- [x] Synthetic fixtures clearly labeled
- [x] Deterministic evaluation harness
- [x] Container deployment definition
- [x] Real Qloo API key and live validation
- [x] Freeze response parser from observed live payloads
- [ ] Real A/B evaluation results
- [x] External hosting URL — https://affinity-director-qloo.onrender.com
- [x] Public repository URL — https://github.com/NumeriaiOS/affinity-director
- [x] Choose and add open-source license (MIT)
- [x] Final English Devpost description
- [x] Judge testing instructions

## Automated preflight

Run `make preflight` at any time for a non-failing readiness report. To reproduce submission readiness, export the actual public URLs and run the strict gate:

```bash
export PUBLIC_DEMO_URL=https://your-live-demo.example
export PUBLIC_REPO_URL=https://github.com/owner/repository
export QLOO_LIVE_ENABLED=true
make preflight-strict
```

The strict gate also requires a passing `reports/live_validation.json`, a clean Git worktree and an open-source license file. Do not set `QLOO_LIVE_ENABLED=true` until the live validation gate has passed.
