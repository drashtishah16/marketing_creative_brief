"""Brand Guidelines verification module.

Checks copy against required phrases, prohibited phrases, mandatory disclaimers,
preferred terminology, and tone voice guidelines.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class BrandChecker:
    """Evaluates text copy against defined brand guidelines and profiles."""

    SLANG_PATTERNS = [
        r"\b(?:omg|lol|cuz|gonna|wanna|aint|kinda|dunno|noob|fr fr|cap|lit)\b",
        r"\b(?:insane deal|crazy cheap|super crazy|mindblowing)\b",
    ]

    BUDGET_PATTERNS = [
        r"\b(?:dirt cheap|budget-rate|slashed prices|bargain basement|cheapest ever)\b",
    ]

    HYPE_PATTERNS = [
        r"\b(?:miracle|magic bullet|cure-all|secret hack|overnight sensation)\b",
    ]

    @classmethod
    def check_text(
        cls,
        text: str,
        required_phrases: Optional[List[str]] = None,
        prohibited_phrases: Optional[List[str]] = None,
        mandatory_disclaimers: Optional[List[str]] = None,
        preferred_tone: Optional[str] = None,
        brand_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Run all brand compliance checks on the provided text copy."""
        warnings: List[Dict[str, Any]] = []

        if not text or not text.strip():
            return warnings

        # 1. Prohibited phrases check (High severity)
        if prohibited_phrases:
            for phrase in prohibited_phrases:
                phrase = phrase.strip()
                if not phrase:
                    continue
                pattern = rf"\b{re.escape(phrase)}\b"
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    warnings.append(
                        {
                            "category": "Brand Guidelines",
                            "rule_name": "Prohibited Phrase",
                            "severity": "High",
                            "fragment": match.group(0),
                            "explanation": f"Found prohibited brand phrase: '{phrase}'. Remove or rephrase.",
                        }
                    )

        # 2. Required phrases check (Medium severity if omitted)
        if required_phrases:
            for phrase in required_phrases:
                phrase = phrase.strip()
                if not phrase:
                    continue
                pattern = rf"\b{re.escape(phrase)}\b"
                if not re.search(pattern, text, flags=re.IGNORECASE):
                    warnings.append(
                        {
                            "category": "Brand Guidelines",
                            "rule_name": "Missing Required Phrase",
                            "severity": "Medium",
                            "fragment": "",
                            "explanation": f"Mandatory brand phrase missing: '{phrase}'.",
                        }
                    )

        # 3. Mandatory disclaimers check (High severity if omitted)
        if mandatory_disclaimers:
            for disclaimer in mandatory_disclaimers:
                disclaimer = disclaimer.strip()
                if not disclaimer:
                    continue
                # For long disclaimers, check if significant substring or exact phrase is present
                pattern = rf"{re.escape(disclaimer)}"
                if not re.search(pattern, text, flags=re.IGNORECASE):
                    warnings.append(
                        {
                            "category": "Brand Guidelines",
                            "rule_name": "Missing Mandatory Disclaimer",
                            "severity": "High",
                            "fragment": "",
                            "explanation": f"Mandatory legal disclaimer missing: '{disclaimer}'.",
                        }
                    )

        # 4. Tone of voice consistency
        tone_warnings = cls.check_tone_consistency(text, preferred_tone)
        warnings.extend(tone_warnings)

        return warnings

    @classmethod
    def check_tone_consistency(
        cls, text: str, preferred_tone: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Detect stylistic and tone inconsistencies based on selected brand voice."""
        warnings: List[Dict[str, Any]] = []
        if not preferred_tone:
            return warnings

        tone_lower = preferred_tone.lower()

        # Check exclamation mark intensity
        exclamation_count = text.count("!")
        multiple_exclamations = re.findall(r"!{2,}", text)

        if multiple_exclamations:
            warnings.append(
                {
                    "category": "Brand Tone",
                    "rule_name": "Excessive Punctuation",
                    "severity": "Low",
                    "fragment": multiple_exclamations[0],
                    "explanation": "Multiple consecutive exclamation marks detected; recommend clean professional punctuation.",
                }
            )

        if tone_lower in ("professional", "premium") and exclamation_count > 2:
            warnings.append(
                {
                    "category": "Brand Tone",
                    "rule_name": "Tone Inconsistency (Exclamation)",
                    "severity": "Low",
                    "fragment": f"{exclamation_count} exclamation points",
                    "explanation": f"Selected tone is '{preferred_tone}', but copy contains {exclamation_count} exclamation marks. A subtle, measured style is advised.",
                }
            )

        # Professional tone checks
        if tone_lower == "professional":
            for pat in cls.SLANG_PATTERNS:
                match = re.search(pat, text, flags=re.IGNORECASE)
                if match:
                    warnings.append(
                        {
                            "category": "Brand Tone",
                            "rule_name": "Informal Slang in Professional Copy",
                            "severity": "Medium",
                            "fragment": match.group(0),
                            "explanation": f"Casual slang '{match.group(0)}' conflicts with professional brand tone.",
                        }
                    )

        # Premium tone checks
        if tone_lower == "premium":
            for pat in cls.BUDGET_PATTERNS:
                match = re.search(pat, text, flags=re.IGNORECASE)
                if match:
                    warnings.append(
                        {
                            "category": "Brand Tone",
                            "rule_name": "Discount Phrasing in Premium Tone",
                            "severity": "Medium",
                            "fragment": match.group(0),
                            "explanation": f"Discount phrase '{match.group(0)}' conflicts with luxury/premium positioning.",
                        }
                    )

        # Educational tone checks
        if tone_lower == "educational":
            for pat in cls.HYPE_PATTERNS:
                match = re.search(pat, text, flags=re.IGNORECASE)
                if match:
                    warnings.append(
                        {
                            "category": "Brand Tone",
                            "rule_name": "Sensationalism in Educational Tone",
                            "severity": "Medium",
                            "fragment": match.group(0),
                            "explanation": f"Sensational word '{match.group(0)}' conflicts with educational credibility.",
                        }
                    )

        return warnings
