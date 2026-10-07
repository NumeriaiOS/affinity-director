# Affinity Director — Devpost draft

## One-line description

An agent that turns a few cultural taste signals into a coherent cross-domain experience plan, using Qloo for affinity grounding instead of relying on generic AI intuition.

## The problem

General-purpose agents can reason about logistics, but cultural recommendations are often based on broad stereotypes or model priors. Event planners, creative teams and experience designers need to know not only what is plausible, but what actually fits the audience across music, venue, film, fashion and adjacent categories.

## What Affinity Director does

A user supplies several taste signals and, optionally, a location. Affinity Director plans a set of domain-specific discovery tasks, queries Qloo, keeps the returned affinity and explainability evidence, ranks candidates, removes duplicate or over-concentrated results, and produces one cross-domain direction.

The interface also exposes an evidence graph connecting input signals to recommendations. This makes the cultural reasoning inspectable instead of presenting a black-box list.

## Why Qloo matters

Qloo is intended to be the grounding layer, not a decorative API call. Without Qloo, the system falls back to a generic deterministic baseline that can suggest categories but has no affinity evidence or defensible cross-domain cultural grounding.

Affinity Director preserves Qloo affinity separately from its own Cultural Fit Score so judges can distinguish source data from product-level ranking logic. Explainability relationships are shown only when explicit contribution metadata is present.

## Agentic workflow

1. Validate and normalize taste signals.
2. Plan cross-domain Qloo discovery tasks.
3. Explore artists, places, brands and films.
4. Normalize affinity and retain raw source values.
5. Score candidates with transparent confidence labels.
6. Run a coherence pass to remove duplication and preserve domain diversity.
7. Build an explainability graph from explicit evidence.
8. Present the resulting direction and a baseline comparison.

## Technical implementation

- Python / FastAPI backend
- Qloo API v2 integration
- deterministic orchestration and scoring
- bounded request validation
- synthetic fixture mode for development only
- live-validation gate before real-quality claims
- single-page judge-facing web UI
- container-ready deployment

## What is still pending

This draft intentionally contains no claims based on synthetic fixtures. The public source repository is now available at `https://github.com/NumeriaiOS/affinity-director`. Before submission, replace this section with measured results from the live Qloo validation set and add the verified public demo URL.
