from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class UsageType(str, Enum):
    API_CALL = "api_call"
    AI_TOKENS = "ai_tokens"

class TokenBreakdown(BaseModel):
    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)

class BillableRequest(BaseModel):
    tenant_id: str = Field(..., json_schema_extra={"example": "tenant_acme"}, description="Client id")
    usage_type: UsageType = Field(..., description="Usage type (api_call or ai_tokens)")
    quantity: int = Field(default=1, ge=1, description="Used quantity (para api_call)")
    tokens: Optional[TokenBreakdown] = Field(default=None, description="Tokens per API call")
    prompt: Optional[str] = Field(default="Simulated prompt text", description="Simulated content")

class BillableResponse(BaseModel):
    success: bool
    message: str
    tenant_id: str
    idempotency_key: str
    event_id: str
    recorded_quantity: int
    is_duplicate: bool = Field(default=False, description="Indica se a requisição foi reconhecida via Idempotency-Key")

class UsageSummaryResponse(BaseModel):
    tenant_id: str
    plan_name: str
    period: str
    api_calls: dict
    ai_tokens: dict