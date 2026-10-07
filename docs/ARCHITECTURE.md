# Architecture v0

User brief
  -> intent / constraint extraction
  -> Qloo entity resolution
  -> iterative Qloo taste queries
  -> candidate generation across domains
  -> cultural-fit scoring + evidence
  -> planner / verifier loop
  -> final experience plan + explainability graph

## Design rule

The product must materially degrade when Qloo is removed. Qloo is therefore the grounding and ranking layer, not a decorative post-processing call.

## Initial measurable comparison

For the same brief, compare:
1. generic LLM-only plan
2. Qloo-grounded plan

Evaluate diversity, cross-domain coherence, evidence coverage and user/judge preference.
