"""Unit test for database seed functionality."""

from backend.database import get_connection, init_db
from backend.seed_data import seed_sample_data


def test_seed_sample_data(tmp_path):
    test_db = tmp_path / "seed_test.db"
    init_db(test_db)

    # Seed
    seed_sample_data(test_db, force=True)

    conn = get_connection(test_db)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM campaigns")
    camp_count = cursor.fetchone()[0]
    assert camp_count == 3

    cursor.execute("SELECT COUNT(*) FROM ad_variants")
    variant_count = cursor.fetchone()[0]
    assert variant_count >= 9

    cursor.execute("SELECT COUNT(*) FROM creative_briefs")
    brief_count = cursor.fetchone()[0]
    assert brief_count == 3

    cursor.execute("SELECT COUNT(*) FROM brand_profiles")
    bp_count = cursor.fetchone()[0]
    assert bp_count == 2

    cursor.execute("SELECT COUNT(*) FROM claim_reviews")
    claim_count = cursor.fetchone()[0]
    assert claim_count > 0

    conn.close()
