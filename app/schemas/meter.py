from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class UsageType(str, Enum):
    API_CALL = "api_call"
    AI_TOKENS = "ai_tokens"

class TokenBreakdown(BaseModel):
    input_tokens: int = Field(default=0, ge=0, description="Tokens de entrada padrão")
    cached_input_tokens: int = Field(default=0, ge=0, description="Tokens de entrada reaproveitados de cache")
    output_tokens: int = Field(default=0, ge=0, description="Tokens de saída do modelo")
    reasoning_tokens: int = Field(default=0, ge=0, description="Tokens de raciocínio/pensamento")

class BillableRequest(BaseModel):
    tenant_id: str = Field(..., example="tenant_acme", description="ID do cliente")
    usage_type: UsageType = Field(..., description="Tipo de consumo (api_call ou ai_tokens)")
    quantity: int = Field(default=1, ge=1, description="Quantidade consumida (para api_call)")
    tokens: Optional[TokenBreakdown] = Field(default=None, description="Detalhamento de tokens para chamadas de IA")
    prompt: Optional[str] = Field(default="Simulated prompt text", description="Conteúdo simulado")

class BillableResponse(BaseModel):
    success: bool
    message: str
    tenant_id: str
    idempotency_key: str
    event_id: str
    recorded_quantity: int
    is_duplicate: bool = Field(default=False, description="Indica se a requisição foi reconhecida via Idempotency-Key")