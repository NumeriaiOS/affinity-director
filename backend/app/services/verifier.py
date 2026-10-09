from __future__ import annotations

REQUIRED_DOMAINS = ("music", "venue", "brand", "film")


def verify_selection(items: list[dict], required_domains: tuple[str, ...] = REQUIRED_DOMAINS) -> dict:
    present = sorted({str(item.get("domain")) for item in items if item.get("domain")})
    missing = [domain for domain in required_domains if domain not in present]
    evidence_items = sum(1 for item in items if item.get("signal_influences"))
    evidence_coverage = round(evidence_items / len(items), 4) if items else 0.0

    if not missing:
        status = "complete"
    elif len(present) >= max(2, len(required_domains) - 1):
        status = "partial"
    else:
        status = "insufficient"

    return {
        "status": status,
        "required_domains": list(required_domains),
        "present_domains": present,
        "missing_domains": missing,
        "item_count": len(items),
        "explicit_evidence_coverage": evidence_coverage,
        "safe_to_present_as_complete": status == "complete",
    }
