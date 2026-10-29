"""Advertising Variant and Copy Generation Engine.

Features:
- 11 Distinct Marketing Angles with Objective alignment
- 7 Channel-tailored Hook styles (Zero deceptive clickbait)
- 6 Objective-matched Call-To-Action (CTA) categories
- Channel-specific copy structures (Social, Search, Email, Display)
- Integrated brand and claim compliance warning scans
- Deterministic, grounded generation without hallucinated facts
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
import random
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import uuid

from backend.brand_checker import BrandChecker
from backend.claim_checker import ClaimChecker
from backend.database import get_connection, row_to_dict, rows_to_dicts

logger = logging.getLogger(__name__)

# =============================================================================
# MARKETING ANGLES DEFINITIONS & EXPLANATIONS
# =============================================================================

MARKETING_ANGLES = {
    "problem-and-solution": {
        "title": "Problem & Solution",
        "description": "Frames the customer's specific friction or bottleneck and introduces the product as the direct resolution.",
        "best_for": ["traffic", "conversions", "leads"],
    },
    "benefit-focused": {
        "title": "Benefit-Focused",
        "description": "Emphasizes the positive transformation and high-value customer outcome rather than technical specifications.",
        "best_for": ["awareness", "leads", "conversions"],
    },
    "product-feature": {
        "title": "Product Feature Deep-Dive",
        "description": "Spotlights a specific high-value functional capability and its everyday practical utility.",
        "best_for": ["awareness", "retention"],
    },
    "convenience": {
        "title": "Convenience & Simplicity",
        "description": "Focuses on time saved, ease of adoption, simplified workflows, and friction-free setup.",
        "best_for": ["traffic", "leads", "retention"],
    },
    "educational": {
        "title": "Educational & Informative",
        "description": "Shares actionable domain insights or best practices, positioning the brand as a credible advisor.",
        "best_for": ["awareness", "leads"],
    },
    "value-for-money": {
        "title": "Value for Money & ROI",
        "description": "Highlights cost efficiency, return on investment, and elimination of wasteful spending.",
        "best_for": ["conversions", "retention"],
    },
    "comparison": {
        "title": "Comparison & Superiority",
        "description": "Contrasts the offering against conventional alternatives (strictly requires verified factual backing).",
        "best_for": ["conversions", "traffic"],
    },
    "emotional-resonance": {
        "title": "Emotional Resonance & Peace of Mind",
        "description": "Connects with the emotional state of the user—reducing anxiety, stress, or self-doubt.",
        "best_for": ["awareness", "retention"],
    },
    "use-case": {
        "title": "Use-Case & Scenario",
        "description": "Depicts a relatable, concrete real-world situation where the product performs seamlessly.",
        "best_for": ["traffic", "leads", "retention"],
    },
    "differentiation": {
        "title": "Unique Differentiation",
        "description": "Details what sets the product distinctly apart from traditional category norms.",
        "best_for": ["awareness", "conversions"],
    },
    "offer-focused": {
        "title": "Direct Offer & Incentive",
        "description": "Leads with the active promotional terms, discount, trial incentive, or limited bonus.",
        "best_for": ["conversions", "leads"],
    },
}

# =============================================================================
# CALL TO ACTION (CTA) DEFINITIONS
# =============================================================================

CTA_CATEGORIES = {
    "action-oriented": [
        "Get Started Today", "Start Your Free Trial", "Claim Your Spot", "Take Action Now"
    ],
    "informational": [
        "Learn More", "Read the Guide", "See How It Works", "Explore the Details"
    ],
    "lead-generation": [
        "Request a Demo", "Download the Report", "Book a Free Consultation", "Get Your Custom Quote"
    ],
    "product-discovery": [
        "Explore Features", "Browse the Catalog", "Take the Virtual Tour", "View Specifications"
    ],
    "purchase-oriented": [
        "Order Now", "Claim Your Discount", "Purchase Today", "Shop the Collection"
    ],
    "contact-oriented": [
        "Speak with a Specialist", "Contact Our Team", "Talk to an Expert", "Chat with Us"
    ],
}


class AdVariantGenerator:
    """Generates distinct, channel-optimized advertising copy variants."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self.db_path = db_path

    @classmethod
    def get_supported_angles(cls) -> Dict[str, Dict[str, Any]]:
        """Return all supported marketing angles."""
        return MARKETING_ANGLES

    @classmethod
    def suggest_angles(
        cls, objective: str, has_offer: bool = False, has_evidence: bool = False
    ) -> List[str]:
        """Suggest suitable marketing angles based on campaign objective and evidence."""
        obj = objective.lower()
        candidates: List[str] = []

        for angle_key, meta in MARKETING_ANGLES.items():
            if angle_key == "comparison" and not has_evidence:
                continue
            if angle_key == "offer-focused" and not has_offer:
                continue
            if obj in meta["best_for"]:
                candidates.append(angle_key)

        # Fallback to general angles if empty
        if not candidates:
            candidates = ["benefit-focused", "problem-and-solution", "convenience"]

        return candidates

    @classmethod
    def generate_hook(
        cls,
        hook_type: str,
        prod_name: str,
        audience: str,
        problem: str,
        benefit: str,
        offer: str = "",
        channel: str = "social media",
    ) -> str:
        """Generate a focused, non-deceptive hook line."""
        clean_prob = problem.strip().rstrip(".")
        clean_ben = benefit.strip().rstrip(".")

        if hook_type == "question":
            if channel == "email":
                return f"Question for {audience}: Is {clean_prob.lower()} slowing you down?"
            return f"Tired of dealing with {clean_prob.lower()}?"

        elif hook_type == "problem":
            return f"When {clean_prob.lower()} gets in the way, productivity grinds to a halt."

        elif hook_type == "benefit":
            return f"Get {clean_ben.lower()} without the usual complexity."

        elif hook_type == "curiosity":
            return f"Here is why forward-thinking {audience} are rethinking how they handle {clean_prob.lower()}."

        elif hook_type == "educational":
            return f"A proven approach to {clean_ben.lower()} for modern {audience}."

        elif hook_type == "offer":
            if offer:
                return f"Special opportunity: {offer.strip()}."
            return f"Discover what makes {prod_name} the choice for {audience}."

        elif hook_type == "scenario":
            return f"Picture tackling your day with zero friction from {clean_prob.lower()}."

        return f"Discover how {prod_name} transforms {clean_ben.lower()}."

    @classmethod
    def select_cta(
        cls, objective: str, has_offer: bool = False, index: int = 0
    ) -> Tuple[str, str]:
        """Select an objective-aligned CTA and return (cta_text, cta_category)."""
        obj = objective.lower()
        if obj == "awareness":
            cat = "informational"
        elif obj == "traffic":
            cat = "product-discovery"
        elif obj == "leads":
            cat = "lead-generation"
        elif obj == "conversions":
            cat = "purchase-oriented" if has_offer else "action-oriented"
        elif obj == "retention":
            cat = "action-oriented"
        else:
            cat = "informational"

        options = CTA_CATEGORIES.get(cat, ["Learn More"])
        cta_text = options[index % len(options)]
        return cta_text, cat

    @classmethod
    def validate_cta_conflict(cls, cta: str, objective: str, has_offer: bool) -> Optional[str]:
        """Detect when a CTA conflicts with the marketing objective."""
        cta_lower = cta.lower()
        obj = objective.lower()

        is_purchase = any(w in cta_lower for w in ["buy", "order", "purchase", "shop", "pay"])
        if is_purchase and obj in ("awareness", "traffic") and not has_offer:
            return f"CTA '{cta}' is purchase-oriented, which conflicts with top-of-funnel '{objective}' objective without an active offer."

        return None

    @classmethod
    def construct_variant_copy(
        cls,
        channel: str,
        angle_key: str,
        hook: str,
        headline: str,
        prod_name: str,
        desc: str,
        features: List[str],
        benefits: List[str],
        audience: str,
        cta: str,
        offer: str = "",
        offer_conditions: str = "",
        disclaimers: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Construct channel-appropriate body copy and structured headline."""
        chan = channel.lower()
        feat_1 = features[0] if features else "Reliable core functionality"
        feat_2 = features[1] if len(features) > 1 else "Intuitive configuration"
        ben_1 = benefits[0] if benefits else "Improved operational efficiency"

        disclaimer_text = f"\n\n* {disclaimers[0]}" if disclaimers else ""

        if chan == "search advertising":
            # Search Ads require Headline 1 | Headline 2 and concise description
            formatted_headline = f"{prod_name} | {headline[:35]}"
            desc_1 = f"Designed for {audience}. {ben_1}."
            desc_2 = f"Key feature: {feat_1}. {offer.strip() if offer else ''} {cta}."
            body = f"{desc_1} {desc_2}{disclaimer_text}".strip()

        elif chan == "email":
            formatted_headline = f"Subject: {headline}"
            body_lines = [
                f"Preview: {hook}",
                "",
                f"Hello {audience},",
                "",
                f"{hook}",
                "",
                f"{prod_name} was developed to address this directly. {desc}",
                "",
                f"What this means for you:",
                f"• {ben_1}",
                f"• Powered by: {feat_1} and {feat_2}",
            ]
            if offer:
                body_lines.append(f"\nCurrent Offer: {offer}")
                if offer_conditions:
                    body_lines.append(f"Offer Terms: {offer_conditions}")

            body_lines.append(f"\n{cta}: Click below to proceed.")
            body_lines.append("\nBest regards,\nThe Product Team")
            if disclaimer_text:
                body_lines.append(disclaimer_text)
            body = "\n".join(body_lines)

        elif chan == "display advertising":
            formatted_headline = headline[:45]
            subhead = f"{ben_1[:55]} with {prod_name}."
            body = f"{subhead}\nAction: [{cta}]{disclaimer_text}"

        else:
            # Social Media (Default)
            formatted_headline = headline
            body_lines = [
                f"{hook}\n",
                f"{desc}\n",
                f"Why {audience} choose {prod_name}:",
                f"✔ {ben_1}",
                f"✔ {feat_1}",
                f"✔ {feat_2}",
            ]
            if offer:
                body_lines.append(f"\nSpecial Promotion: {offer}")
                if offer_conditions:
                    body_lines.append(f"({offer_conditions})")

            body_lines.append(f"\n👉 {cta}")
            if disclaimer_text:
                body_lines.append(disclaimer_text)

            body = "\n".join(body_lines)

        return formatted_headline, body

    def generate_variants_for_campaign(
        self,
        campaign_id: str,
        variant_count: int = 3,
        preferred_angles: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate a set of ad variants, run brand & claim checks, and persist to SQLite."""
        variant_count = max(1, min(10, variant_count))

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            camp_row = cursor.fetchone()
            if not camp_row:
                raise ValueError(f"Campaign '{campaign_id}' not found.")
            campaign = row_to_dict(camp_row)

            # Extract fields
            name = campaign["name"]
            prod_name = campaign["product_name"]
            desc = campaign["product_description"]
            features = campaign.get("features", [])
            benefits = campaign.get("benefits", [])
            audience = campaign["target_audience"]
            problem = campaign.get("audience_needs") or "manual inefficiencies"
            objective = campaign["objective"]
            channel = campaign["channel"]
            offer = campaign.get("offer", "")
            offer_conditions = campaign.get("offer_conditions", "")
            tone = campaign.get("tone_of_voice", "Professional")
            verified_facts = campaign.get("verified_facts", [])
            required_phrases = campaign.get("required_phrases", [])
            prohibited_phrases = campaign.get("prohibited_phrases", [])
            disclaimers = campaign.get("mandatory_disclaimers", [])

            # Determine angles
            has_evidence = len(verified_facts) > 0
            has_offer = bool(offer and offer.strip())

            available_angles = preferred_angles or self.suggest_angles(
                objective, has_offer=has_offer, has_evidence=has_evidence
            )
            if not available_angles:
                available_angles = ["benefit-focused", "problem-and-solution", "convenience"]

            hook_styles = ["problem", "question", "benefit", "curiosity", "educational", "offer", "scenario"]

            created_variants = []
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()

            with conn:
                for i in range(variant_count):
                    angle_key = available_angles[i % len(available_angles)]
                    angle_info = MARKETING_ANGLES.get(angle_key, MARKETING_ANGLES["benefit-focused"])
                    hook_style = hook_styles[i % len(hook_styles)]

                    var_id = f"var-{uuid.uuid4().hex[:8]}"
                    var_name = f"Variant {i + 1} - {angle_info['title']} ({channel.title()})"

                    # 1. Hook
                    hook = self.generate_hook(
                        hook_type=hook_style,
                        prod_name=prod_name,
                        audience=audience,
                        problem=problem,
                        benefit=benefits[0] if benefits else "Seamless Workflow",
                        offer=offer,
                        channel=channel,
                    )

                    # 2. Headline
                    benefit_str = benefits[i % len(benefits)] if benefits else "Streamlined Workflow"
                    headline = f"{prod_name}: {benefit_str}"

                    # 3. Call to Action
                    cta, _ = self.select_cta(objective, has_offer=has_offer, index=i)

                    # Check for CTA conflict warning
                    cta_conflict = self.validate_cta_conflict(cta, objective, has_offer)

                    # 4. Construct copy
                    formatted_headline, body_copy = self.construct_variant_copy(
                        channel=channel,
                        angle_key=angle_key,
                        hook=hook,
                        headline=headline,
                        prod_name=prod_name,
                        desc=desc,
                        features=features,
                        benefits=benefits,
                        audience=audience,
                        cta=cta,
                        offer=offer,
                        offer_conditions=offer_conditions,
                        disclaimers=disclaimers,
                    )

                    # 5. Run Brand and Claim Verification Scans
                    full_text = f"{formatted_headline}\n{hook}\n{body_copy}\n{cta}"

                    brand_warnings = BrandChecker.check_text(
                        full_text,
                        required_phrases=required_phrases,
                        prohibited_phrases=prohibited_phrases,
                        mandatory_disclaimers=disclaimers,
                        preferred_tone=tone,
                    )

                    claim_warnings = ClaimChecker.check_claims(
                        full_text,
                        verified_facts=verified_facts,
                        offer_conditions=offer_conditions,
                        has_offer=has_offer,
                    )

                    all_warnings = brand_warnings + claim_warnings
                    if cta_conflict:
                        all_warnings.append({
                            "category": "Call To Action",
                            "rule_name": "Objective Conflict",
                            "severity": "Medium",
                            "fragment": cta,
                            "explanation": cta_conflict,
                        })

                    # Identify supporting evidence needed
                    evidence_needed = [
                        w["evidence_required"] for w in claim_warnings if "evidence_required" in w
                    ]

                    # 6. Insert Variant into SQLite
                    conn.execute(
                        """
                        INSERT INTO ad_variants (
                            id, campaign_id, name, angle, hook, headline, body_copy,
                            cta, channel, target_audience, primary_message,
                            supporting_evidence_needed, warnings, review_status,
                            rejection_reason, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending Review', '', ?, ?)
                        """,
                        (
                            var_id,
                            campaign_id,
                            var_name,
                            angle_info["title"],
                            hook,
                            formatted_headline,
                            body_copy,
                            cta,
                            channel,
                            audience,
                            benefit_str,
                            json.dumps(evidence_needed),
                            json.dumps(all_warnings),
                            now,
                            now,
                        ),
                    )

                    # 7. Register Initial Audit History Record
                    conn.execute(
                        """
                        INSERT INTO review_history (
                            id, variant_id, action, previous_status, new_status,
                            reviewer_name, notes, created_at
                        ) VALUES (?, ?, 'Created', NULL, 'Pending Review', 'System Generator', 'Initial variant generation.', ?)
                        """,
                        (f"rev-{uuid.uuid4().hex[:8]}", var_id, now),
                    )

                    # 8. Register Claim Reviews
                    from backend.evidence_checker import EvidenceChecker
                    ev_service = EvidenceChecker(self.db_path)
                    ev_service.register_claim_warnings(campaign_id, var_id, claim_warnings, conn=conn)

                    created_variants.append(var_id)

            # Retrieve newly created variants after transaction commits
            results = [self.get_variant(vid) for vid in created_variants]
            logger.info("Successfully generated %d variants for campaign %s", len(results), campaign_id)
            return [v for v in results if v is not None]
        finally:
            conn.close()

    def get_variant(self, variant_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single variant by ID."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ad_variants WHERE id = ?", (variant_id,))
            return row_to_dict(cursor.fetchone())
        finally:
            conn.close()

    def list_variants_for_campaign(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Retrieve all variants associated with a campaign."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM ad_variants WHERE campaign_id = ? ORDER BY created_at ASC",
                (campaign_id,),
            )
            return rows_to_dicts(cursor.fetchall())
        finally:
            conn.close()

    def update_variant_content(
        self,
        variant_id: str,
        headline: str,
        hook: str,
        body_copy: str,
        cta: str,
    ) -> bool:
        """Update variant text, reset status to Pending Review, and recheck brand/claims."""
        variant = self.get_variant(variant_id)
        if not variant:
            return False

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = get_connection(self.db_path)

        try:
            # Fetch campaign rules for recheck
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaigns WHERE id = ?", (variant["campaign_id"],))
            campaign = row_to_dict(cursor.fetchone())

            full_text = f"{headline}\n{hook}\n{body_copy}\n{cta}"

            brand_warnings = BrandChecker.check_text(
                full_text,
                required_phrases=campaign.get("required_phrases"),
                prohibited_phrases=campaign.get("prohibited_phrases"),
                mandatory_disclaimers=campaign.get("mandatory_disclaimers"),
                preferred_tone=campaign.get("tone_of_voice"),
            )

            claim_warnings = ClaimChecker.check_claims(
                full_text,
                verified_facts=campaign.get("verified_facts"),
                offer_conditions=campaign.get("offer_conditions"),
                has_offer=bool(campaign.get("offer")),
            )

            all_warnings = brand_warnings + claim_warnings
            evidence_needed = [
                w["evidence_required"] for w in claim_warnings if "evidence_required" in w
            ]

            with conn:
                conn.execute(
                    """
                    UPDATE ad_variants
                    SET headline = ?,
                        hook = ?,
                        body_copy = ?,
                        cta = ?,
                        warnings = ?,
                        supporting_evidence_needed = ?,
                        review_status = 'Pending Review',
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        headline.strip(),
                        hook.strip(),
                        body_copy.strip(),
                        cta.strip(),
                        json.dumps(all_warnings),
                        json.dumps(evidence_needed),
                        now,
                        variant_id,
                    ),
                )

                # Record history entry
                conn.execute(
                    """
                    INSERT INTO review_history (
                        id, variant_id, action, previous_status, new_status,
                        reviewer_name, notes, created_at
                    ) VALUES (?, ?, 'Edited', ?, 'Pending Review', 'Human Editor', 'Copy updated; reset to Pending Review.', ?)
                    """,
                    (
                        f"rev-{uuid.uuid4().hex[:8]}",
                        variant_id,
                        variant["review_status"],
                        now,
                    ),
                )
            return True
        finally:
            conn.close()

    def regenerate_single_variant(self, variant_id: str) -> Optional[Dict[str, Any]]:
        """Regenerate a single variant while keeping its place in the campaign."""
        old_var = self.get_variant(variant_id)
        if not old_var:
            return None

        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute("DELETE FROM ad_variants WHERE id = ?", (variant_id,))
            new_variants = self.generate_variants_for_campaign(
                old_var["campaign_id"], variant_count=1
            )
            return new_variants[0] if new_variants else None
        finally:
            conn.close()
