import stripe
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.config import settings
from app.db.models import Subscription, Plan, PlanType, ProcessedWebhook, Tenant

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeWebhookService:
    @staticmethod
    def verify_and_construct_event(payload: bytes, sig_header: str):
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")

    @staticmethod
    def process_event(db: Session, event) -> dict:
        if hasattr(event, "to_dict"):
            event = event.to_dict()

        event_id = event["id"]
        event_type = event["type"]

        already_processed = db.query(ProcessedWebhook).filter_by(event_id=event_id).first()
        if already_processed:
            return {"status": "ignored", "reason": "Event already processed"}

        if event_type in ["checkout.session.completed", "customer.subscription.updated"]:
            data = event.get("data", {}).get("object", {})
            stripe_customer_id = data.get("customer")
            stripe_sub_id = data.get("subscription") or data.get("id")
            
            tenant_id = data.get("client_reference_id") or data.get("metadata", {}).get("tenant_id")

            if tenant_id:
                sub = db.query(Subscription).filter_by(tenant_id=tenant_id).first()
                plan_pro = db.query(Plan).filter_by(name=PlanType.PRO).first()

                if sub and plan_pro:
                    sub.plan_id = plan_pro.id
                    sub.stripe_customer_id = stripe_customer_id
                    sub.stripe_subscription_id = stripe_sub_id
                    sub.status = "active"

        elif event_type == "customer.subscription.deleted":
            data = event.get("data", {}).get("object", {})
            stripe_sub_id = data.get("id")
            
            sub = db.query(Subscription).filter_by(stripe_subscription_id=stripe_sub_id).first()
            plan_free = db.query(Plan).filter_by(name=PlanType.FREE).first()

            if sub and plan_free:
                sub.plan_id = plan_free.id
                sub.status = "canceled"

        db.add(ProcessedWebhook(event_id=event_id, event_type=event_type))
        db.commit()

        return {"status": "success", "event_type": event_type}