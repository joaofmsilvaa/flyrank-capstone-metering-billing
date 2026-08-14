## METERING & QUOTAS

- [x] A billable action creates exactly one usage event, even under retries.
- [x] A test proves double-counting cannot happen.
- [x] Usage is checked against the tenant's plan; requests over the limit are rejected.
- [x] Responses carry the correct status codes (429/402) and a message explaining why.

### Evidência de Teste Automatizado:
```text
collected 5 items
tests\test_metering.py [ 60%]
tests\test_webhooks.py [100%]