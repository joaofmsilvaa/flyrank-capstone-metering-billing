# FlyRank Capstone - Metering & Billing System Evidence

## 1. METERING & QUOTAS
- [x] A billable action creates exactly one usage event, even under retries.
- [x] A test proves double-counting cannot happen.
- [x] Usage is checked against the tenant's plan; requests over the limit are rejected.
- [x] Responses carry the correct status codes (429/402) and a message explaining why.

## 2. STRIPE INTEGRATION & WEBHOOKS
- [x] Stripe webhook endpoint receives and processes customer events.
- [x] Webhook signature verification is active and rejects forged requests (400 Bad Request).
- [x] Event deduplication prevents processing replay webhooks twice.
- [x] Successful subscription upgrades correctly transition tenants from FREE to PRO.

## 3. CONSUMPTION SUMMARY
- [x] Endpoint `GET /api/v1/usage/{tenant_id}` aggregates current month usage.
- [x] Correct percentage calculations for API calls and AI tokens.

---

### 🧪 Execução dos Testes Automatizados (`python -m pytest`)

```text
============================= test session starts =============================
platform win32 -- Python 3.14.x, pytest-9.x, pluggy-1.x
rootdir: C:\Users\joaoy\Desktop\projetos\flyrank-capstone-metering-billing
collected 6 items

tests\test_metering.py ....                                            [ 66%]
tests\test_webhooks.py ..                                              [100%]

============================== 6 passed in 1.85s ==============================