from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.meter import BillableRequest, BillableResponse
from app.services.meter_service import MeterService

router = APIRouter(prefix="/api/v1", tags=["Metering"])

@router.post("/generate", response_model=BillableResponse)
def generate_billable_action(
    request: BillableRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="Chave única de idempotência"),
    db: Session = Depends(get_db)
):
    if not idempotency_key.strip():
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required.")

    return MeterService.record_usage(db=db, request=request, idempotency_key=idempotency_key)