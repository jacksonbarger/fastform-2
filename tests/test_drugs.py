import pytest
import sqlite3
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from fastform.api.app import app
from fastform.settings import settings

client = TestClient(app)

@pytest.fixture
def temp_db():
    """Create a temporary database for testing with enhanced schema"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Create enhanced table schema matching the new structure
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE drug_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dosage_form TEXT,
            strength_qty REAL,
            strength_unit TEXT,
            route TEXT,
            generic_name TEXT,
            brand_name TEXT,
            ndc TEXT,
            formulary_tier INTEGER,
            prior_authorization BOOLEAN DEFAULT 0,
            quantity_limit BOOLEAN DEFAULT 0,
            step_therapy BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert test data with enhanced schema
    conn.executemany("""
        INSERT INTO drug_rules (
            name, dosage_form, strength_qty, strength_unit, route,
            generic_name, brand_name, ndc, formulary_tier,
            prior_authorization, quantity_limit, step_therapy
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Acetaminophen', 'tablet', 500.0, 'mg', 'oral', 'acetaminophen', 'Tylenol', '12345-001-01', 1, False, False, False),
        ('Ibuprofen', 'tablet', 200.0, 'mg', 'oral', 'ibuprofen', 'Advil', '12345-003-01', 1, False, False, False),
        ('Aspirin', 'tablet', 325.0, 'mg', 'oral', 'aspirin', 'Bayer', '12345-005-01', 1, False, False, False)
    ])
    conn.commit()
    conn.close()
    
    # Temporarily override settings
    original_db_path = settings.db_path
    settings.db_path = db_path
    
    yield db_path
    
    # Cleanup
    settings.db_path = original_db_path
    Path(db_path).unlink()

def test_search_drugs_exact_match(temp_db):
    """Test drug search with exact match"""
    response = client.post("/v1/drugs/search", json={"query": "Acetaminophen"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Acetaminophen"
    assert data[0]["dosage_form"] == "tablet"
    assert data[0]["brand_name"] == "Tylenol"
    assert data[0]["formulary_tier"] == 1

def test_search_drugs_case_insensitive(temp_db):
    """Test case insensitive search"""
    response = client.post("/v1/drugs/search", json={"query": "acetaminophen"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Acetaminophen"

def test_search_drugs_spacing_insensitive(temp_db):
    """Test spacing insensitive search"""
    response = client.post("/v1/drugs/search", json={"query": "Aceta minophen"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Acetaminophen"

def test_search_drugs_generic_name(temp_db):
    """Test search by generic name"""
    response = client.post("/v1/drugs/search", json={"query": "ibuprofen"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Ibuprofen"
    assert data[0]["generic_name"] == "ibuprofen"

def test_search_drugs_brand_name(temp_db):
    """Test search by brand name"""
    response = client.post("/v1/drugs/search", json={"query": "Advil"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["brand_name"] == "Advil"
    assert data[0]["name"] == "Ibuprofen"

def test_search_drugs_empty_query(temp_db):
    """Test empty query returns empty results"""
    response = client.post("/v1/drugs/search", json={"query": ""})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

def test_search_drugs_no_matches(temp_db):
    """Test query with no matches returns empty results"""
    response = client.post("/v1/drugs/search", json={"query": "nonexistent"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
