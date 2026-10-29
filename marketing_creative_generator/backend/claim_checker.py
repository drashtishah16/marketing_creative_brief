"""Claim detection and warning analysis engine.

Detects potentially unsubstantiated, misleading, or sensitive marketing claims:
- Numerical performance claims
- Guarantees and risk-free claims
- Absolute superlatives (#1, best, safest)
- Sensitive health or financial claims
- Testimonials and endorsements
- Unverified awards and certifications
- Unsubstantiated competitor comparisons
- Fabricated urgency and scarcity
- Discounts with missing terms or conditions
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class ClaimChecker:
    """Scans marketing copy for claims requiring substantiation and assigns severity."""

    # 1. Absolute Superlatives (Medium to High)
    ABSOLUTE_PATTERNS = [
        (r"\b(?:the best|#1|number one|no\. 1)\b", "Absolute Superlative (#1 / The Best)", "High",
         "Independent benchmark or market share research proving #1 market position."),
        (r"\b(?:safest|most secure|100% safe|unhackable)\b", "Absolute Safety Claim", "High",
         "Third-party safety audits or certification proving absolute safety."),
        (r"\b(?:unrivaled|unmatched|incomparable|revolutionary|miraculous)\b", "Unsubstantiated Hyperbole", "Medium",
         "Documented technological or competitive differentiation."),
        (r"\b(?:the only solution|only tool that)\b", "Exclusivity Claim", "High",
         "Market landscape analysis verifying absence of alternative solutions."),
    ]

    # 2. Guarantees & Risk-Free Promises
    GUARANTEE_PATTERNS = [
        (r"\b(?:guaranteed|guarantee|100% guaranteed)\b", "Performance Guarantee", "High",
         "Terms of service, refund policy, and legally binding guarantee documentation."),
        (r"\b(?:risk[- ]free|zero risk|no risk)\b", "Risk-Free Representation", "High",
         "Refund policy or trial terms outlining user protections and limitations."),
        (r"\b(?:money[- ]back guarantee|full refund guaranteed)\b", "Money-Back Guarantee", "Medium",
         "Published refund policy specifying qualification criteria and processing timeframe."),
    ]

    # 3. Sensitive Health & Financial Claims (Always High)
    SENSITIVE_PATTERNS = [
        (r"\b(?:cure|treat|heals|reverses disease|medical grade|fda approved)\b", "Sensitive Medical/Health Claim", "High",
         "Clinical trials, regulatory clearances (FDA/EMA), or medical board citations."),
        (r"\b(?:lose \d+\s*(?:lbs|kg|pounds)|melt fat|anti-aging miracle)\b", "Weight Loss / Health Claim", "High",
         "Peer-reviewed scientific study validating specific physical outcomes."),
        (r"\b(?:guaranteed returns|passive income|get rich|100% profit|financial freedom)\b", "Sensitive Financial Return Claim", "High",
         "Registered financial prospectus and statutory regulatory disclosures (SEC/FINRA/FCA)."),
    ]

    # 4. Numerical Performance & Statistical Claims
    NUMERICAL_PATTERNS = [
        (r"\b\d+(?:\.\d+)?%", "Numerical Improvement Claim", "Medium",
         "Internal case studies, user benchmarks, or statistical methodology report verifying percentage figure."),
        (r"\b(?:saves? \$?\d+[\d,]*(?:\.\d{2})?|\$?\d+[\d,]* in savings)\b", "Monetary Savings Claim", "Medium",
         "Calculated customer ROI model with transparent baseline assumptions."),
        (r"\b(?:\d+x (?:faster|cheaper|better|more productive|roi))\b", "Multiplier Performance Claim", "Medium",
         "Comparative benchmark test methodology and raw data logs."),
        (r"\b(?:99\.\d+%\s*(?:uptime|reliability|accuracy))\b", "High-Availability / SLA Claim", "Medium",
         "Historical infrastructure telemetry reports and published SLA documentation."),
    ]

    # 5. Awards & Certifications
    AWARD_PATTERNS = [
        (r"\b(?:award[- ]winning|voted best|rated #1 by)\b", "Award Representation", "Medium",
         "Awarding body name, award year, and evaluation criteria reference."),
        (r"\b(?:iso\s*\d+|hipaa certified|soc 2 compliant|certified organic)\b", "Certification Claim", "High",
         "Official certificate of compliance from accredited audit registrar."),
    ]

    # 6. Testimonials & Endorsements
    TESTIMONIAL_PATTERNS = [
        (r"\b(?:thousands of happy customers|millions trust|customers agree)\b", "Broad Customer Consensus Claim", "Low",
         "Customer count verification or survey methodology summary."),
        (r"\b(?:endorsed by|recommended by doctors|dentists recommend)\b", "Professional Endorsement", "High",
         "Documented endorsement contract or certified survey of practitioners."),
    ]

    # 7. Unverified Scarcity & Urgency
    URGENCY_PATTERNS = [
        (r"\b(?:only \d+ (?:left|spots left|seats remaining))\b", "Stock Scarcity Claim", "Medium",
         "Live inventory integration or quota policy verifying stock limitation."),
        (r"\b(?:offer ends in \d+ (?:hours|minutes)|today only|expires tonight)\b", "Urgency / Expiry Claim", "Medium",
         "Campaign schedule confirming verified offer expiration window."),
    ]

    # 8. Unsubstantiated Competitor Comparisons
    COMPARISON_PATTERNS = [
        (r"\b(?:better than|superior to|outperforms|faster than)\s+([A-Z][a-zA-Z0-9_]+)\b", "Direct Competitor Comparison", "High",
         "Head-to-head empirical testing report under identical operating conditions."),
    ]

    @classmethod
    def check_claims(
        cls,
        text: str,
        verified_facts: Optional[List[str]] = None,
        offer_conditions: Optional[str] = None,
        has_offer: bool = False,
    ) -> List[Dict[str, Any]]:
        """Analyze text and generate structured warnings for claims needing evidence."""
        warnings: List[Dict[str, Any]] = []
        if not text or not text.strip():
            return warnings

        verified_text = " ".join(verified_facts or []).lower()

        # Check all rule pattern categories
        all_pattern_groups = [
            cls.ABSOLUTE_PATTERNS,
            cls.GUARANTEE_PATTERNS,
            cls.SENSITIVE_PATTERNS,
            cls.NUMERICAL_PATTERNS,
            cls.AWARD_PATTERNS,
            cls.TESTIMONIAL_PATTERNS,
            cls.URGENCY_PATTERNS,
        ]

        for group in all_pattern_groups:
            for pattern, warning_type, severity, evidence_req in group:
                matches = re.finditer(pattern, text, flags=re.IGNORECASE)
                for m in matches:
                    fragment = m.group(0)
                    # If this claim is already explicitly acknowledged in verified_facts, lower severity or annotate
                    if fragment.lower() in verified_text:
                        # Still flag for trace, but note verification
                        warnings.append({
                            "category": "Claim Verification",
                            "rule_name": warning_type,
                            "severity": "Low",
                            "fragment": fragment,
                            "explanation": f"Claim '{fragment}' detected; corroborated by supplied verified facts.",
                            "evidence_required": evidence_req,
                            "is_corroborated": True,
                        })
                    else:
                        warnings.append({
                            "category": "Claim Verification",
                            "rule_name": warning_type,
                            "severity": severity,
                            "fragment": fragment,
                            "explanation": f"Unsubstantiated claim '{fragment}' detected. Requires supporting evidence.",
                            "evidence_required": evidence_req,
                            "is_corroborated": False,
                        })

        # Check Competitor Comparisons
        for pattern, warning_type, severity, evidence_req in cls.COMPARISON_PATTERNS:
            for m in re.finditer(pattern, text, flags=re.IGNORECASE):
                competitor = m.group(1)
                warnings.append({
                    "category": "Claim Verification",
                    "rule_name": warning_type,
                    "severity": severity,
                    "fragment": m.group(0),
                    "explanation": f"Direct comparison against '{competitor}' without documented proof.",
                    "evidence_required": evidence_req,
                    "is_corroborated": False,
                })

        # Check Discount / Offer without conditions
        discount_match = re.search(r"\b(?:\d+%\s*off|save\s*\$?\d+|free\s*gift)\b", text, flags=re.IGNORECASE)
        if discount_match:
            if not offer_conditions or not offer_conditions.strip():
                warnings.append({
                    "category": "Promotional Disclosure",
                    "rule_name": "Discount Missing Terms",
                    "severity": "High",
                    "fragment": discount_match.group(0),
                    "explanation": f"Promotional discount '{discount_match.group(0)}' promoted without stated terms, eligibility, or expiration.",
                    "evidence_required": "Published promotional terms, minimum purchase requirement, and expiration date.",
                    "is_corroborated": False,
                })

        return warnings
