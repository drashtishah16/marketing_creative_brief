"""Creative Brief generation engine.

Synthesizes campaign inputs into structured, professional creative briefs.
Maintains clear boundaries between verified input facts and generated suggestions.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from backend.database import get_connection, row_to_dict

logger = logging.getLogger(__name__)


class CreativeBriefGenerator:
    """Generates and manages structured marketing creative briefs."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self.db_path = db_path

    @classmethod
    def synthesize_brief(cls, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured creative brief fields deterministically from campaign inputs."""
        name = campaign.get("name", "Untitled Campaign")
        prod_name = campaign.get("product_name", "Product")
        desc = campaign.get("product_description", "")
        features = campaign.get("features", [])
        benefits = campaign.get("benefits", [])
        audience = campaign.get("target_audience", "Target Market")
        needs = campaign.get("audience_needs", "")
        objective = campaign.get("objective", "awareness").lower()
        channel = campaign.get("channel", "social media").lower()
        tone = campaign.get("tone_of_voice", "Professional")
        offer = campaign.get("offer", "")
        offer_conditions = campaign.get("offer_conditions", "")
        brand_name = campaign.get("brand_name") or prod_name
        verified_facts = campaign.get("verified_facts", [])
        claims_needing_evidence = campaign.get("claims_requiring_evidence", [])
        required_phrases = campaign.get("required_phrases", [])
        prohibited_phrases = campaign.get("prohibited_phrases", [])
        disclaimers = campaign.get("mandatory_disclaimers", [])

        # 1. Overview
        overview = (
            f"Campaign '{name}' targets {audience} via {channel.title()}. "
            f"The initiative focuses on driving {objective.title()} for {brand_name}'s {prod_name} "
            f"using a {tone.lower()} brand voice."
        )

        # 2. Product Summary
        feat_summary = f" Key capabilities include: {', '.join(features[:3])}." if features else ""
        prod_summary = f"{prod_name} is described as: {desc}.{feat_summary}"

        # 3. Objective & Desired Response
        response_map = {
            "awareness": f"Recognize {prod_name} as an emerging, reliable solution and recall its primary value.",
            "traffic": f"Click through to destination pages to explore features, specifications, and use cases.",
            "leads": f"Submit contact information or request a personalized demonstration/consultation.",
            "conversions": f"Complete trial sign-up, place an order, or subscribe with clear awareness of conditions.",
            "retention": f"Re-engage with high-value features, discover advanced capabilities, and renew participation.",
        }
        desired_response = response_map.get(
            objective,
            f"Engage positively with {prod_name} and explore next steps."
        )

        # 4. Audience Problem / Need
        aud_problem = (
            needs if needs.strip()
            else f"{audience} faces operational friction, time constraints, or unmet requirements addressed by {prod_name}."
        )

        # 5. Customer Insight [SUGGESTED INSIGHT]
        customer_insight = (
            f"[SUGGESTED INSIGHT] {audience} seeks dependable, low-friction solutions that deliver "
            f"measurable relief without requiring disruptive workflow changes or risky commitments."
        )

        # 6. Value Proposition
        primary_benefit = benefits[0] if benefits else "streamlined efficiency and improved outcomes"
        value_prop = (
            f"{prod_name} empowers {audience} to achieve {primary_benefit} "
            f"through {features[0] if features else 'targeted innovation'}."
        )

        # 7. Primary Message
        primary_msg = (
            f"Experience {primary_benefit.lower()} with {prod_name}—designed specifically for {audience}."
        )

        # 8. Communication Angle
        angle_map = {
            "awareness": "Educational / Problem-Solution Angle (Introduce category context and define need)",
            "traffic": "Curiosity & Problem-Solution Angle (Highlight friction and present the alternative)",
            "leads": "Benefit-Focused & Convenience Angle (Showcase tangible daily advantages with free consultation)",
            "conversions": "Value-for-Money & Offer-Focused Angle (Demonstrate clear ROI paired with incentive)",
            "retention": "Product-Feature & Use-Case Angle (Reinforce value and celebrate ongoing mastery)",
        }
        comm_angle = angle_map.get(objective, "Benefit-Focused Angle")

        # 9. Message Hierarchy
        msg_hierarchy = (
            "1. Hook / Headline: Lead with the audience's primary pain point or compelling core benefit.\n"
            "2. Body Proof: Anchor message with verified product features without ungrounded hype.\n"
            "3. Offer & Action: Present the specific offer terms and direct the user to a frictionless call to action."
        )

        # 10. Recommended CTA
        cta_map = {
            "awareness": "Learn More About " + prod_name,
            "traffic": "Explore " + prod_name + " Today",
            "leads": "Request a Free Demo",
            "conversions": "Start Your Trial Now" if not offer else "Claim This Offer",
            "retention": "Discover What's New",
        }
        recommended_cta = cta_map.get(objective, "Get Started")

        # 11. Missing Evidence & Risk Review Checklist
        missing_evidence: List[str] = []
        if claims_needing_evidence:
            missing_evidence.extend(claims_needing_evidence)
        if offer and not offer_conditions:
            missing_evidence.append("Promotional terms, eligibility rules, and expiry schedule for the offer.")

        potential_risks = [
            "Ensure no unsubstantiated performance claims (e.g. percentages, multiplier metrics) are published without proof.",
            "Verify all price and discount representations match live landing page terms exactly.",
            "Do not state or imply competitor inferiority without independent empirical verification.",
        ]
        if disclaimers:
            potential_risks.append(f"Ensure mandatory disclaimer is visible on the final asset: '{disclaimers[0]}'")

        brand_restrictions = []
        if prohibited_phrases:
            brand_restrictions.append(f"Prohibited terms: {', '.join(prohibited_phrases)}")
        if required_phrases:
            brand_restrictions.append(f"Required phrases: {', '.join(required_phrases)}")
        if disclaimers:
            brand_restrictions.append(f"Mandatory disclaimers: {', '.join(disclaimers)}")

        return {
            "overview": overview,
            "product_summary": prod_summary,
            "objective": objective.title(),
            "target_audience": audience,
            "audience_problem": aud_problem,
            "customer_insight": customer_insight,
            "value_proposition": value_prop,
            "primary_message": primary_msg,
            "communication_angle": comm_angle,
            "recommended_tone": tone,
            "desired_response": desired_response,
            "message_hierarchy": msg_hierarchy,
            "recommended_cta": recommended_cta,
            "verified_facts": verified_facts,
            "missing_evidence": missing_evidence,
            "brand_restrictions": brand_restrictions,
            "potential_risks": potential_risks,
        }

    def generate_and_save_brief(self, campaign_id: str) -> Dict[str, Any]:
        """Generate brief from campaign data and persist or update in SQLite."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            camp_row = cursor.fetchone()
            if not camp_row:
                raise ValueError(f"Campaign '{campaign_id}' not found.")
            campaign = row_to_dict(camp_row)

            brief_data = self.synthesize_brief(campaign)
            brief_id = f"brf-{uuid.uuid4().hex[:8]}"
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()

            with conn:
                # Upsert brief for campaign
                conn.execute(
                    """
                    INSERT INTO creative_briefs (
                        id, campaign_id, overview, product_summary, objective,
                        target_audience, audience_problem, customer_insight,
                        value_proposition, primary_message, communication_angle,
                        recommended_tone, desired_response, message_hierarchy,
                        recommended_cta, verified_facts, missing_evidence,
                        brand_restrictions, potential_risks, status,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Needs Review', ?, ?)
                    ON CONFLICT(campaign_id) DO UPDATE SET
                        overview = excluded.overview,
                        product_summary = excluded.product_summary,
                        objective = excluded.objective,
                        target_audience = excluded.target_audience,
                        audience_problem = excluded.audience_problem,
                        customer_insight = excluded.customer_insight,
                        value_proposition = excluded.value_proposition,
                        primary_message = excluded.primary_message,
                        communication_angle = excluded.communication_angle,
                        recommended_tone = excluded.recommended_tone,
                        desired_response = excluded.desired_response,
                        message_hierarchy = excluded.message_hierarchy,
                        recommended_cta = excluded.recommended_cta,
                        verified_facts = excluded.verified_facts,
                        missing_evidence = excluded.missing_evidence,
                        brand_restrictions = excluded.brand_restrictions,
                        potential_risks = excluded.potential_risks,
                        status = 'Needs Review',
                        updated_at = excluded.updated_at
                    """,
                    (
                        brief_id,
                        campaign_id,
                        brief_data["overview"],
                        brief_data["product_summary"],
                        brief_data["objective"],
                        brief_data["target_audience"],
                        brief_data["audience_problem"],
                        brief_data["customer_insight"],
                        brief_data["value_proposition"],
                        brief_data["primary_message"],
                        brief_data["communication_angle"],
                        brief_data["recommended_tone"],
                        brief_data["desired_response"],
                        brief_data["message_hierarchy"],
                        brief_data["recommended_cta"],
                        json.dumps(brief_data["verified_facts"]),
                        json.dumps(brief_data["missing_evidence"]),
                        json.dumps(brief_data["brand_restrictions"]),
                        json.dumps(brief_data["potential_risks"]),
                        now,
                        now,
                    ),
                )
            return self.get_brief_for_campaign(campaign_id) or {}
        finally:
            conn.close()

    def get_brief_for_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve existing creative brief for a campaign."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM creative_briefs WHERE campaign_id = ?", (campaign_id,))
            return row_to_dict(cursor.fetchone())
        finally:
            conn.close()

    def update_brief_content(self, brief_id: str, updates: Dict[str, Any]) -> bool:
        """Allow user to manually edit brief sections."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = get_connection(self.db_path)

        allowed_fields = [
            "overview", "product_summary", "audience_problem", "customer_insight",
            "value_proposition", "primary_message", "communication_angle",
            "recommended_tone", "desired_response", "message_hierarchy",
            "recommended_cta", "status"
        ]

        set_clauses = ["updated_at = ?"]
        params: List[Any] = [now]

        for k in allowed_fields:
            if k in updates:
                set_clauses.append(f"{k} = ?")
                params.append(str(updates[k]))

        params.append(brief_id)
        sql = f"UPDATE creative_briefs SET {', '.join(set_clauses)} WHERE id = ?"

        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                return cursor.rowcount > 0
        finally:
            conn.close()
