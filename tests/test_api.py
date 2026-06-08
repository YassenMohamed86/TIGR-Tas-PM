"""
test_api.py — Flask API and Route Tests
========================================

All test data is CATEGORY 2 (synthetic) — no biological sequences.
"""

from __future__ import annotations

import pytest

from app import app


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ---------------------------------------------------------------------------
# Web route tests
# ---------------------------------------------------------------------------

def test_index_page_loads(client) -> None:
    """GET / should return 200."""
    rv = client.get("/")
    assert rv.status_code == 200


# ---------------------------------------------------------------------------
# JSON API tests — CATEGORY 2 (synthetic) data
# ---------------------------------------------------------------------------

def test_api_analyze_valid_sequence(client) -> None:
    """A valid 60-nt synthetic sequence should produce scored pairs."""
    rv = client.post(
        "/api/analyze",
        json={
            "sequence": "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG",
            "spacer_length": 9,
        },
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == "success"
    assert data["total_pairs"] > 0


def test_api_analyze_invalid_sequence(client) -> None:
    """Non-nucleotide characters should return 400."""
    rv = client.post(
        "/api/analyze",
        json={
            "sequence": "XXXX",
            "spacer_length": 9,
        },
    )
    assert rv.status_code == 400
    data = rv.get_json()
    assert data["status"] == "error"


def test_api_analyze_empty_sequence(client) -> None:
    """An empty sequence string should return 400."""
    rv = client.post(
        "/api/analyze",
        json={
            "sequence": "",
            "spacer_length": 9,
        },
    )
    assert rv.status_code == 400
