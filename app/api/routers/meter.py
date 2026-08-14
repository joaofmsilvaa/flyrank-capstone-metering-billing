from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.meter import BillableRequest, BillableResponse
from app.services.meter_service import MeterService

from datetime import datetime, timezone
from sqlalchemy import func
from app.db.models import UsageEvent, Subscription, UsageType, Tenant
from app.schemas.meter import UsageSummaryResponse

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

@router.get("/usage/{tenant_id}", response_model=UsageSummaryResponse)
def get_tenant_usage(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found.")

    subscription = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail=f"No subscription found for tenant '{tenant_id}'.")

    plan = subscription.plan
    now = datetime.now(timezone.utc)
    first_day_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    api_usage = db.query(func.coalesce(func.sum(UsageEvent.quantity), 0)).filter(
        UsageEvent.tenant_id == tenant_id,
        UsageEvent.usage_type == UsageType.API_CALL,
        UsageEvent.created_at >= first_day_of_month
    ).scalar()

    token_usage = db.query(func.coalesce(func.sum(UsageEvent.quantity), 0)).filter(
        UsageEvent.tenant_id == tenant_id,
        UsageEvent.usage_type == UsageType.AI_TOKENS,
        UsageEvent.created_at >= first_day_of_month
    ).scalar()

    api_used = int(api_usage)
    tokens_used = int(token_usage)

    api_pct = round((api_used / plan.max_api_calls_per_month) * 100, 2) if plan.max_api_calls_per_month > 0 else 0.0
    tokens_pct = round((tokens_used / plan.max_tokens_per_month) * 100, 2) if plan.max_tokens_per_month > 0 else 0.0

    return UsageSummaryResponse(
        tenant_id=tenant_id,
        plan_name=plan.name.value,
        period=now.strftime("%Y-%m"),
        api_calls={
            "used": api_used,
            "limit": plan.max_api_calls_per_month,
            "percentage": api_pct
        },
        ai_tokens={
            "used": tokens_used,
            "limit": plan.max_tokens_per_month,
            "percentage": tokens_pct
        }
    )