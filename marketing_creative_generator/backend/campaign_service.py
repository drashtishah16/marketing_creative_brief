"""Campaign and Brand Profile management service.

Handles CRUD operations, campaign duplication, search/filtering, and metric aggregations.
"""

from __future__ import annotations

import datetime
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from backend.database import get_connection, row_to_dict, rows_to_dicts

logger = logging.getLogger(__name__)


class CampaignService:
    """Manages lifecycle and queries for marketing campaigns and brand profiles."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self.db_path = db_path

    # =========================================================================
    # Brand Profiles CRUD
    # =========================================================================

    def create_brand_profile(
        self,
        name: str,
        brand_name: str,
        tone_of_voice: str,
        preferred_terms: Optional[List[str]] = None,
        prohibited_terms: Optional[List[str]] = None,
        required_phrases: Optional[List[str]] = None,
        mandatory_disclaimers: Optional[List[str]] = None,
        formatting_rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new reusable brand guidelines profile."""
        profile_id = f"bp-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO brand_profiles (
                        id, name, brand_name, tone_of_voice, preferred_terms,
                        prohibited_terms, required_phrases, mandatory_disclaimers,
                        formatting_rules, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile_id,
                        name.strip(),
                        brand_name.strip(),
                        tone_of_voice.strip(),
                        json.dumps(preferred_terms or []),
                        json.dumps(prohibited_terms or []),
                        json.dumps(required_phrases or []),
                        json.dumps(mandatory_disclaimers or []),
                        json.dumps(formatting_rules or {}),
                        now,
                        now,
                    ),
                )
            return self.get_brand_profile(profile_id) or {}
        finally:
            conn.close()

    def get_brand_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Fetch brand profile by ID."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM brand_profiles WHERE id = ?", (profile_id,))
            return row_to_dict(cursor.fetchone())
        finally:
            conn.close()

    def list_brand_profiles(self) -> List[Dict[str, Any]]:
        """List all brand profiles sorted by name."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM brand_profiles ORDER BY name ASC")
            return rows_to_dicts(cursor.fetchall())
        finally:
            conn.close()

    # =========================================================================
    # Campaigns CRUD
    # =========================================================================

    def create_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and create a new campaign record."""
        # Validate required fields
        required_fields = ["name", "product_name", "product_description", "target_audience", "objective", "channel", "tone_of_voice"]
        for field in required_fields:
            val = data.get(field)
            if not val or not str(val).strip():
                raise ValueError(f"Missing required campaign field: '{field}'")

        campaign_id = f"cmp-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        def clean_list(key: str) -> str:
            val = data.get(key, [])
            if isinstance(val, str):
                # Split lines if string
                items = [x.strip() for x in val.split("\n") if x.strip()]
                return json.dumps(items)
            elif isinstance(val, list):
                return json.dumps([str(x).strip() for x in val if str(x).strip()])
            return json.dumps([])

        conn = get_connection(self.db_path)
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO campaigns (
                        id, name, product_name, product_description, features,
                        benefits, target_audience, audience_needs, objective,
                        channel, offer, offer_conditions, tone_of_voice, brand_name,
                        brand_profile_id, verified_facts, claims_requiring_evidence,
                        required_phrases, prohibited_phrases, mandatory_disclaimers,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        campaign_id,
                        str(data["name"]).strip(),
                        str(data["product_name"]).strip(),
                        str(data["product_description"]).strip(),
                        clean_list("features"),
                        clean_list("benefits"),
                        str(data["target_audience"]).strip(),
                        str(data.get("audience_needs", "")).strip(),
                        str(data["objective"]).strip().lower(),
                        str(data["channel"]).strip().lower(),
                        str(data.get("offer", "")).strip(),
                        str(data.get("offer_conditions", "")).strip(),
                        str(data["tone_of_voice"]).strip(),
                        str(data.get("brand_name", "")).strip(),
                        data.get("brand_profile_id"),
                        clean_list("verified_facts"),
                        clean_list("claims_requiring_evidence"),
                        clean_list("required_phrases"),
                        clean_list("prohibited_phrases"),
                        clean_list("mandatory_disclaimers"),
                        now,
                        now,
                    ),
                )
            logger.info("Campaign created with ID: %s", campaign_id)
            return self.get_campaign(campaign_id) or {}
        finally:
            conn.close()

    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single campaign by ID with related data."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            return row_to_dict(cursor.fetchone())
        finally:
            conn.close()

    def list_campaigns(
        self,
        search_query: Optional[str] = None,
        objective: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List campaigns with optional search query and filters."""
        query = "SELECT * FROM campaigns WHERE 1=1"
        params: List[Any] = []

        if search_query and search_query.strip():
            query += " AND (name LIKE ? OR product_name LIKE ? OR brand_name LIKE ?)"
            term = f"%{search_query.strip()}%"
            params.extend([term, term, term])

        if objective and objective.strip().lower() != "all":
            query += " AND objective = ?"
            params.append(objective.strip().lower())

        if channel and channel.strip().lower() != "all":
            query += " AND channel = ?"
            params.append(channel.strip().lower())

        query += " ORDER BY updated_at DESC"

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return rows_to_dicts(cursor.fetchall())
        finally:
            conn.close()

    def update_campaign(self, campaign_id: str, updates: Dict[str, Any]) -> bool:
        """Update campaign fields and flag existing brief as needing review."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = get_connection(self.db_path)

        def clean_list(val: Any) -> str:
            if isinstance(val, str):
                items = [x.strip() for x in val.split("\n") if x.strip()]
                return json.dumps(items)
            elif isinstance(val, list):
                return json.dumps([str(x).strip() for x in val if str(x).strip()])
            return json.dumps([])

        allowed_fields = [
            "name", "product_name", "product_description", "target_audience",
            "audience_needs", "objective", "channel", "offer", "offer_conditions",
            "tone_of_voice", "brand_name", "brand_profile_id"
        ]
        list_fields = [
            "features", "benefits", "verified_facts", "claims_requiring_evidence",
            "required_phrases", "prohibited_phrases", "mandatory_disclaimers"
        ]

        set_clauses = ["updated_at = ?"]
        params: List[Any] = [now]

        for k in allowed_fields:
            if k in updates:
                set_clauses.append(f"{k} = ?")
                params.append(str(updates[k]).strip() if updates[k] is not None else "")

        for k in list_fields:
            if k in updates:
                set_clauses.append(f"{k} = ?")
                params.append(clean_list(updates[k]))

        params.append(campaign_id)
        sql = f"UPDATE campaigns SET {', '.join(set_clauses)} WHERE id = ?"

        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                # When campaign is edited, mark associated creative brief as 'Needs Review'
                conn.execute(
                    "UPDATE creative_briefs SET status = 'Needs Review', updated_at = ? WHERE campaign_id = ?",
                    (now, campaign_id),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def duplicate_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Duplicate an existing campaign and its inputs (variants left to be regenerated)."""
        original = self.get_campaign(campaign_id)
        if not original:
            return None

        dup_data = dict(original)
        dup_data["name"] = f"Copy of {original['name']}"
        # create_campaign will assign a fresh ID and timestamps
        return self.create_campaign(dup_data)

    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign and cascade deletion to brief, variants, and claims."""
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
                return cursor.rowcount > 0
        finally:
            conn.close()

    # =========================================================================
    # Dashboard Metrics Calculation (Real Database Figures)
    # =========================================================================

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Compute live metric counters and breakdown distributions from SQLite."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()

            # 1. Total campaigns
            cursor.execute("SELECT COUNT(*) FROM campaigns")
            total_campaigns = cursor.fetchone()[0]

            # 2. Total variants
            cursor.execute("SELECT COUNT(*) FROM ad_variants")
            total_variants = cursor.fetchone()[0]

            # 3. Variants awaiting review
            cursor.execute("SELECT COUNT(*) FROM ad_variants WHERE review_status = 'Pending Review'")
            pending_review = cursor.fetchone()[0]

            # 4. Approved variants
            cursor.execute("SELECT COUNT(*) FROM ad_variants WHERE review_status = 'Approved'")
            approved_variants = cursor.fetchone()[0]

            # 5. Rejected variants
            cursor.execute("SELECT COUNT(*) FROM ad_variants WHERE review_status = 'Rejected'")
            rejected_variants = cursor.fetchone()[0]

            # 6. High severity warnings (unresolved)
            cursor.execute(
                """
                SELECT COUNT(*) FROM claim_reviews
                WHERE severity = 'High' AND review_decision = 'Unresolved'
                """
            )
            high_severity_warnings = cursor.fetchone()[0]

            # Status breakdown for charts
            cursor.execute(
                """
                SELECT review_status, COUNT(*) as cnt
                FROM ad_variants
                GROUP BY review_status
                """
            )
            status_distribution = {row[0]: row[1] for row in cursor.fetchall()}

            # Marketing angle breakdown
            cursor.execute(
                """
                SELECT angle, COUNT(*) as cnt
                FROM ad_variants
                GROUP BY angle
                ORDER BY cnt DESC
                """
            )
            angle_distribution = {row[0]: row[1] for row in cursor.fetchall()}

            # Objective breakdown
            cursor.execute(
                """
                SELECT objective, COUNT(*) as cnt
                FROM campaigns
                GROUP BY objective
                """
            )
            objective_distribution = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "total_campaigns": total_campaigns,
                "total_variants": total_variants,
                "pending_review": pending_review,
                "approved_variants": approved_variants,
                "rejected_variants": rejected_variants,
                "high_severity_warnings": high_severity_warnings,
                "status_distribution": status_distribution,
                "angle_distribution": angle_distribution,
                "objective_distribution": objective_distribution,
            }
        finally:
            conn.close()
