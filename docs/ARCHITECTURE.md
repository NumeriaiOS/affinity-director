# Architecture v0.3

Taste signals + optional location
  -> Qloo API v2 request construction
  -> cross-domain fan-out (artist / place / brand / movie)
  -> normalize Qloo entity results
  -> preserve raw affinity + per-result explainability
  -> Cultural Fit Score
  -> global de-duplication
  -> round-robin domain coherence selection
  -> judge-facing result cards + execution trace

## Score separation

`affinity_raw` is the provider value. `affinity_score` is only a display normalization to 0-100 when the raw value is interpretable. `cultural_fit` is an Affinity Director product metric dominated by affinity, with small rank/explainability components. It is never labeled as a Qloo metric.

If affinity is missing, the system does not fabricate one: Cultural Fit becomes conservative and low-confidence.

## Demo / live split

`demo_fixture` uses deterministic synthetic entities and is visibly labeled as synthetic. It exists so UI, orchestration and scoring can be built before the API key is available.

`live` uses the Qloo v2 `/insights` provider. No fallback silently converts a failed live request into fixture data.

## Design rule

The product must materially degrade when Qloo is removed. Qloo is therefore the grounding and ranking layer, not a decorative post-processing call.

## Evaluation plan after credentials

For matched briefs compare:
1. generic baseline
2. Qloo-grounded agent

Measure entity-resolution success, affinity coverage, cross-domain diversity, duplicate rate, explanation coverage, latency and human/judge preference.
