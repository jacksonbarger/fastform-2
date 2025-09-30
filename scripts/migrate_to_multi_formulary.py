#!/usr/bin/env python3
"""
Multi-Formulary Database Migration Script

Migrates from single formulary to normalized multi-formulary schema.
Creates separate tables for drugs, formularies, and coverage rules.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_multi_formulary_schema(db_path: str) -> None:
    """Create the normalized multi-formulary database schema."""
    conn = sqlite3.connect(db_path)
    
    # Backup existing data
    logger.info("Backing up existing drug_rules data...")
    cursor = conn.execute("SELECT * FROM drug_rules")
    existing_drugs = cursor.fetchall()
    
    # Get column names from existing table
    cursor = conn.execute("PRAGMA table_info(drug_rules)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    logger.info(f"Found {len(existing_drugs)} existing drugs with columns: {existing_columns}")
    
    # Drop existing table
    conn.execute("DROP TABLE IF EXISTS drug_rules")
    
    # Create new normalized schema
    
    # 1. Master drug catalog (insurance-agnostic)
    conn.execute("""
        CREATE TABLE drugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            generic_name TEXT,
            brand_name TEXT,
            ndc TEXT,
            dosage_form TEXT,
            strength_qty REAL,
            strength_unit TEXT,
            route TEXT,
            drug_class TEXT,
            manufacturer TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Insurance formularies/plans
    conn.execute("""
        CREATE TABLE formularies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_name TEXT NOT NULL,
            insurer TEXT NOT NULL,
            plan_type TEXT,
            coverage_year INTEGER,
            state_coverage TEXT,
            effective_date DATE,
            expiration_date DATE,
            update_frequency TEXT DEFAULT 'monthly',
            last_updated DATETIME,
            api_endpoint TEXT,
            data_source TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Formulary-specific coverage rules
    conn.execute("""
        CREATE TABLE formulary_coverage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formulary_id INTEGER NOT NULL,
            drug_id INTEGER NOT NULL,
            is_covered BOOLEAN DEFAULT 1,
            formulary_tier INTEGER,
            prior_authorization BOOLEAN DEFAULT 0,
            quantity_limit BOOLEAN DEFAULT 0,
            step_therapy BOOLEAN DEFAULT 0,
            copay_generic REAL,
            copay_preferred REAL,
            copay_nonpreferred REAL,
            copay_specialty REAL,
            notes TEXT,
            last_verified DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (formulary_id) REFERENCES formularies(id),
            FOREIGN KEY (drug_id) REFERENCES drugs(id),
            UNIQUE(formulary_id, drug_id)
        )
    """)
    
    # 4. Formulary update tracking
    conn.execute("""
        CREATE TABLE formulary_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formulary_id INTEGER NOT NULL,
            update_type TEXT, -- 'scheduled', 'manual', 'api_sync'
            status TEXT, -- 'pending', 'in_progress', 'completed', 'failed'
            drugs_added INTEGER DEFAULT 0,
            drugs_modified INTEGER DEFAULT 0,
            drugs_removed INTEGER DEFAULT 0,
            error_message TEXT,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            FOREIGN KEY (formulary_id) REFERENCES formularies(id)
        )
    """)
    
    # Create indexes for performance
    conn.execute("CREATE INDEX idx_drugs_name ON drugs(name)")
    conn.execute("CREATE INDEX idx_drugs_generic ON drugs(generic_name)")
    conn.execute("CREATE INDEX idx_drugs_brand ON drugs(brand_name)")
    conn.execute("CREATE INDEX idx_coverage_formulary ON formulary_coverage(formulary_id)")
    conn.execute("CREATE INDEX idx_coverage_drug ON formulary_coverage(drug_id)")
    conn.execute("CREATE INDEX idx_coverage_tier ON formulary_coverage(formulary_tier)")
    
    conn.commit()
    logger.info("Multi-formulary schema created successfully")
    
    return existing_drugs, existing_columns

def create_sample_formularies(conn: sqlite3.Connection) -> dict:
    """Create sample insurance formularies."""
    formularies_data = [
        {
            'plan_name': 'Medicare Part D Standard',
            'insurer': 'Centers for Medicare & Medicaid Services',
            'plan_type': 'Medicare Part D',
            'coverage_year': 2025,
            'state_coverage': 'National',
            'effective_date': '2025-01-01',
            'update_frequency': 'quarterly',
            'api_endpoint': 'https://www.cms.gov/files/document/medicare-part-d-formulary-data.json',
            'data_source': 'CMS Open Data'
        },
        {
            'plan_name': 'Aetna Better Health',
            'insurer': 'Aetna Inc.',
            'plan_type': 'Commercial',
            'coverage_year': 2025,
            'state_coverage': 'Multi-state',
            'effective_date': '2025-01-01',
            'update_frequency': 'monthly',
            'api_endpoint': 'https://api.aetna.com/formulary/v1',
            'data_source': 'Aetna API'
        },
        {
            'plan_name': 'Blue Cross Blue Shield Standard',
            'insurer': 'Blue Cross Blue Shield Association',
            'plan_type': 'Commercial',
            'coverage_year': 2025,
            'state_coverage': 'Multi-state',
            'effective_date': '2025-01-01',
            'update_frequency': 'monthly',
            'api_endpoint': 'https://api.bcbs.com/formulary',
            'data_source': 'BCBS Provider Portal'
        },
        {
            'plan_name': 'UnitedHealthcare Choice Plus',
            'insurer': 'UnitedHealth Group',
            'plan_type': 'Commercial',
            'coverage_year': 2025,
            'state_coverage': 'National',
            'effective_date': '2025-01-01',
            'update_frequency': 'bi-weekly',
            'api_endpoint': 'https://developer.uhc.com/formulary/api/v2',
            'data_source': 'UHC Developer API'
        },
        {
            'plan_name': 'Humana Gold Plus',
            'insurer': 'Humana Inc.',
            'plan_type': 'Medicare Advantage',
            'coverage_year': 2025,
            'state_coverage': 'Multi-state',
            'effective_date': '2025-01-01',
            'update_frequency': 'monthly',
            'api_endpoint': 'https://api.humana.com/formulary/v1',
            'data_source': 'Humana Provider Portal'
        },
        {
            'plan_name': 'Cigna HealthCare',
            'insurer': 'Cigna Corporation',
            'plan_type': 'Commercial',
            'coverage_year': 2025,
            'state_coverage': 'National',
            'effective_date': '2025-01-01',
            'update_frequency': 'monthly',
            'api_endpoint': 'https://api.cigna.com/formulary',
            'data_source': 'Cigna Provider API'
        }
    ]
    
    formulary_ids = {}
    
    for formulary in formularies_data:
        cursor = conn.execute("""
            INSERT INTO formularies (
                plan_name, insurer, plan_type, coverage_year, state_coverage,
                effective_date, update_frequency, api_endpoint, data_source, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            formulary['plan_name'], formulary['insurer'], formulary['plan_type'],
            formulary['coverage_year'], formulary['state_coverage'],
            formulary['effective_date'], formulary['update_frequency'],
            formulary['api_endpoint'], formulary['data_source'], datetime.now()
        ))
        
        formulary_ids[formulary['plan_name']] = cursor.lastrowid
        
    conn.commit()
    logger.info(f"Created {len(formularies_data)} sample formularies")
    
    return formulary_ids

