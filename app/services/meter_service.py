import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import UsageEvent, UsageType, Tenant
from app.schemas.meter import BillableRequest, BillableResponse
from app.services.quota_service import QuotaService
from fastapi import HTTPException

class MeterService:
    @staticmethod
    def record_usage(db: Session, request: BillableRequest, idempotency_key: str) -> BillableResponse:
        tenant = db.query(Tenant).filter(Tenant.id == request.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant '{request.tenant_id}' not found.")

        existing_event = db.query(UsageEvent).filter(
            UsageEvent.tenant_id == request.tenant_id,
            UsageEvent.idempotency_key == idempotency_key
        ).first()

        if existing_event:
            return BillableResponse(
                success=True,
                message="Event previously recorded (idempotent replay).",
                tenant_id=existing_event.tenant_id,
                idempotency_key=idempotency_key,
                event_id=existing_event.id,
                recorded_quantity=existing_event.quantity,
                is_duplicate=True
            )

        if request.usage_type == UsageType.API_CALL:
            quantity = request.quantity
        else: # AI_TOKENS
            tokens = request.tokens
            quantity = (
                tokens.input_tokens +
                tokens.cached_input_tokens +
                tokens.output_tokens +
                tokens.reasoning_tokens
            ) if tokens else 0

        QuotaService.check_quota_or_raise(db, request.tenant_id, request.usage_type, quantity)

        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        new_event = UsageEvent(
            id=event_id,
            tenant_id=request.tenant_id,
            usage_type=request.usage_type,
            quantity=quantity,
            idempotency_key=idempotency_key
        )

        try:
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
        except IntegrityError:
            db.rollback()
            existing_event = db.query(UsageEvent).filter(
                UsageEvent.tenant_id == request.tenant_id,
                UsageEvent.idempotency_key == idempotency_key
            ).first()
            return BillableResponse(
                success=True,
                message="Event previously recorded (concurrent request).",
                tenant_id=existing_event.tenant_id,
                idempotency_key=idempotency_key,
                event_id=existing_event.id,
                recorded_quantity=existing_event.quantity,
                is_duplicate=True
            )

        return BillableResponse(
            success=True,
            message="Usage successfully recorded.",
            tenant_id=request.tenant_id,
            idempotency_key=idempotency_key,
            event_id=event_id,
            recorded_quantity=quantity,
            is_duplicate=False
        )