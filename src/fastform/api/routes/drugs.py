from typing import List, Optional
import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from fastform.settings import settings

router = APIRouter()

class DrugSearchRequest(BaseModel):
    query: str
    limit: int = 50
    formulary_id: Optional[int] = None

class DrugItem(BaseModel):
    id: int
    name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    ndc: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    formulary_tier: Optional[int] = None
    prior_authorization: bool = False
    quantity_limit: bool = False
    step_therapy: bool = False
    formulary_name: Optional[str] = None
    insurer: Optional[str] = None

@router.post("/search", response_model=List[DrugItem])
async def search_drugs(request: DrugSearchRequest):
    """
    Search for drugs with enhanced multi-field matching and optional formulary filtering.
    """
    if not request.query.strip():
        return []
    
    try:
        conn = sqlite3.connect(settings.db_path)
        
        # Clean search query
        clean_query = ' '.join(request.query.lower().strip().split())
        
        # Build formulary filter
        formulary_filter = ""
        params = []
        
        if request.formulary_id:
            formulary_filter = "AND fc.formulary_id = ?"
            params.append(request.formulary_id)
        
        # Query with correct column names
        search_query = f"""
            SELECT DISTINCT
                d.id,
                d.name,
                d.generic_name,
                d.brand_name,
                d.ndc,
                CASE 
                    WHEN d.strength_qty IS NOT NULL AND d.strength_unit IS NOT NULL 
                    THEN CAST(d.strength_qty AS TEXT) || d.strength_unit
                    WHEN d.strength_qty IS NOT NULL 
                    THEN CAST(d.strength_qty AS TEXT)
                    ELSE d.strength_unit
                END as strength,
                d.dosage_form,
                fc.formulary_tier,
                fc.prior_authorization,
                fc.quantity_limit,
                fc.step_therapy,
                f.plan_name as formulary_name,
                f.insurer
            FROM drugs d
            JOIN formulary_coverage fc ON d.id = fc.drug_id
            JOIN formularies f ON fc.formulary_id = f.id
            WHERE f.is_active = 1
            {formulary_filter}
            AND (
                LOWER(REPLACE(d.name, ' ', '')) LIKE LOWER(REPLACE(?, ' ', '')) OR
                LOWER(REPLACE(d.generic_name, ' ', '')) LIKE LOWER(REPLACE(?, ' ', '')) OR
                LOWER(REPLACE(d.brand_name, ' ', '')) LIKE LOWER(REPLACE(?, ' ', '')) OR
                LOWER(d.ndc) LIKE LOWER(?) OR
                LOWER(d.name) LIKE LOWER(?) OR
                LOWER(d.generic_name) LIKE LOWER(?) OR
                LOWER(d.brand_name) LIKE LOWER(?)
            )
            ORDER BY 
                CASE 
                    WHEN LOWER(d.name) = LOWER(?) THEN 1
                    WHEN LOWER(d.generic_name) = LOWER(?) THEN 2
                    WHEN LOWER(d.brand_name) = LOWER(?) THEN 3
                    ELSE 4
                END,
                d.name
            LIMIT ?
        """
        
        # Prepare search parameters
        like_pattern = f"%{clean_query}%"
        params.extend([
            like_pattern, like_pattern, like_pattern,
            like_pattern,
            like_pattern, like_pattern, like_pattern,
            request.query, request.query, request.query,
            request.limit
        ])
        
        cursor = conn.execute(search_query, params)
        results = []
        
        for row in cursor.fetchall():
            drug = DrugItem(
                id=row[0],
                name=row[1],
                generic_name=row[2],
                brand_name=row[3],
                ndc=row[4],
                strength=row[5],
                dosage_form=row[6],
                formulary_tier=row[7],
                prior_authorization=bool(row[8]),
                quantity_limit=bool(row[9]) if row[9] is not None else False,
                step_therapy=bool(row[10]),
                formulary_name=row[11],
                insurer=row[12]
            )
            results.append(drug)
        
        conn.close()
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
