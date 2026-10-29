"""Unit tests for AdVariantGenerator."""

import pytest
from backend.database import init_db
from backend.campaign_service import CampaignService
from backend.ad_variant_generator import AdVariantGenerator


@pytest.fixture
def variant_svc_fixture(tmp_path):
    test_db = tmp_path / "variant_test.db"
    init_db(test_db)
    camp_svc = CampaignService(test_db)
    var_svc = AdVariantGenerator(test_db)
    return camp_svc, var_svc


def test_ad_variant_generation_count_and_fields(variant_svc_fixture):
    camp_svc, var_svc = variant_svc_fixture

    camp = camp_svc.create_campaign({
        "name": "DevFlow Launch",
        "product_name": "DevFlow IDE",
        "product_description": "Next-gen editor for microservice development.",
        "features": ["Instant container spin-up", "Automated mock servers"],
        "benefits": ["Build APIs 3x faster", "Cut local setup friction"],
        "target_audience": "Full-stack software engineers",
        "audience_needs": "Tired of broken Docker environments.",
        "objective": "conversions",
        "channel": "social media",
        "tone_of_voice": "Conversational",
        "offer": "Free 14-day trial",
        "offer_conditions": "No credit card required. Cancel anytime.",
    })

    variants = var_svc.generate_variants_for_campaign(camp["id"], variant_count=3)
    assert len(variants) == 3

    for v in variants:
        assert v["campaign_id"] == camp["id"]
        assert v["name"].startswith("Variant ")
        assert len(v["hook"]) > 0
        assert len(v["headline"]) > 0
        assert len(v["body_copy"]) > 0
        assert len(v["cta"]) > 0
        assert v["review_status"] == "Pending Review"


def test_channel_specific_copy_formatting(variant_svc_fixture):
    camp_svc, var_svc = variant_svc_fixture

    # Test Email channel formatting
    camp_email = camp_svc.create_campaign({
        "name": "Email Campaign",
        "product_name": "InboxHero",
        "product_description": "Email triage tool.",
        "features": ["Smart priority inbox"],
        "benefits": ["Reach inbox zero effortlessly"],
        "target_audience": "Executives",
        "objective": "leads",
        "channel": "email",
        "tone_of_voice": "Professional",
    })
    variants = var_svc.generate_variants_for_campaign(camp_email["id"], variant_count=1)
    v = variants[0]
    assert "Subject:" in v["headline"]
    assert "Preview:" in v["body_copy"]
    assert "Hello Executives" in v["body_copy"]


def test_cta_objective_conflict_detection():
    # Purchase-oriented CTA with awareness objective should trigger warning
    conflict = AdVariantGenerator.validate_cta_conflict(
        cta="Order Now for $499",
        objective="awareness",
        has_offer=False,
    )
    assert conflict is not None
    assert "purchase-oriented" in conflict


def test_variant_edit_and_reset_to_pending(variant_svc_fixture):
    camp_svc, var_svc = variant_svc_fixture

    camp = camp_svc.create_campaign({
        "name": "Edit Test",
        "product_name": "App",
        "product_description": "Desc",
        "target_audience": "Users",
        "objective": "traffic",
        "channel": "social media",
        "tone_of_voice": "Friendly",
    })
    variants = var_svc.generate_variants_for_campaign(camp["id"], variant_count=1)
    v_id = variants[0]["id"]

    # Manually update
    var_svc.update_variant_content(
        variant_id=v_id,
        headline="New Headline",
        hook="New Hook",
        body_copy="New Body Copy",
        cta="Learn More",
    )

    updated = var_svc.get_variant(v_id)
    assert updated["headline"] == "New Headline"
    assert updated["review_status"] == "Pending Review"
