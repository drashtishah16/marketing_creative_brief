"""Unit tests for BrandChecker rules."""

from backend.brand_checker import BrandChecker


def test_prohibited_phrases_detection():
    text = "Get our revolutionary product, it is the cheapest ever solution!"
    warnings = BrandChecker.check_text(
        text,
        prohibited_phrases=["cheapest ever", "unrivaled"],
    )
    assert any(w["rule_name"] == "Prohibited Phrase" and "cheapest ever" in w["explanation"] for w in warnings)


def test_missing_required_phrases():
    text = "Discover the newest smart fitness tracker today."
    warnings = BrandChecker.check_text(
        text,
        required_phrases=["Eco-Certified 2026", "Engineered with Care"],
    )
    missing = [w for w in warnings if w["rule_name"] == "Missing Required Phrase"]
    assert len(missing) == 2


def test_mandatory_disclaimer_missing():
    text = "Sign up now for our free subscription!"
    warnings = BrandChecker.check_text(
        text,
        mandatory_disclaimers=["Terms and conditions apply. 18+ only."],
    )
    assert any(w["rule_name"] == "Missing Mandatory Disclaimer" for w in warnings)


def test_mandatory_disclaimer_present():
    text = "Sign up now! Terms and conditions apply. 18+ only."
    warnings = BrandChecker.check_text(
        text,
        mandatory_disclaimers=["Terms and conditions apply. 18+ only."],
    )
    assert not any(w["rule_name"] == "Missing Mandatory Disclaimer" for w in warnings)


def test_tone_consistency_professional():
    text = "OMG this is crazy cheap and super cool!! Grab it now!"
    warnings = BrandChecker.check_tone_consistency(text, preferred_tone="Professional")
    rule_names = {w["rule_name"] for w in warnings}
    assert "Informal Slang in Professional Copy" in rule_names
    assert "Excessive Punctuation" in rule_names
