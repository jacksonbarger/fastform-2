"""
Formularies API routes for FastForm.
"""

import sqlite3
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...settings import Settings

router = APIRouter()
settings = Settings()

class FormularyInfo(BaseModel):
    """Formulary information model."""
    id: int
    plan_name: str
    insurer: str
    update_frequency: str
    last_updated: Optional[str] = None
    is_active: bool
    coverage_count: int  # Number of drugs covered

class FormularyStats(BaseModel):
    """Formulary statistics model."""
    total_formularies: int
    active_formularies: int
    total_drugs: int
    total_coverage_rules: int

@router.get("/", response_model=List[FormularyInfo])
async def get_formularies(
    active_only: bool = Query(True, description="Only return active formularies"),
    insurer: Optional[str] = Query(None, description="Filter by insurer name")
):
    """
    Get list of available formularies for dropdown selection.
    
    Returns formulary options that users can select to search 
    against specific insurance coverage.
    """
    try:
        conn = sqlite3.connect(settings.db_path)
        
        # Build query with optional filters
        where_clauses = []
        params = []
        
        if active_only:
            where_clauses.append("f.is_active = 1")
        
        if insurer:
            where_clauses.append("LOWER(f.insurer) LIKE LOWER(?)")
            params.append(f"%{insurer}%")
        
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                f.id,
                f.plan_name,
                f.insurer,
                
                f.update_frequency,
                f.last_updated,
                f.is_active,
                COUNT(fc.drug_id) as coverage_count
            FROM formularies f
            LEFT JOIN formulary_coverage fc ON f.id = fc.formulary_id
            {where_clause}
            GROUP BY f.id, f.plan_name, f.insurer,  
                     f.update_frequency, f.last_updated, f.is_active
            ORDER BY f.insurer, f.plan_name
        """
        
        cursor = conn.execute(query, params)
        formularies = []
        
        for row in cursor.fetchall():
            formulary = FormularyInfo(
                id=row[0],
                plan_name=row[1],
                insurer=row[2],
                update_frequency=row[3],
                last_updated=row[4],
                is_active=bool(row[5]),
                coverage_count=row[6]
            )
            formularies.append(formulary)
        
        conn.close()
        return formularies
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/stats", response_model=FormularyStats)
async def get_formulary_stats():
    """
    Get overall formulary system statistics.
    
    Provides summary information about the multi-formulary system
    including counts of formularies, drugs, and coverage rules.
    """
    try:
        conn = sqlite3.connect(settings.db_path)
        
        # Get formulary counts
        cursor = conn.execute("SELECT COUNT(*) FROM formularies")
        total_formularies = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM formularies WHERE is_active = 1")
        active_formularies = cursor.fetchone()[0]
        
        # Get drug count
        cursor = conn.execute("SELECT COUNT(*) FROM drugs")
        total_drugs = cursor.fetchone()[0]
        
        # Get coverage rules count
        cursor = conn.execute("SELECT COUNT(*) FROM formulary_coverage")
        total_coverage_rules = cursor.fetchone()[0]
        
        conn.close()
        
        return FormularyStats(
            total_formularies=total_formularies,
            active_formularies=active_formularies,
            total_drugs=total_drugs,
            total_coverage_rules=total_coverage_rules
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{formulary_id}", response_model=FormularyInfo)
async def get_formulary_details(formulary_id: int):
    """
    Get detailed information about a specific formulary.
    
    Returns comprehensive information about a single formulary
    including coverage statistics and metadata.
    """
    try:
        conn = sqlite3.connect(settings.db_path)
        
        query = """
            SELECT 
                f.id,
                f.plan_name,
                f.insurer,
                
                f.update_frequency,
                f.last_updated,
                f.is_active,
                COUNT(fc.drug_id) as coverage_count
            FROM formularies f
            LEFT JOIN formulary_coverage fc ON f.id = fc.formulary_id
            WHERE f.id = ?
            GROUP BY f.id, f.plan_name, f.insurer,  
                     f.update_frequency, f.last_updated, f.is_active
        """
        
        cursor = conn.execute(query, (formulary_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Formulary {formulary_id} not found")
        
        formulary = FormularyInfo(
            id=row[0],
            plan_name=row[1],
            insurer=row[2],
            update_frequency=row[3],
            last_updated=row[4],
            is_active=bool(row[5]),
            coverage_count=row[6]
        )
        
        conn.close()
        return formulary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")