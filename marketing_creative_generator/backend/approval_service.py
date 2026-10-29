"""Human review and approval workflow service.

Enforces governance policies, audit history logging, and high-severity warning gating.
Variants cannot be approved with unresolved High-severity warnings without explicit override.
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

from backend.database import get_connection, row_to_dict, rows_to_dicts
from backend.evidence_checker import EvidenceChecker

logger = logging.getLogger(__name__)


class ApprovalService:
    """Manages review lifecycle decisions, audit history, and approval gates."""

    VALID_STATUSES = {"Pending Review", "Approved", "Rejected", "Needs Revision"}

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self.db_path = db_path
        self.evidence_checker = EvidenceChecker(db_path)

    def get_review_history(self, variant_id: str) -> List[Dict[str, Any]]:
        """Retrieve complete audit history trail for a specific variant."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM review_history
                WHERE variant_id = ?
                ORDER BY created_at DESC
                """,
                (variant_id,),
            )
            return rows_to_dicts(cursor.fetchall())
        finally:
            conn.close()

    def approve_variant(
        self,
        variant_id: str,
        reviewer_name: str = "Human Reviewer",
        override_reason: str = "",
    ) -> Dict[str, Any]:
        """Approve a variant. Blocks approval if unresolved High-severity warnings exist without override."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ad_variants WHERE id = ?", (variant_id,))
            var_row = cursor.fetchone()
            if not var_row:
                raise ValueError(f"Variant '{variant_id}' not found.")
            variant = row_to_dict(var_row)

            # Check for unresolved high-severity claims
            unresolved_high = self.evidence_checker.count_unresolved_high_severity(variant_id)
            if unresolved_high > 0 and not (override_reason and override_reason.strip()):
                raise PermissionError(
                    f"Cannot approve variant '{variant_id}': Found {unresolved_high} unresolved High-severity warning(s). "
                    "Reviewer must either supply verified evidence or document an explicit override justification."
                )

            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            prev_status = variant["review_status"]
            notes = "Standard human approval." if not override_reason else f"Approved with override: {override_reason}"

            with conn:
                conn.execute(
                    """
                    UPDATE ad_variants
                    SET review_status = 'Approved',
                        rejection_reason = '',
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (now, variant_id),
                )
                conn.execute(
                    """
                    INSERT INTO review_history (
                        id, variant_id, action, previous_status, new_status,
                        reviewer_name, notes, created_at
                    ) VALUES (?, ?, 'Approved', ?, 'Approved', ?, ?, ?)
                    """,
                    (
                        f"rev-{uuid.uuid4().hex[:8]}",
                        variant_id,
                        prev_status,
                        reviewer_name.strip() or "Human Reviewer",
                        notes,
                        now,
                    ),
                )
            logger.info("Variant %s approved by %s", variant_id, reviewer_name)
            cursor.execute("SELECT * FROM ad_variants WHERE id = ?", (variant_id,))
            return row_to_dict(cursor.fetchone()) or {}
        finally:
            conn.close()

    def reject_variant(
        self,
        variant_id: str,
        rejection_reason: str,
        reviewer_name: str = "Human Reviewer",
    ) -> Dict[str, Any]:
        """Reject a variant and document the mandatory rejection rationale."""
        if not rejection_reason or not rejection_reason.strip():
            raise ValueError("A clear rejection rationale is required to reject a variant.")

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ad_variants WHERE id = ?", (variant_id,))
            var_row = cursor.fetchone()
            if not var_row:
                raise ValueError(f"Variant '{variant_id}' not found.")
            variant = row_to_dict(var_row)

            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            prev_status = variant["review_status"]

            with conn:
                conn.execute(
                    """
                    UPDATE ad_variants
                    SET review_status = 'Rejected',
                        rejection_reason = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (rejection_reason.strip(), now, variant_id),
                )
                conn.execute(
                    """
                    INSERT INTO review_history (
                        id, variant_id, action, previous_status, new_status,
                        reviewer_name, notes, created_at
                    ) VALUES (?, ?, 'Rejected', ?, 'Rejected', ?, ?, ?)
                    """,
                    (
                        f"rev-{uuid.uuid4().hex[:8]}",
                        variant_id,
                        prev_status,
                        reviewer_name.strip() or "Human Reviewer",
                        rejection_reason.strip(),
                        now,
                    ),
                )
            logger.info("Variant %s rejected by %s: %s", variant_id, reviewer_name, rejection_reason)
            cursor.execute("SELECT * FROM ad_variants WHERE id = ?", (variant_id,))
            return row_to_dict(cursor.fetchone()) or {}
        finally:
            conn.close()

    def request_revisions(
        self,
        variant_id: str,
        revision_notes: str,
        reviewer_name: str = "Human Reviewer",
    ) -> Dict[str, Any]:
        """Mark variant as Needs Revision with actionable guidance for copy editors."""
        if not revision_notes or not revision_notes.strip():
            raise ValueError("Revision instructions are required.")

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ad_variants WHERE id = ?", (variant_id,))
            var_row = cursor.fetchone()
            if not var_row:
                raise ValueError(f"Variant '{variant_id}' not found.")
            variant = row_to_dict(var_row)

            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            prev_status = variant["review_status"]

            with conn:
                conn.execute(
                    """
                    UPDATE ad_variants
                    SET review_status = 'Needs Revision',
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (now, variant_id),
                )
                conn.execute(
                    """
                    INSERT INTO review_history (
                        id, variant_id, action, previous_status, new_status,
                        reviewer_name, notes, created_at
                    ) VALUES (?, ?, 'Requested Revision', ?, 'Needs Revision', ?, ?, ?)
                    """,
                    (
                        f"rev-{uuid.uuid4().hex[:8]}",
                        variant_id,
                        prev_status,
                        reviewer_name.strip() or "Human Reviewer",
                        revision_notes.strip(),
                        now,
                    ),
                )
            logger.info("Variant %s marked Needs Revision by %s", variant_id, reviewer_name)
            cursor.execute("SELECT * FROM ad_variants WHERE id = ?", (variant_id,))
            return row_to_dict(cursor.fetchone()) or {}
        finally:
            conn.close()
