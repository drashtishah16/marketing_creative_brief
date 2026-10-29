"""Unit tests for CreativeBriefGenerator."""

import pytest
from backend.database import init_db
from backend.campaign_service import CampaignService
from backend.brief_generator import CreativeBriefGenerator


@pytest.fixture
def brief_service_fixture(tmp_path):
    test_db = tmp_path / "brief_test.db"
    init_db(test_db)
    camp_svc = CampaignService(test_db)
    brief_svc = CreativeBriefGenerator(test_db)
    return camp_svc, brief_svc


def test_brief_generation_structure(brief_service_fixture):
    camp_svc, brief_svc = brief_service_fixture

    camp = camp_svc.create_campaign({
        "name": "CloudSync Launch",
        "product_name": "CloudSync Pro",
        "product_description": "Encrypted real-time file synchronization for remote legal teams.",
        "features": ["Zero-knowledge encryption", "Instant delta syncing"],
        "benefits": ["Protect client confidentiality", "Save hours on document sharing"],
        "target_audience": "Boutique law firms and legal compliance officers",
        "audience_needs": "Need secure remote document access without cloud data leakage.",
        "objective": "leads",
        "channel": "search advertising",
        "tone_of_voice": "Professional",
        "brand_name": "CloudSync",
        "verified_facts": ["SOC 2 Type II certified infrastructure", "256-bit AES encryption"],
        "claims_requiring_evidence": ["Zero-knowledge audit report"],
        "mandatory_disclaimers": ["Subject to local regulatory jurisdiction."],
    })

    brief = brief_svc.generate_and_save_brief(camp["id"])

    assert brief["campaign_id"] == camp["id"]
    assert "CloudSync Launch" in brief["overview"]
    assert "Protect client confidentiality" in brief["value_proposition"]
    assert "[SUGGESTED INSIGHT]" in brief["customer_insight"]
    assert len(brief["verified_facts"]) == 2
    assert len(brief["missing_evidence"]) == 1
    assert brief["status"] == "Needs Review"


def test_brief_manual_edit(brief_service_fixture):
    camp_svc, brief_svc = brief_service_fixture

    camp = camp_svc.create_campaign({
        "name": "Test Campaign",
        "product_name": "Product X",
        "product_description": "Description",
        "target_audience": "Developers",
        "objective": "awareness",
        "channel": "social media",
        "tone_of_voice": "Friendly",
    })

    brief = brief_svc.generate_and_save_brief(camp["id"])
    success = brief_svc.update_brief_content(
        brief["id"],
        {"value_proposition": "Custom refined value proposition.", "status": "Reviewed"}
    )
    assert success is True

    updated_brief = brief_svc.get_brief_for_campaign(camp["id"])
    assert updated_brief["value_proposition"] == "Custom refined value proposition."
    assert updated_brief["status"] == "Reviewed"
