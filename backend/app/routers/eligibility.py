"""
Eligibility check endpoints.
Deterministic rule-based engine — no LLM involved.
Results are persisted to eligibility_records table.
"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import EligibilityRecord, FarmerProfile, Scheme
from app.routers.farmers import get_current_farmer
from app.schemas.farmer import EligibilityCheckResponse, CriterionResult
from app.services.eligibility import check_eligibility

router = APIRouter()


@router.post("/check", response_model=List[EligibilityCheckResponse])
def check_farmer_eligibility(
    scheme_ids: List[int],
    current_farmer: Annotated[FarmerProfile, Depends(get_current_farmer)],
    db: Session = Depends(get_db),
) -> List[EligibilityCheckResponse]:
    """
    Check eligibility of the authenticated farmer against one or more schemes.
    Results are persisted — subsequent calls update existing records.
    Maximum 20 schemes per request.
    """
    if len(scheme_ids) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 schemes per eligibility check request",
        )

    if not scheme_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one scheme_id is required",
        )

    responses = []

    for scheme_id in scheme_ids:
        scheme = db.query(Scheme).filter(
            Scheme.id == scheme_id,
            Scheme.is_active == True,
        ).first()

        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme {scheme_id} not found or inactive",
            )

        # Run deterministic eligibility engine
        result = check_eligibility(current_farmer, scheme)

        # Persist result — upsert by farmer_id + scheme_id
        existing = db.query(EligibilityRecord).filter(
            EligibilityRecord.farmer_id == current_farmer.id,
            EligibilityRecord.scheme_id == scheme_id,
        ).first()

        if existing:
            existing.overall_result = result["overall_result"]
            existing.criteria_results = result["criteria_results"]
            existing.summary = result["summary"]
        else:
            record = EligibilityRecord(
                farmer_id=current_farmer.id,
                scheme_id=scheme_id,
                overall_result=result["overall_result"],
                criteria_results=result["criteria_results"],
                summary=result["summary"],
            )
            db.add(record)

        db.commit()

        # Build response
        criteria_results = {
            k: CriterionResult(
                result=v["result"],
                explanation=v["explanation"],
            )
            for k, v in result["criteria_results"].items()
        }

        responses.append(
            EligibilityCheckResponse(
                farmer_id=current_farmer.id,
                scheme_id=scheme_id,
                overall_result=result["overall_result"],
                criteria_results=criteria_results,
                summary=result["summary"],
            )
        )

    return responses


@router.get("/my-results", response_model=List[EligibilityCheckResponse])
def get_my_eligibility_results(
    current_farmer: Annotated[FarmerProfile, Depends(get_current_farmer)],
    db: Session = Depends(get_db),
) -> List[EligibilityCheckResponse]:
    """Get all previously checked eligibility results for the authenticated farmer."""
    records = (
        db.query(EligibilityRecord)
        .filter(EligibilityRecord.farmer_id == current_farmer.id)
        .all()
    )

    responses = []
    for record in records:
        criteria_results = {
            k: CriterionResult(
                result=v["result"],
                explanation=v["explanation"],
            )
            for k, v in (record.criteria_results or {}).items()
        }
        responses.append(
            EligibilityCheckResponse(
                farmer_id=record.farmer_id,
                scheme_id=record.scheme_id,
                overall_result=record.overall_result,
                criteria_results=criteria_results,
                summary=record.summary or "",
            )
        )

    return responses
