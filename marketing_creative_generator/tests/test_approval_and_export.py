"""Unit tests for ApprovalService and ExportService."""

import pytest
from backend.database import init_db
from backend.campaign_service import CampaignService
from backend.ad_variant_generator import AdVariantGenerator
from backend.approval_service import ApprovalService
from backend.evidence_checker import EvidenceChecker
from backend.export_service import ExportService


@pytest.fixture
def test_env(tmp_path):
    test_db = tmp_path / "appr_export_test.db"
    init_db(test_db)
    camp_svc = CampaignService(test_db)
    var_svc = AdVariantGenerator(test_db)
    appr_svc = ApprovalService(test_db)
    ev_svc = EvidenceChecker(test_db)
    export_svc = ExportService(test_db)
    return camp_svc, var_svc, appr_svc, ev_svc, export_svc


def test_approve_variant_clean_history(test_env):
    camp_svc, var_svc, appr_svc, ev_svc, export_svc = test_env

    camp = camp_svc.create_campaign({
        "name": "Clean Campaign",
        "product_name": "Product Clean",
        "product_description": "Clean description.",
        "target_audience": "Audience",
        "objective": "awareness",
        "channel": "social media",
        "tone_of_voice": "Friendly",
    })
    variants = var_svc.generate_variants_for_campaign(camp["id"], variant_count=1)
    v_id = variants[0]["id"]

    # Approve
    approved = appr_svc.approve_variant(v_id, reviewer_name="Alice Senior Reviewer")
    assert approved["review_status"] == "Approved"

    # Check history
    history = appr_svc.get_review_history(v_id)
    assert any(h["action"] == "Approved" and h["reviewer_name"] == "Alice Senior Reviewer" for h in history)


def test_rejection_workflow(test_env):
    camp_svc, var_svc, appr_svc, ev_svc, export_svc = test_env

    camp = camp_svc.create_campaign({
        "name": "Reject Campaign",
        "product_name": "Product R",
        "product_description": "Description",
        "target_audience": "Audience",
        "objective": "traffic",
        "channel": "social media",
        "tone_of_voice": "Friendly",
    })
    variants = var_svc.generate_variants_for_campaign(camp["id"], variant_count=1)
    v_id = variants[0]["id"]

    rejected = appr_svc.reject_variant(v_id, rejection_reason="Tone is too casual for enterprise target.", reviewer_name="Bob Lead")
    assert rejected["review_status"] == "Rejected"
    assert rejected["rejection_reason"] == "Tone is too casual for enterprise target."


def test_approval_blocked_by_unresolved_high_severity(test_env):
    camp_svc, var_svc, appr_svc, ev_svc, export_svc = test_env

    camp = camp_svc.create_campaign({
        "name": "Risky Campaign",
        "product_name": "Product Risk",
        "product_description": "Risk description.",
        "target_audience": "Audience",
        "objective": "conversions",
        "channel": "social media",
        "tone_of_voice": "Professional",
    })
    variants = var_svc.generate_variants_for_campaign(camp["id"], variant_count=1)
    v_id = variants[0]["id"]

    # Manually register an unresolved High-severity warning
    ev_svc.register_claim_warnings(camp["id"], v_id, [
        {
            "category": "Claim Verification",
            "rule_name": "Sensitive Medical/Health Claim",
            "severity": "High",
            "fragment": "Cures all back pain instantly",
            "explanation": "Unsubstantiated clinical claim",
            "evidence_required": "Peer reviewed clinical study",
            "is_corroborated": False,
        }
    ])

    # Trying to approve without override MUST fail
    with pytest.raises(PermissionError):
        appr_svc.approve_variant(v_id, reviewer_name="Charlie Reviewer")

    # Trying to approve with explicit override justification SUCCEEDS
    overridden = appr_svc.approve_variant(
        v_id,
        reviewer_name="Charlie Compliance Officer",
        override_reason="Exemption approved by Chief Medical Counsel under filing #8839.",
    )
    assert overridden["review_status"] == "Approved"


def test_export_service_csv_and_markdown(test_env):
    camp_svc, var_svc, appr_svc, ev_svc, export_svc = test_env

    camp = camp_svc.create_campaign({
        "name": "Export Campaign",
        "product_name": "ExportTool",
        "product_description": "Export description.",
        "target_audience": "Marketers",
        "objective": "leads",
        "channel": "social media",
        "tone_of_voice": "Professional",
    })
    var_svc.generate_variants_for_campaign(camp["id"], variant_count=2)

    csv_data = export_svc.export_variants_to_csv(camp["id"])
    assert "Variant ID" in csv_data
    assert "ExportTool" in csv_data
    assert "Call To Action" in csv_data

    md_brief = export_svc.export_brief_to_markdown(camp["id"])
    assert "# CREATIVE BRIEF: Export Campaign" in md_brief
    assert "## 1. CAMPAIGN OVERVIEW" in md_brief

    backup = export_svc.export_campaign_full_backup(camp["id"])
    assert backup["campaign"]["name"] == "Export Campaign"
    assert len(backup["ad_variants"]) == 2
