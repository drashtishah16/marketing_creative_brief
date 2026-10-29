"""Database configuration, schema definition, and connection management.

Uses SQLite with explicit foreign key enforcement, transaction safety,
and structured logging.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "marketing_generator.db"


def get_connection(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    """Create and return a SQLite database connection with FKs enabled."""
    target_path = Path(db_path) if db_path else DEFAULT_DB_PATH

    if target_path != Path(":memory:") and not str(target_path).startswith(":memory:"):
        target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_path), timeout=30.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str | Path] = None) -> None:
    """Initialize database tables, indices, and default constraints."""
    target_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    logger.info("Initializing database at %s", target_path)

    schema_sql = """
    -- Brand guidelines profiles
    CREATE TABLE IF NOT EXISTS brand_profiles (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        brand_name TEXT NOT NULL,
        tone_of_voice TEXT NOT NULL,
        preferred_terms TEXT DEFAULT '[]',
        prohibited_terms TEXT DEFAULT '[]',
        required_phrases TEXT DEFAULT '[]',
        mandatory_disclaimers TEXT DEFAULT '[]',
        formatting_rules TEXT DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    -- Marketing campaigns
    CREATE TABLE IF NOT EXISTS campaigns (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        product_name TEXT NOT NULL,
        product_description TEXT NOT NULL,
        features TEXT DEFAULT '[]',
        benefits TEXT DEFAULT '[]',
        target_audience TEXT NOT NULL,
        audience_needs TEXT DEFAULT '',
        objective TEXT NOT NULL,
        channel TEXT NOT NULL,
        offer TEXT DEFAULT '',
        offer_conditions TEXT DEFAULT '',
        tone_of_voice TEXT NOT NULL,
        brand_name TEXT DEFAULT '',
        brand_profile_id TEXT,
        verified_facts TEXT DEFAULT '[]',
        claims_requiring_evidence TEXT DEFAULT '[]',
        required_phrases TEXT DEFAULT '[]',
        prohibited_phrases TEXT DEFAULT '[]',
        mandatory_disclaimers TEXT DEFAULT '[]',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (brand_profile_id) REFERENCES brand_profiles(id) ON DELETE SET NULL
    );

    -- Generated & edited creative briefs
    CREATE TABLE IF NOT EXISTS creative_briefs (
        id TEXT PRIMARY KEY,
        campaign_id TEXT NOT NULL UNIQUE,
        overview TEXT NOT NULL,
        product_summary TEXT NOT NULL,
        objective TEXT NOT NULL,
        target_audience TEXT NOT NULL,
        audience_problem TEXT NOT NULL,
        customer_insight TEXT NOT NULL,
        value_proposition TEXT NOT NULL,
        primary_message TEXT NOT NULL,
        communication_angle TEXT NOT NULL,
        recommended_tone TEXT NOT NULL,
        desired_response TEXT NOT NULL,
        message_hierarchy TEXT NOT NULL,
        recommended_cta TEXT NOT NULL,
        verified_facts TEXT DEFAULT '[]',
        missing_evidence TEXT DEFAULT '[]',
        brand_restrictions TEXT DEFAULT '[]',
        potential_risks TEXT DEFAULT '[]',
        status TEXT NOT NULL DEFAULT 'Needs Review',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
    );

    -- Generated advertising variants
    CREATE TABLE IF NOT EXISTS ad_variants (
        id TEXT PRIMARY KEY,
        campaign_id TEXT NOT NULL,
        name TEXT NOT NULL,
        angle TEXT NOT NULL,
        hook TEXT NOT NULL,
        headline TEXT NOT NULL,
        body_copy TEXT NOT NULL,
        cta TEXT NOT NULL,
        channel TEXT NOT NULL,
        target_audience TEXT NOT NULL,
        primary_message TEXT NOT NULL,
        supporting_evidence_needed TEXT DEFAULT '[]',
        warnings TEXT DEFAULT '[]',
        review_status TEXT NOT NULL DEFAULT 'Pending Review',
        rejection_reason TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
    );

    -- Claim and evidence audit reviews
    CREATE TABLE IF NOT EXISTS claim_reviews (
        id TEXT PRIMARY KEY,
        variant_id TEXT,
        campaign_id TEXT NOT NULL,
        claim_text TEXT NOT NULL,
        warning_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        explanation TEXT NOT NULL,
        evidence_required TEXT NOT NULL,
        evidence_supplied INTEGER NOT NULL DEFAULT 0,
        evidence_source TEXT DEFAULT '',
        document_reference TEXT DEFAULT '',
        review_decision TEXT NOT NULL DEFAULT 'Unresolved',
        reviewer_notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (variant_id) REFERENCES ad_variants(id) ON DELETE CASCADE
    );

    -- Human review and decision audit trail
    CREATE TABLE IF NOT EXISTS review_history (
        id TEXT PRIMARY KEY,
        variant_id TEXT NOT NULL,
        action TEXT NOT NULL,
        previous_status TEXT,
        new_status TEXT NOT NULL,
        reviewer_name TEXT NOT NULL DEFAULT 'Human Reviewer',
        notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY (variant_id) REFERENCES ad_variants(id) ON DELETE CASCADE
    );

    -- Indices for query performance
    CREATE INDEX IF NOT EXISTS idx_campaigns_name ON campaigns(name);
    CREATE INDEX IF NOT EXISTS idx_campaigns_objective ON campaigns(objective);
    CREATE INDEX IF NOT EXISTS idx_ad_variants_campaign ON ad_variants(campaign_id);
    CREATE INDEX IF NOT EXISTS idx_ad_variants_status ON ad_variants(review_status);
    CREATE INDEX IF NOT EXISTS idx_claim_reviews_variant ON claim_reviews(variant_id);
    CREATE INDEX IF NOT EXISTS idx_claim_reviews_severity ON claim_reviews(severity);
    CREATE INDEX IF NOT EXISTS idx_review_history_variant ON review_history(variant_id);
    """

    conn = get_connection(target_path)
    try:
        with conn:
            conn.executescript(schema_sql)
        logger.info("Database schema initialized successfully.")
    finally:
        conn.close()


def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    """Convert an sqlite3.Row object to a standard Python dictionary with parsed JSON fields."""
    if row is None:
        return None
    d = dict(row)
    # Attempt to parse json columns safely
    json_fields = {
        "features",
        "benefits",
        "verified_facts",
        "claims_requiring_evidence",
        "required_phrases",
        "prohibited_phrases",
        "mandatory_disclaimers",
        "preferred_terms",
        "prohibited_terms",
        "formatting_rules",
        "missing_evidence",
        "brand_restrictions",
        "potential_risks",
        "supporting_evidence_needed",
        "warnings",
    }
    for field in json_fields:
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                # Keep as-is if not valid json
                pass
    return d


def rows_to_dicts(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    """Convert a list of sqlite3.Row objects to standard Python dictionaries."""
    return [d for r in rows if (d := row_to_dict(r)) is not None]
