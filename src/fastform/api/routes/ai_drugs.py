from typing import List, Optional
import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from openai import OpenAI

from fastform.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class IntelligentDrugSearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

class DrugMatchResult(BaseModel):
    id: int
    name: str
    dosage_form: str | None = None
    strength_qty: float | None = None
    strength_unit: str | None = None
    route: str | None = None
    generic_name: str | None = None
    brand_name: str | None = None
    ndc: str | None = None
    formulary_tier: int | None = None
    prior_authorization: bool = False
    quantity_limit: bool = False
    step_therapy: bool = False
    match_confidence: float = 0.0
    match_reason: str = ""

@router.post("/intelligent-search", response_model=List[DrugMatchResult])
async def intelligent_drug_search(request: IntelligentDrugSearchRequest):
    """
    Intelligent drug search using OpenAI to handle typos, brand/generic variations,
    and provide context-aware matching with explanations.
    """
    if not request.query.strip():
        return []
    
    if not settings.openai_key_found:
        raise HTTPException(
            status_code=503, 
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Get all drugs from the database for analysis
        conn = sqlite3.connect(settings.db_path)
        conn.row_factory = sqlite3.Row
        
        drug_query = """
        SELECT id, name, dosage_form, strength_qty, strength_unit, route,
               generic_name, brand_name, ndc, formulary_tier,
               prior_authorization, quantity_limit, step_therapy
        FROM drug_rules 
        ORDER BY formulary_tier, name
        LIMIT 50
        """
        
        cursor = conn.execute(drug_query)
        all_drugs = cursor.fetchall()
        conn.close()
        
        # Create drug list for OpenAI analysis
        drug_list = []
        for drug in all_drugs:
            drug_info = f"{drug['name']}"
            if drug['generic_name'] and drug['generic_name'] != drug['name']:
                drug_info += f" ({drug['generic_name']})"
            if drug['brand_name']:
                drug_info += f" - {drug['brand_name']}"
            drug_list.append(drug_info)
        
        drug_names = "\\n".join(drug_list)
        
        # Create OpenAI prompt for intelligent matching
        prompt = f"""You are a pharmaceutical expert. Given this user query: "{request.query}"

Find the best matching medications from this formulary list:
{drug_names}

Return a JSON array of the top 5 matches with this exact format:
[
  {{"medication_name": "Exact name from list", "confidence": 0.95, "reason": "Exact match"}},
  {{"medication_name": "Another name", "confidence": 0.80, "reason": "Spelling correction"}}
]

Handle common issues:
- Misspellings (ibuprofin -> Ibuprofen)  
- Brand/generic (Advil -> Ibuprofen)
- Abbreviations (APAP -> Acetaminophen)
- Partial matches (metfor -> Metformin)

Only include matches with confidence >= 0.5. Return empty array if no good matches."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a pharmaceutical expert. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse OpenAI response
        import json
        try:
            matches = json.loads(ai_response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse OpenAI response: {ai_response}")
            matches = []
        
        # Match AI suggestions to actual database records
        results = []
        for match in matches:
            medication_name = match.get('medication_name', '').lower()
            confidence = float(match.get('confidence', 0.0))
            reason = match.get('reason', 'AI suggested match')
            
            # Find matching drugs in database
            for drug_row in all_drugs:
                if (drug_row['name'].lower() in medication_name or 
                    medication_name in drug_row['name'].lower()):
                    
                    result = DrugMatchResult(
                        **dict(drug_row),
                        match_confidence=confidence,
                        match_reason=reason
                    )
                    results.append(result)
                    break
        
        # Remove duplicates and sort by confidence
        seen_ids = set()
        unique_results = []
        for result in sorted(results, key=lambda x: x.match_confidence, reverse=True):
            if result.id not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result.id)
        
        return unique_results[:request.max_results]
        
    except Exception as e:
        logger.error(f"Error in intelligent search: {str(e)}")
        if "openai" in str(e).lower() or "api" in str(e).lower():
            raise HTTPException(status_code=503, detail=f"OpenAI service error: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
