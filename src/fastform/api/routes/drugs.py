import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from fastform.settings import settings

router = APIRouter()


class DrugSearchRequest(BaseModel):
    query: str
    limit: int = 50
    formulary_id: int | None = None


class DrugItem(BaseModel):
    id: int
    name: str
    generic_name: str | None = None
    brand_name: str | None = None
    ndc: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    formulary_tier: int | None = None
    prior_authorization: bool = False
    quantity_limit: bool = False
    step_therapy: bool = False
    formulary_name: str | None = None
    insurer: str | None = None


@router.post("/search", response_model=list[DrugItem])
async def search_drugs(request: DrugSearchRequest):
    """
    Search for drugs with enhanced multi-field matching and optional formulary filtering.
    """
    if not request.query.strip():
        return []

    try:
        conn = sqlite3.connect(settings.db_path)

        # Clean search query
        clean_query = " ".join(request.query.lower().strip().split())

        # Query the drug_rules table (current schema)
        search_query = """
            SELECT DISTINCT
                id,
                name,
                generic_name,
                brand_name,
                ndc,
                CASE 
                    WHEN strength_qty IS NOT NULL AND strength_unit IS NOT NULL
                    THEN CAST(strength_qty AS TEXT) || strength_unit
                    WHEN strength_qty IS NOT NULL 
                    THEN CAST(strength_qty AS TEXT)
                    ELSE strength_unit
                END as strength,
                dosage_form,
                formulary_tier,
                prior_authorization,
                quantity_limit,
                step_therapy,
                'Medicare Part D' as formulary_name,
                'CMS' as insurer
            FROM drug_rules
            WHERE 
                LOWER(REPLACE(name, ' ', '')) LIKE LOWER(REPLACE(?, ' ', '')) OR
                LOWER(REPLACE(generic_name, ' ', '')) LIKE LOWER(REPLACE(?, ' ', '')) OR
                LOWER(REPLACE(brand_name, ' ', '')) LIKE LOWER(REPLACE(?, ' ', '')) OR
                LOWER(ndc) LIKE LOWER(?) OR
                LOWER(name) LIKE LOWER(?) OR
                LOWER(generic_name) LIKE LOWER(?) OR
                LOWER(brand_name) LIKE LOWER(?)
            ORDER BY 
                CASE 
                    WHEN LOWER(name) = LOWER(?) THEN 1
                    WHEN LOWER(generic_name) = LOWER(?) THEN 2
                    WHEN LOWER(brand_name) = LOWER(?) THEN 3
                    ELSE 4
                END,
                name
            LIMIT ?
        """

        params = [
            f"%{clean_query}%",  # name
            f"%{clean_query}%",  # generic_name
            f"%{clean_query}%",  # brand_name
            f"%{clean_query}%",  # ndc
            f"%{request.query}%",  # name exact
            f"%{request.query}%",  # generic_name exact
            f"%{request.query}%",  # brand_name exact
            f"%{request.query}%",  # name priority
            f"%{request.query}%",  # generic_name priority
            f"%{request.query}%",  # brand_name priority
            request.limit,
        ]

        cursor = conn.execute(search_query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(
                DrugItem(
                    id=row[0],
                    name=row[1],
                    generic_name=row[2],
                    brand_name=row[3],
                    ndc=row[4],
                    strength=row[5],
                    dosage_form=row[6],
                    formulary_tier=row[7],
                    prior_authorization=bool(row[8]),
                    quantity_limit=bool(row[9]),
                    step_therapy=bool(row[10]),
                    formulary_name=row[11],
                    insurer=row[12],
                )
            )

        conn.close()
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e
