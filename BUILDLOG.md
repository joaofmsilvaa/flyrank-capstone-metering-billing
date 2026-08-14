### 📝 Atualizar o `BUILDLOG.md`

Garante que o arquivo `BUILDLOG.md` registre os passos seguidos no projeto:

```markdown
# Build Log

## Phase 1: Database & Seed
- Configured PostgreSQL connection and SQLAlchemy models (`Tenant`, `Plan`, `Subscription`, `UsageEvent`, `ProcessedWebhook`).
- Created idempotent database seed (`python -m app.db.seed`) for `FREE` and `PRO` plans and initial tenants (`tenant_acme`, `tenant_globex`).

## Phase 2: Metering Service & Idempotency
- Implemented `POST /api/v1/generate` endpoint consuming `Idempotency-Key` header.
- Guarded against double-counting and enforced plan boundaries with standard `429` (Quota Exceeded) and `402` (Payment Required) status codes.

## Phase 3: Stripe Integration & Webhook Handler
- Configured Stripe Test Mode integration.
- Built `/webhooks/stripe` with cryptographic signature validation (`Stripe-Signature`).
- Handled webhook replay protection via `processed_webhooks` table.

## Phase 4: Usage Summary
- Created `GET /api/v1/usage/{tenant_id}` to compute real-time monthly usage metrics and percentages against plan quotas.