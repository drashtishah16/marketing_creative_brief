"""Export and reporting service.

Generates CSV tables, Markdown brief documents, and JSON campaign backups.
"""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from backend.ad_variant_generator import AdVariantGenerator
from backend.brief_generator import CreativeBriefGenerator
from backend.campaign_service import CampaignService

logger = logging.getLogger(__name__)


class ExportService:
    """Handles serialization and formatting for creative briefs, ad variants, and campaign backups."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self.db_path = db_path
        self.campaign_svc = CampaignService(db_path)
        self.brief_svc = CreativeBriefGenerator(db_path)
        self.variant_svc = AdVariantGenerator(db_path)

    def export_variants_to_csv(self, campaign_id: str) -> str:
        """Export all ad variants for a campaign into standardized CSV format."""
        variants = self.variant_svc.list_variants_for_campaign(campaign_id)
        if not variants:
            # Return empty CSV with standard schema headers
            cols = [
                "Variant ID", "Variant Name", "Channel", "Angle", "Hook",
                "Headline", "Body Copy", "Call To Action", "Status",
                "Warnings Summary", "Created At"
            ]
            return pd.DataFrame(columns=cols).to_csv(index=False)

        rows = []
        for v in variants:
            raw_warnings = v.get("warnings") or []
            if isinstance(raw_warnings, str):
                try:
                    raw_warnings = json.loads(raw_warnings)
                except Exception:
                    raw_warnings = []

            warning_descs = [
                f"[{w.get('severity', 'Info')}] {w.get('rule_name')}: {w.get('explanation')}"
                for w in raw_warnings
            ]
            warn_str = " | ".join(warning_descs) if warning_descs else "None"

            rows.append({
                "Variant ID": v.get("id"),
                "Variant Name": v.get("name"),
                "Channel": v.get("channel", "").title(),
                "Angle": v.get("angle"),
                "Hook": v.get("hook"),
                "Headline": v.get("headline"),
                "Body Copy": v.get("body_copy"),
                "Call To Action": v.get("cta"),
                "Status": v.get("review_status"),
                "Warnings Summary": warn_str,
                "Created At": v.get("created_at"),
            })

        df = pd.DataFrame(rows)
        return df.to_csv(index=False)

    def export_brief_to_markdown(self, campaign_id: str) -> str:
        """Render creative brief as a formatted Markdown publication document."""
        campaign = self.campaign_svc.get_campaign(campaign_id)
        if not campaign:
            return "# Error\n\nCampaign not found."

        brief = self.brief_svc.get_brief_for_campaign(campaign_id)
        if not brief:
            brief = self.brief_svc.generate_and_save_brief(campaign_id)

        verified_facts = brief.get("verified_facts") or []
        missing_evidence = brief.get("missing_evidence") or []
        brand_restrictions = brief.get("brand_restrictions") or []
        risks = brief.get("potential_risks") or []

        md_lines = [
            f"# CREATIVE BRIEF: {campaign.get('name')}",
            f"**Brand / Product:** {campaign.get('brand_name') or campaign.get('product_name')} | **Date:** {brief.get('updated_at', '')[:10]}",
            f"**Review Status:** `{brief.get('status', 'Needs Review')}`",
            "",
            "---",
            "",
            "## 1. CAMPAIGN OVERVIEW",
            f"{brief.get('overview', '')}",
            "",
            "## 2. PRODUCT & SERVICE SUMMARY",
            f"{brief.get('product_summary', '')}",
            "",
            "## 3. OBJECTIVE & DESIRED RESPONSE",
            f"- **Objective:** {brief.get('objective', '')}",
            f"- **Target Audience:** {brief.get('target_audience', '')}",
            f"- **Desired Audience Response:** {brief.get('desired_response', '')}",
            "",
            "## 4. AUDIENCE PROBLEM & CUSTOMER INSIGHT",
            f"- **Audience Need / Friction:** {brief.get('audience_problem', '')}",
            f"- **Customer Insight:** {brief.get('customer_insight', '')}",
            "",
            "## 5. VALUE PROPOSITION & PRIMARY MESSAGE",
            f"- **Value Proposition:** {brief.get('value_proposition', '')}",
            f"- **Primary Core Message:** {brief.get('primary_message', '')}",
            f"- **Communication Angle:** {brief.get('communication_angle', '')}",
            f"- **Tone of Voice:** {brief.get('recommended_tone', '')}",
            "",
            "## 6. MESSAGE HIERARCHY & CALL TO ACTION",
            f"**Recommended CTA:** `{brief.get('recommended_cta', '')}`",
            "",
            f"**Suggested Hierarchy:**",
            f"{brief.get('message_hierarchy', '')}",
            "",
            "## 7. VERIFIED PRODUCT FACTS (USER-SUPPLIED)",
        ]

        if verified_facts:
            for f in verified_facts:
                md_lines.append(f"- [VERIFIED FACT] {f}")
        else:
            md_lines.append("_No verified facts explicitly listed._")

        md_lines.extend([
            "",
            "## 8. MISSING EVIDENCE & SUBSTANTIATION CHECKLIST",
        ])
        if missing_evidence:
            for m in missing_evidence:
                md_lines.append(f"- [EVIDENCE REQUIRED] {m}")
        else:
            md_lines.append("_No missing evidence claims flagged._")

        md_lines.extend([
            "",
            "## 9. BRAND RESTRICTIONS & COMPLIANCE RULES",
        ])
        if brand_restrictions:
            for r in brand_restrictions:
                md_lines.append(f"- {r}")
        else:
            md_lines.append("_Standard guidelines apply._")

        md_lines.extend([
            "",
            "## 10. RISK REVIEW CHECKLIST",
        ])
        if risks:
            for rk in risks:
                md_lines.append(f"- ⚠️ {rk}")
        else:
            md_lines.append("_Standard review required before distribution._")

        md_lines.extend([
            "",
            "---",
            "_Generated by Marketing Creative Brief & Ad Variant Generator. Human review required._",
        ])

        return "\n".join(md_lines)

    def export_campaign_full_backup(self, campaign_id: str) -> Dict[str, Any]:
        """Generate structured JSON payload containing campaign, brief, variants, and reviews."""
        campaign = self.campaign_svc.get_campaign(campaign_id)
        brief = self.brief_svc.get_brief_for_campaign(campaign_id)
        variants = self.variant_svc.list_variants_for_campaign(campaign_id)

        reviews = []
        history = []
        if variants:
            from backend.approval_service import ApprovalService
            from backend.evidence_checker import EvidenceChecker
            app_svc = ApprovalService(self.db_path)
            ev_svc = EvidenceChecker(self.db_path)
            reviews = ev_svc.get_claims_for_campaign(campaign_id)
            for v in variants:
                history.extend(app_svc.get_review_history(v["id"]))

        return {
            "campaign": campaign,
            "creative_brief": brief,
            "ad_variants": variants,
            "claim_reviews": reviews,
            "review_history": history,
            "export_timestamp": pd.Timestamp.now().isoformat(),
        }
