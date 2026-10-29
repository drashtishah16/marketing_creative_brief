"""Unit tests for ClaimChecker and EvidenceChecker."""

from backend.claim_checker import ClaimChecker
from backend.evidence_checker import EvidenceChecker
from backend.database import init_db, get_connection


def test_detect_absolute_and_guarantee_claims():
    text = "We are the best tool on the market. 100% guaranteed results or money back."
    warnings = ClaimChecker.check_claims(text)

    types = {w["rule_name"] for w in warnings}
    assert "Absolute Superlative (#1 / The Best)" in types
    assert "Performance Guarantee" in types


def test_detect_numerical_performance_claim():
    text = "Boost your development speed by 45% and get 10x ROI within 30 days."
    warnings = ClaimChecker.check_claims(text)

    types = {w["rule_name"] for w in warnings}
    assert "Numerical Improvement Claim" in types
    assert "Multiplier Performance Claim" in types


def test_detect_sensitive_financial_claims():
    text = "Sign up for our crypto bot and enjoy guaranteed returns and passive income!"
    warnings = ClaimChecker.check_claims(text)

    sensitive = [w for w in warnings if w["rule_name"] == "Sensitive Financial Return Claim"]
    assert len(sensitive) > 0
    assert sensitive[0]["severity"] == "High"


def test_discount_without_conditions():
    text = "Get 50% off right now!"
    warnings = ClaimChecker.check_claims(text, offer_conditions="")
    assert any(w["rule_name"] == "Discount Missing Terms" for w in warnings)


def test_corroborated_claim_lowered_severity():
    text = "Delivers 99.9% uptime for enterprise teams."
    verified_facts = ["Historical data shows 99.9% uptime over 3 years"]
    warnings = ClaimChecker.check_claims(text, verified_facts=verified_facts)

    uptime_warning = next(w for w in warnings if "99.9% uptime" in w["fragment"].lower())
    assert uptime_warning["is_corroborated"] is True
    assert uptime_warning["severity"] == "Low"


def test_evidence_checker_persistence_and_update(tmp_path):
    test_db = tmp_path / "evidence_test.db"
    init_db(test_db)

    # Insert mock campaign and variant first for FK integrity
    conn = get_connection(test_db)
    with conn:
        conn.execute(
            """
            INSERT INTO campaigns (id, name, product_name, product_description, target_audience, objective, channel, tone_of_voice, created_at, updated_at)
            VALUES ('camp-1', 'C1', 'P1', 'Desc', 'Audience', 'conversions', 'social media', 'professional', '2026-01-01', '2026-01-01')
            """
        )
        conn.execute(
            """
            INSERT INTO ad_variants (id, campaign_id, name, angle, hook, headline, body_copy, cta, channel, target_audience, primary_message, created_at, updated_at)
            VALUES ('var-1', 'camp-1', 'V1', 'Angle', 'Hook', 'Headline', 'Copy', 'CTA', 'social media', 'Audience', 'Msg', '2026-01-01', '2026-01-01')
            """
        )
    conn.close()

    ev_checker = EvidenceChecker(test_db)
    raw_warnings = [
        {
            "category": "Claim Verification",
            "rule_name": "Performance Guarantee",
            "severity": "High",
            "fragment": "100% guaranteed",
            "explanation": "Needs refund terms.",
            "evidence_required": "Legal refund policy.",
            "is_corroborated": False,
        }
    ]

    claim_ids = ev_checker.register_claim_warnings("camp-1", "var-1", raw_warnings)
    assert len(claim_ids) == 1

    # Initially unresolved high severity claim exists
    assert ev_checker.count_unresolved_high_severity("var-1") == 1

    # Now update decision with evidence source
    success = ev_checker.update_claim_decision(
        claim_id=claim_ids[0],
        decision="Accepted with Evidence",
        evidence_source="https://example.com/refund-terms.pdf",
        document_reference="Section 4.2 Refund Policy",
        reviewer_notes="Verified against official terms.",
    )
    assert success is True
    # Now count of unresolved should be 0
    assert ev_checker.count_unresolved_high_severity("var-1") == 0
