from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.db.models import UsageEvent, Subscription, Plan, UsageType, Tenant

class QuotaService:
    @staticmethod
    def get_monthly_usage(db: Session, tenant_id: str, usage_type: UsageType) -> int:
        now = datetime.now(timezone.utc)
        first_day_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        total_usage = db.query(func.coalesce(func.sum(UsageEvent.quantity), 0)).filter(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.usage_type == usage_type,
            UsageEvent.created_at >= first_day_of_month
        ).scalar()

        return int(total_usage)

    @staticmethod
    def check_quota_or_raise(db: Session, tenant_id: str, usage_type: UsageType, requested_quantity: int):
        subscription = db.query(Subscription).filter(
            Subscription.tenant_id == tenant_id
        ).first()

        if not subscription or subscription.status != "active":
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "payment_required",
                    "message": "Tenant does not have an active subscription or payment is required.",
                    "code": 402
                }
            )

        plan = subscription.plan
        current_usage = QuotaService.get_monthly_usage(db, tenant_id, usage_type)

        if usage_type == UsageType.API_CALL:
            limit = plan.max_api_calls_per_month
        else: # AI_TOKENS
            limit = plan.max_tokens_per_month

        # 3. Validação da Fronteira (Boundary Check)
        if current_usage + requested_quantity > limit:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "quota_exceeded",
                    "message": f"Quota limit exceeded for {usage_type.value}. Maximum allowed: {limit}.",
                    "limit": limit,
                    "current_usage": current_usage,
                    "requested": requested_quantity,
                    "code": 429
                }
            )

        return True