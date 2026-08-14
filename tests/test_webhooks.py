import time
import json
import stripe
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Subscription, Plan, PlanType, Tenant

def generate_stripe_signature(payload: str, secret: str) -> str:
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload}"
    signature = stripe.WebhookSignature._compute_signature(signed_payload, secret)
    return f"t={timestamp},v1={signature}"


def test_forged_webhook_returns_400(client: TestClient):
    payload = {"id": "evt_fake_123", "object": "event", "type": "checkout.session.completed"}
    headers = {"Stripe-Signature": "t=123456,v1=bad_signature_hash"}

    response = client.post("/webhooks/stripe", json=payload, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"


def test_stripe_webhook_upgrade_tenant_to_pro(client: TestClient, db_session: Session):
    sub = db_session.query(Subscription).filter_by(tenant_id="tenant_acme").first()
    plan_free = db_session.query(Plan).filter_by(name=PlanType.FREE).first()
    sub.plan_id = plan_free.id
    db_session.commit()

    event_id = f"evt_test_{int(time.time())}"
    payload_dict = {
        "id": event_id,
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "object": "checkout.session",
                "customer": "cus_test_acme_123",
                "subscription": "sub_stripe_pro_123",
                "client_reference_id": "tenant_acme"
            }
        }
    }
    payload_str = json.dumps(payload_dict)
    
    test_secret = "whsec_test_secret_for_pytest"
    settings.STRIPE_WEBHOOK_SECRET = test_secret

    headers = {
        "Stripe-Signature": generate_stripe_signature(payload_str, test_secret)
    }

    response_1 = client.post("/webhooks/stripe", content=payload_str, headers=headers)
    assert response_1.status_code == 200
    assert response_1.json()["status"] == "success"

    db_session.refresh(sub)
    plan_pro = db_session.query(Plan).filter_by(name=PlanType.PRO).first()
    assert sub.plan_id == plan_pro.id
    assert sub.stripe_customer_id == "cus_test_acme_123"

    response_2 = client.post("/webhooks/stripe", content=payload_str, headers=headers)
    assert response_2.status_code == 200
    assert response_2.json()["status"] == "ignored"
    assert response_2.json()["reason"] == "Event already processed"