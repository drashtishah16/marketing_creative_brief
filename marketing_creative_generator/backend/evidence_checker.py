"""Evidence tracking and claim review management service.

Maintains traceable audit records for claim substantiation, document references,
and human compliance determinations.
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from backend.database import get_connection, row_to_dict, rows_to_dicts

logger = logging.getLogger(__name__)

COMPLIANCE_DISCLAIMER = (
    "DISCLAIMER: This system provides automated marketing heuristics and claim-warning checks. "
    "It does NOT constitute a legal compliance guarantee or formal legal advice. "
    "All claims and disclosures must be reviewed by qualified legal or regulatory counsel."
)


class EvidenceChecker:
    """Manages claim audit records, evidence logging, and resolution statuses in SQLite."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self.db_path = db_path

    def register_claim_warnings(
        self,
        campaign_id: str,
        variant_id: Optional[str],
        warnings: List[Dict[str, Any]],
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[str]:
        """Persist detected claim warnings into the claim_reviews table."""
        if not warnings:
            return []

        inserted_ids = []
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        should_close = False
        target_conn = conn
        if target_conn is None:
            target_conn = get_connection(self.db_path)
            should_close = True

        try:
            for w in warnings:
                # Only insert claim verification warnings into claim_reviews table
                if w.get("category") not in ("Claim Verification", "Promotional Disclosure"):
                    continue

                claim_id = f"clm-{uuid.uuid4().hex[:8]}"
                claim_text = w.get("fragment") or w.get("explanation", "")
                target_conn.execute(
                    """
                    INSERT INTO claim_reviews (
                        id, variant_id, campaign_id, claim_text, warning_type,
                        severity, explanation, evidence_required, evidence_supplied,
                        evidence_source, document_reference, review_decision,
                        reviewer_notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        claim_id,
                        variant_id,
                        campaign_id,
                        claim_text,
                        w.get("rule_name", "General Claim Warning"),
                        w.get("severity", "Medium"),
                        w.get("explanation", ""),
                        w.get("evidence_required", "Documentation verifying factual accuracy."),
                        1 if w.get("is_corroborated") else 0,
                        "User verified product facts" if w.get("is_corroborated") else "",
                        "",
                        "Accepted with Evidence" if w.get("is_corroborated") else "Unresolved",
                        "",
                        now,
                        now,
                    ),
                )
                inserted_ids.append(claim_id)
            if should_close:
                target_conn.commit()
            logger.info("Registered %d claim reviews for campaign %s", len(inserted_ids), campaign_id)
        finally:
            if should_close:
                target_conn.close()

        return inserted_ids

    def get_claims_for_variant(self, variant_id: str) -> List[Dict[str, Any]]:
        """Retrieve all claim review records linked to a specific variant."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM claim_reviews
                WHERE variant_id = ?
                ORDER BY CASE severity WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, created_at DESC
                """,
                (variant_id,),
            )
            return rows_to_dicts(cursor.fetchall())
        finally:
            conn.close()

    def get_claims_for_campaign(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Retrieve all claim review records linked to a campaign."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM claim_reviews
                WHERE campaign_id = ?
                ORDER BY CASE severity WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, created_at DESC
                """,
                (campaign_id,),
            )
            return rows_to_dicts(cursor.fetchall())
        finally:
            conn.close()

    def update_claim_decision(
        self,
        claim_id: str,
        decision: str,
        evidence_source: str = "",
        document_reference: str = "",
        reviewer_notes: str = "",
    ) -> bool:
        """Record reviewer decision and supporting documentation for a claim warning."""
        valid_decisions = {"Unresolved", "Accepted with Evidence", "Waived", "Rejected"}
        if decision not in valid_decisions:
            raise ValueError(f"Invalid decision '{decision}'. Must be one of {valid_decisions}")

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        evidence_supplied = 1 if decision in ("Accepted with Evidence", "Waived") else 0

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE claim_reviews
                    SET review_decision = ?,
                        evidence_supplied = ?,
                        evidence_source = ?,
                        document_reference = ?,
                        reviewer_notes = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        decision,
                        evidence_supplied,
                        evidence_source,
                        document_reference,
                        reviewer_notes,
                        now,
                        claim_id,
                    ),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def count_unresolved_high_severity(self, variant_id: str) -> int:
        """Return count of unresolved high-severity claims that block approval."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM claim_reviews
                WHERE variant_id = ?
                  AND severity = 'High'
                  AND review_decision = 'Unresolved'
                """,
                (variant_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            conn.close()
