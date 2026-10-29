"""Unit tests for CampaignService and BrandProfile operations."""

import pytest
from backend.database import init_db
from backend.campaign_service import CampaignService


@pytest.fixture
def test_service(tmp_path):
    test_db = tmp_path / "campaign_svc_test.db"
    init_db(test_db)
    return CampaignService(test_db)


def test_create_and_get_campaign(test_service):
    data = {
        "name": "Q4 Enterprise Push",
        "product_name": "TaskFlow Pro",
        "product_description": "AI-assisted task management platform for agile teams.",
        "features": ["Automated backlog sorting", "Sprint burndown tracking"],
        "benefits": ["Saves 5 hours per sprint", "Reduces missed deadlines"],
        "target_audience": "Engineering managers and product leads",
        "audience_needs": "Need faster release coordination.",
        "objective": "conversions",
        "channel": "social media",
        "tone_of_voice": "Professional",
        "brand_name": "TaskFlow Inc",
    }
    campaign = test_service.create_campaign(data)
    assert campaign["id"].startswith("cmp-")
    assert campaign["name"] == "Q4 Enterprise Push"
    assert len(campaign["features"]) == 2

    # Fetch by ID
    fetched = test_service.get_campaign(campaign["id"])
    assert fetched["product_name"] == "TaskFlow Pro"


def test_create_campaign_missing_required_fields(test_service):
    with pytest.raises(ValueError):
        test_service.create_campaign({"name": "Incomplete"})


def test_duplicate_campaign(test_service):
    data = {
        "name": "Original Campaign",
        "product_name": "P1",
        "product_description": "Desc",
        "target_audience": "Audience",
        "objective": "leads",
        "channel": "email",
        "tone_of_voice": "Friendly",
    }
    orig = test_service.create_campaign(data)
    dup = test_service.duplicate_campaign(orig["id"])

    assert dup is not None
    assert dup["id"] != orig["id"]
    assert dup["name"] == "Copy of Original Campaign"
    assert dup["product_name"] == "P1"


def test_campaign_filtering_and_search(test_service):
    test_service.create_campaign({
        "name": "Search Campaign Alpha",
        "product_name": "Product A",
        "product_description": "Desc A",
        "target_audience": "Devs",
        "objective": "awareness",
        "channel": "search advertising",
        "tone_of_voice": "Professional",
    })
    test_service.create_campaign({
        "name": "Social Campaign Beta",
        "product_name": "Product B",
        "product_description": "Desc B",
        "target_audience": "Designers",
        "objective": "conversions",
        "channel": "social media",
        "tone_of_voice": "Playful",
    })

    # Search by text
    results = test_service.list_campaigns(search_query="Alpha")
    assert len(results) == 1
    assert results[0]["name"] == "Search Campaign Alpha"

    # Filter by objective
    results_conv = test_service.list_campaigns(objective="conversions")
    assert len(results_conv) == 1
    assert results_conv[0]["name"] == "Social Campaign Beta"


def test_dashboard_metrics(test_service):
    metrics = test_service.get_dashboard_metrics()
    assert metrics["total_campaigns"] == 0
    assert metrics["total_variants"] == 0

    test_service.create_campaign({
        "name": "Metric Test Campaign",
        "product_name": "Product M",
        "product_description": "Desc M",
        "target_audience": "Managers",
        "objective": "retention",
        "channel": "email",
        "tone_of_voice": "Conversational",
    })

    metrics_after = test_service.get_dashboard_metrics()
    assert metrics_after["total_campaigns"] == 1
    assert metrics_after["objective_distribution"].get("retention") == 1
