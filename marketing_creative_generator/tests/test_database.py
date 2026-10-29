"""Unit tests for SQLite database setup and foreign key enforcement."""

import sqlite3
import pytest
from backend.database import get_connection, init_db, row_to_dict


def test_init_db_creates_tables(tmp_path):
    test_db = tmp_path / "test.db"
    init_db(test_db)

    conn = get_connection(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    expected_tables = {
        "brand_profiles",
        "campaigns",
        "creative_briefs",
        "ad_variants",
        "claim_reviews",
        "review_history",
    }
    assert expected_tables.issubset(tables)


def test_foreign_key_enforcement(tmp_path):
    test_db = tmp_path / "fk_test.db"
    init_db(test_db)

    conn = get_connection(test_db)
    # Attempt to insert an ad_variant with non-existent campaign_id
    with pytest.raises(sqlite3.IntegrityError):
        with conn:
            conn.execute(
                """
                INSERT INTO ad_variants (
                    id, campaign_id, name, angle, hook, headline, body_copy,
                    cta, channel, target_audience, primary_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "var-1",
                    "non-existent-campaign",
                    "Variant A",
                    "Problem-Solution",
                    "Hook text",
                    "Headline text",
                    "Body copy",
                    "Learn More",
                    "Social Media",
                    "Devs",
                    "Message",
                    "2026-01-01T00:00:00",
                    "2026-01-01T00:00:00",
                ),
            )
    conn.close()


def test_row_to_dict_parses_json():
    # Test json parsing utility
    fake_row = {
        "id": "c1",
        "features": '["Feature A", "Feature B"]',
        "name": "Test Campaign",
    }

    class DummyRow(dict):
        pass

    dummy = DummyRow(fake_row)
    parsed = row_to_dict(dummy)
    assert parsed["features"] == ["Feature A", "Feature B"]
    assert parsed["name"] == "Test Campaign"