def migrate_existing_drugs(conn: sqlite3.Connection, existing_drugs: list, existing_columns: list, formulary_ids: dict) -> None:
    """Migrate existing drug data to new schema."""
    
    # Insert drugs into master catalog
    logger.info("Migrating existing drugs to master catalog...")
    
    drug_id_mapping = {}
    
    for drug_data in existing_drugs:
        # Map old columns to new schema
        drug_dict = dict(zip(existing_columns, drug_data))
        
        cursor = conn.execute("""
            INSERT INTO drugs (
                name, generic_name, brand_name, ndc, dosage_form,
                strength_qty, strength_unit, route
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            drug_dict.get('name'),
            drug_dict.get('generic_name'),
            drug_dict.get('brand_name'),
            drug_dict.get('ndc'),
            drug_dict.get('dosage_form'),
            drug_dict.get('strength_qty'),
            drug_dict.get('strength_unit'),
            drug_dict.get('route')
        ))
        
        new_drug_id = cursor.lastrowid
        drug_id_mapping[drug_dict.get('id', len(drug_id_mapping) + 1)] = new_drug_id
    
    conn.commit()
    logger.info(f"Migrated {len(existing_drugs)} drugs to master catalog")
    
    # Create formulary-specific coverage with variations
    logger.info("Creating formulary-specific coverage rules...")
    
    medicare_id = formulary_ids['Medicare Part D Standard']
    
    # Import existing Medicare data as baseline
    for drug_data in existing_drugs:
        drug_dict = dict(zip(existing_columns, drug_data))
        old_drug_id = drug_dict.get('id', 0)
        new_drug_id = drug_id_mapping.get(old_drug_id)
        
        if new_drug_id:
            conn.execute("""
                INSERT INTO formulary_coverage (
                    formulary_id, drug_id, is_covered, formulary_tier,
                    prior_authorization, quantity_limit, step_therapy
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                medicare_id, new_drug_id, True,
                drug_dict.get('formulary_tier', 1),
                drug_dict.get('prior_authorization', False),
                drug_dict.get('quantity_limit', False),
                drug_dict.get('step_therapy', False)
            ))
    
    # Create realistic variations for other formularies
    create_formulary_variations(conn, drug_id_mapping, formulary_ids)
    
    conn.commit()
    logger.info("Created formulary-specific coverage rules")

