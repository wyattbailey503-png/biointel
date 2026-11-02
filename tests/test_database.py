"""Tests for Database Schema, Transactions, and Idempotency."""

from __future__ import annotations

import tempfile
from pathlib import Path
from biointel.storage.database import Database


def test_database_initialization_is_idempotent() -> None:
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        db = Database(f.name)
        # Running initialization again should not throw errors
        db.initialize_schema()

        # Check tables exist
        with db.get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            assert "source_registry" in tables
            assert "documents" in tables
            assert "publications" in tables
            assert "technologies" in tables
            assert "structures" in tables
            assert "experiments" in tables
            assert "claims" in tables
            assert "competitor_matches" in tables
            assert "scientific_changes" in tables
            assert "economic_scenarios" in tables


def test_upsert_document_and_versioning(temp_db: Database) -> None:
    doc = {
        "document_id": "test:001",
        "source_id": "europe_pmc",
        "external_id": "12345",
        "title": "Initial Paper",
        "url": "https://example.org/12345",
        "content_hash": "hash_v1",
        "format": "json",
        "ingestion_status": "ingested",
    }
    # Register source first due to foreign key
    temp_db.upsert_source({
        "source_id": "europe_pmc",
        "name": "Europe PMC",
        "publisher": "EMBL-EBI",
        "url": "https://example.org",
        "category": "literature",
    })

    # First insert -> version 1
    is_new = temp_db.upsert_document(doc, raw_payload='{"v": 1}')
    assert is_new is True

    # Re-insert identical hash -> no new version
    is_updated = temp_db.upsert_document(doc, raw_payload='{"v": 1}')
    assert is_updated is False

    # Update with new content hash -> version 2
    doc["content_hash"] = "hash_v2"
    doc["title"] = "Updated Paper Title"
    is_updated_2 = temp_db.upsert_document(doc, raw_payload='{"v": 2}')
    assert is_updated_2 is True

    with temp_db.get_connection() as conn:
        versions = conn.execute("SELECT * FROM document_versions WHERE document_id = ?", ("test:001",)).fetchall()
        assert len(versions) == 2
