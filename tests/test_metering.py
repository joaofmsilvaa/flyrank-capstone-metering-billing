import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import Tenant, Subscription, Plan, PlanType, UsageEvent

def test_idempotent_metering(client: TestClient):
    unique_key = f"key_{uuid.uuid4().hex}"
    payload = {
        "tenant_id": "tenant_acme",
        "usage_type": "api_call",
        "quantity": 5
    }
    headers = {"Idempotency-Key": unique_key}

    response_1 = client.post("/api/v1/generate", json=payload, headers=headers)
    assert response_1.status_code == 200
    data_1 = response_1.json()
    assert data_1["success"] is True
    assert data_1["is_duplicate"] is False
    assert data_1["recorded_quantity"] == 5

    response_2 = client.post("/api/v1/generate", json=payload, headers=headers)
    assert response_2.status_code == 200
    data_2 = response_2.json()
    assert data_2["success"] is True
    assert data_2["is_duplicate"] is True
    assert data_2["event_id"] == data_1["event_id"]


def test_quota_exceeded_returns_429(client: TestClient, db_session: Session):
    tenant_id = f"tenant_limit_{uuid.uuid4().hex[:6]}"
    tenant = Tenant(id=tenant_id, name="Limit Test Corp")
    db_session.add(tenant)

    plan_free = db_session.query(Plan).filter_by(name=PlanType.FREE).first()
    sub = Subscription(id=f"sub_{tenant_id}", tenant_id=tenant_id, plan_id=plan_free.id, status="active")
    db_session.add(sub)
    db_session.commit()

    event = UsageEvent(
        id=f"evt_{uuid.uuid4().hex[:8]}",
        tenant_id=tenant_id,
        usage_type="api_call",
        quantity=1000,
        idempotency_key=f"fill_{uuid.uuid4().hex}"
    )
    db_session.add(event)
    db_session.commit()

    response = client.post(
        "/api/v1/generate",
        json={"tenant_id": tenant_id, "usage_type": "api_call", "quantity": 1},
        headers={"Idempotency-Key": f"key_over_{uuid.uuid4().hex}"}
    )

    assert response.status_code == 429
    error_data = response.json()["detail"]
    assert error_data["error"] == "quota_exceeded"
    assert error_data["limit"] == 1000
    assert error_data["current_usage"] == 1000


def test_inactive_subscription_returns_402(client: TestClient, db_session: Session):
    tenant_id = f"tenant_canceled_{uuid.uuid4().hex[:6]}"
    tenant = Tenant(id=tenant_id, name="Canceled Corp")
    db_session.add(tenant)

    plan_free = db_session.query(Plan).filter_by(name=PlanType.FREE).first()
    sub = Subscription(id=f"sub_{tenant_id}", tenant_id=tenant_id, plan_id=plan_free.id, status="canceled")
    db_session.add(sub)
    db_session.commit()

    response = client.post(
        "/api/v1/generate",
        json={"tenant_id": tenant_id, "usage_type": "api_call", "quantity": 1},
        headers={"Idempotency-Key": f"key_{uuid.uuid4().hex}"}
    )

    assert response.status_code == 402
    assert response.json()["detail"]["error"] == "payment_required"

def test_get_tenant_usage_summary(client: TestClient):
    response = client.get("/api/v1/usage/tenant_acme")
    assert response.status_code == 200
    data = response.json()
    
    assert data["tenant_id"] == "tenant_acme"
    assert "api_calls" in data
    assert "ai_tokens" in data
    assert "percentage" in data["api_calls"]