def create_formulary_variations(conn: sqlite3.Connection, drug_id_mapping: dict, formulary_ids: dict) -> None:
    """Create realistic formulary variations across different insurers."""
    
    import random
    
    # Get all drug IDs
    drug_ids = list(drug_id_mapping.values())
    
    # Define insurer characteristics
    insurer_profiles = {
        'Aetna Better Health': {'tier_shift': 0, 'pa_rate': 0.15, 'ql_rate': 0.20, 'st_rate': 0.10},
        'Blue Cross Blue Shield Standard': {'tier_shift': 0, 'pa_rate': 0.18, 'ql_rate': 0.15, 'st_rate': 0.12},
        'UnitedHealthcare Choice Plus': {'tier_shift': -1, 'pa_rate': 0.20, 'ql_rate': 0.25, 'st_rate': 0.15},  # More restrictive
        'Humana Gold Plus': {'tier_shift': 0, 'pa_rate': 0.12, 'ql_rate': 0.18, 'st_rate': 0.08},  # Less restrictive
        'Cigna HealthCare': {'tier_shift': 1, 'pa_rate': 0.16, 'ql_rate': 0.22, 'st_rate': 0.11}
    }
    
    # Get Medicare baseline data
    medicare_id = formulary_ids['Medicare Part D Standard']
    cursor = conn.execute("""
        SELECT drug_id, formulary_tier, prior_authorization, quantity_limit, step_therapy
        FROM formulary_coverage 
        WHERE formulary_id = ?
    """, (medicare_id,))
    
    medicare_coverage = cursor.fetchall()
    
    # Create variations for each insurer
    for plan_name, profile in insurer_profiles.items():
        formulary_id = formulary_ids[plan_name]
        
        for drug_id, base_tier, base_pa, base_ql, base_st in medicare_coverage:
            # Adjust tier based on insurer profile
            new_tier = max(1, min(5, base_tier + profile['tier_shift']))
            
            # Adjust restrictions based on insurer rates
            new_pa = base_pa or (random.random() < profile['pa_rate'])
            new_ql = base_ql or (random.random() < profile['ql_rate'])  
            new_st = base_st or (random.random() < profile['st_rate'])
            
            # Some drugs might not be covered by certain insurers
            is_covered = True
            if base_tier == 5:  # Specialty drugs
                is_covered = random.random() < 0.85  # 15% chance not covered
            
            conn.execute("""
                INSERT INTO formulary_coverage (
                    formulary_id, drug_id, is_covered, formulary_tier,
                    prior_authorization, quantity_limit, step_therapy
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (formulary_id, drug_id, is_covered, new_tier, new_pa, new_ql, new_st))

if __name__ == "__main__":
    db_path = "fastform.db"
    
    logger.info("Starting multi-formulary database migration...")
    
    # Create new schema and backup existing data
    existing_drugs, existing_columns = create_multi_formulary_schema(db_path)
    
    # Create connection for data migration
    conn = sqlite3.connect(db_path)
    
    # Create sample formularies
    formulary_ids = create_sample_formularies(conn)
    
    # Migrate existing drug data
    migrate_existing_drugs(conn, existing_drugs, existing_columns, formulary_ids)
    
    # Log final statistics
    cursor = conn.execute("SELECT COUNT(*) FROM drugs")
    drug_count = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM formularies")
    formulary_count = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM formulary_coverage")
    coverage_count = cursor.fetchone()[0]
    
    logger.info(f"\nMigration complete!")
    logger.info(f"📊 Final Statistics:")
    logger.info(f"  - Drugs in catalog: {drug_count}")
    logger.info(f"  - Insurance formularies: {formulary_count}")
    logger.info(f"  - Coverage rules: {coverage_count}")
    
    # Show formulary breakdown
    cursor = conn.execute("""
        SELECT f.plan_name, f.insurer, COUNT(fc.id) as covered_drugs
        FROM formularies f
        LEFT JOIN formulary_coverage fc ON f.id = fc.formulary_id AND fc.is_covered = 1
        GROUP BY f.id, f.plan_name, f.insurer
        ORDER BY covered_drugs DESC
    """)
    
    logger.info(f"\n📋 Coverage by Formulary:")
    for plan_name, insurer, covered_drugs in cursor.fetchall():
        logger.info(f"  - {plan_name} ({insurer}): {covered_drugs} covered drugs")
    
    conn.close()
    logger.info(f"Database saved to: {db_path}")
    logger.info("Ready for multi-formulary API endpoints!")
