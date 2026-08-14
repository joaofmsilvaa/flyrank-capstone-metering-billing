from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.stripe_service import StripeWebhookService

router = APIRouter(tags=["Stripe Webhooks"])

@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db)
):
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    payload = await request.body()

    event = StripeWebhookService.verify_and_construct_event(payload, stripe_signature)

    result = StripeWebhookService.process_event(db=db, event=event)
    return result