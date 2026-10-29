"""Sample data seeder for realistic demonstration campaigns and brand profiles."""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from typing import Optional

# Ensure marketing_creative_generator is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.ad_variant_generator import AdVariantGenerator
from backend.brief_generator import CreativeBriefGenerator
from backend.campaign_service import CampaignService
from backend.database import init_db

logger = logging.getLogger(__name__)


def seed_sample_data(db_path: Optional[str | Path] = None, force: bool = False) -> None:
    """Pre-populate the database with realistic demonstration campaigns, briefs, and variants."""
    init_db(db_path)
    camp_svc = CampaignService(db_path)
    brief_svc = CreativeBriefGenerator(db_path)
    var_svc = AdVariantGenerator(db_path)

    # Check if already seeded
    existing = camp_svc.list_campaigns()
    if existing and not force:
        logger.info("Database already contains %d campaigns; skipping sample seed.", len(existing))
        return

    logger.info("Seeding realistic sample marketing campaigns...")

    # 1. Brand Profiles
    bp_tech = camp_svc.create_brand_profile(
        name="Apex Enterprise Brand Guide",
        brand_name="Apex Systems",
        tone_of_voice="Professional",
        preferred_terms=["engineers", "enterprises", "reliability"],
        prohibited_terms=["bug-free", "cheapest", "foolproof"],
        required_phrases=["Built for Enterprise Reliability"],
        mandatory_disclaimers=["Requires active enterprise license. Terms and conditions apply."],
    )

    bp_eco = camp_svc.create_brand_profile(
        name="PureHydro Eco Guidelines",
        brand_name="PureHydro",
        tone_of_voice="Friendly",
        preferred_terms=["sustainable", "clean hydration", "reusable"],
        prohibited_terms=["miracle bottle", "dirt cheap", "unbreakable"],
        required_phrases=["Engineered for the Planet"],
        mandatory_disclaimers=["Free shipping applies to standard domestic orders only."],
    )

    # 2. Campaign 1: B2B SaaS Workflow Tool (FlowSync)
    c1 = camp_svc.create_campaign({
        "name": "FlowSync Q4 Enterprise Sprint",
        "product_name": "FlowSync Enterprise",
        "product_description": "Continuous code integration and branch synchronization platform for distributed engineering teams.",
        "features": [
            "Automated background merge resolution",
            "Real-time CI pipeline status triggers",
            "SOC 2 Type II audit logging & SSO"
        ],
        "benefits": [
            "Save 5 hours per developer weekly",
            "Eliminate broken staging deployments",
            "Accelerate sprint velocity with confidence"
        ],
        "target_audience": "VP of Engineering and Lead DevOps Architects",
        "audience_needs": "Frequent merge bottlenecks and long deployment queues stalling release cycles.",
        "objective": "leads",
        "channel": "search advertising",
        "tone_of_voice": "Professional",
        "brand_name": "FlowSync",
        "brand_profile_id": bp_tech["id"],
        "offer": "Custom Architecture Review & 30-Day Guided Pilot",
        "offer_conditions": "Available to qualified engineering teams of 20+ developers.",
        "verified_facts": [
            "SOC 2 Type II certified infrastructure",
            "Native integration with GitHub Enterprise, GitLab, and Bitbucket"
        ],
        "claims_requiring_evidence": [
            "Independent benchmark validating 5 hours weekly developer time savings"
        ],
        "required_phrases": ["Built for Enterprise Reliability"],
        "prohibited_phrases": ["cheapest", "bug-free"],
        "mandatory_disclaimers": ["Requires active enterprise license. Terms and conditions apply."],
    })
    brief_svc.generate_and_save_brief(c1["id"])
    var_svc.generate_variants_for_campaign(c1["id"], variant_count=3)

    # 3. Campaign 2: PureHydro EcoFlask (Consumer Lifestyle)
    c2 = camp_svc.create_campaign({
        "name": "PureHydro Summer Hydration",
        "product_name": "PureHydro Titanium Flask",
        "product_description": "Triple-walled vacuum insulated water bottle made from recycled aerospace-grade titanium.",
        "features": [
            "36-hour ice retention vacuum insulation",
            "Leak-proof magnetic cap mechanism",
            "100% BPA and microplastic free"
        ],
        "benefits": [
            "Keep hydration refreshing anywhere all day",
            "Eliminate hundreds of single-use plastic bottles",
            "Durable ultralight carry for active commuters"
        ],
        "target_audience": "Eco-conscious active professionals and daily commuters",
        "audience_needs": "Frustrated with leaking bottles, lukewarm water, and synthetic plastics.",
        "objective": "conversions",
        "channel": "social media",
        "tone_of_voice": "Friendly",
        "brand_name": "PureHydro",
        "brand_profile_id": bp_eco["id"],
        "offer": "20% off your first bottle + Free carbon-neutral shipping",
        "offer_conditions": "Use code HYDRATE20 at checkout. Minimum order $35. Offer ends Sunday.",
        "verified_facts": [
            "Certified 100% BPA and phthalate-free by SGS Laboratories",
            "Certified Carbon Neutral by Climate Impact Partners"
        ],
        "claims_requiring_evidence": [
            "Thermal insulation lab testing graph showing 36-hour ice retention"
        ],
        "required_phrases": ["Engineered for the Planet"],
        "prohibited_phrases": ["dirt cheap", "miracle bottle"],
        "mandatory_disclaimers": ["Free shipping applies to standard domestic orders only."],
    })
    brief_svc.generate_and_save_brief(c2["id"])
    var_svc.generate_variants_for_campaign(c2["id"], variant_count=3)

    # 4. Campaign 3: PulsePeak Health Coach (Digital Health)
    c3 = camp_svc.create_campaign({
        "name": "PulsePeak Recovery Awareness",
        "product_name": "PulsePeak Coach",
        "product_description": "Personalized athletic recovery and HRV monitoring mobile app with registered sports nutritionist guidance.",
        "features": [
            "Continuous HRV recovery scoring",
            "Personalized daily readiness recommendations",
            "Direct chat with certified sports dietitians"
        ],
        "benefits": [
            "Train smarter without overtraining burnout",
            "Build sustainable energy and sleep habits",
            "Access personalized nutritional coaching on-demand"
        ],
        "target_audience": "Marathon runners, CrossFit athletes, and endurance hobbyists",
        "audience_needs": "Chronic fatigue, plateauing performance, and confusion over nutrition.",
        "objective": "awareness",
        "channel": "email",
        "tone_of_voice": "Educational",
        "brand_name": "PulsePeak Health",
        "offer": "7-day unrestricted trial access",
        "offer_conditions": "Valid for new accounts. Cancel anytime.",
        "verified_facts": [
            "Over 45,000 registered active athletes in 2026",
            "Syncs natively with Apple Health, Garmin, and WHOOP"
        ],
        "claims_requiring_evidence": [
            "Peer-reviewed study citations on HRV-guided training periodization"
        ],
        "required_phrases": ["Evidence-Based Health"],
        "prohibited_phrases": ["cure injury", "instant fat loss"],
        "mandatory_disclaimers": ["Not intended as medical advice. Always consult a physician."],
    })
    brief_svc.generate_and_save_brief(c3["id"])
    var_svc.generate_variants_for_campaign(c3["id"], variant_count=3)

    logger.info("Successfully seeded 3 realistic sample campaigns.")


if __name__ == "__main__":
    seed_sample_data()
