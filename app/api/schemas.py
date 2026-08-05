from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class UsageTypeEnum(str, Enum):
    API_CALL = "api_call"
    AI_TOKENS = "ai_tokens"

class TokenBreakdown(BaseModel):
    """
    Details for calculating token cost.
    Rules:
    - Cached input tokens are cheaper
    - Reasoning tokens count as output
    """
    input_tokens: int = Field(default=0, ge=0, description="Default input tokens")
    cached_input_tokens: int = Field(default=0, ge=0, description="Cached input tokens")
    output_tokens: int = Field(default=0, ge=0, description="Default output tokens")
    reasoning_tokens: int = Field(default=0, ge=0, description="Reasoning tokens")

class MeteringRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID consumming the API")
    prompt: Optional[str] = Field(default="Hello world", description="Prompt sent for simulation")
    usage_type: UsageTypeEnum = Field(default=UsageTypeEnum.AI_TOKENS, description="Type of consumed resource")
    
    tokens: Optional[TokenBreakdown] = Field(default_factory=TokenBreakdown)

class MeteringResponse(BaseModel):
    success: bool = True
    message: str
    tenant_id: str
    idempotency_key: str
    recorded_tokens: Optional[TokenBreakdown] = None
    simulated_output: str = "AI completion response simulated."

class QuotaExceededErrorResponse(BaseModel):
    error: str = "Quota Exceeded"
    status_code: int = 429
    detail: str
    current_usage: int
    limit: int

class PaymentRequiredErrorResponse(BaseModel):
    error: str = "Payment Required"
    status_code: int = 402
    detail: str

class UsageQuotaDetail(BaseModel):
    used: int
    limit: int

class UsageSummaryResponse(BaseModel):
    tenant_id: str
    plan_name: str
    status: str
    api_calls: UsageQuotaDetail
    ai_tokens: UsageQuotaDetail
    total_cost_cents: int
    formatted_cost: str