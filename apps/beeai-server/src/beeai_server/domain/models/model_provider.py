# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from beeai_server.utils.utils import utc_now


class ModelProviderType(StrEnum):
    anthropic = "anthropic"
    cerebras = "cerebras"
    chutes = "chutes"
    cohere = "cohere"
    deepseek = "deepseek"
    gemini = "gemini"
    github = "github"
    groq = "groq"
    watsonx = "watsonx"
    jan = "jan"
    mistral = "mistral"
    moonshot = "moonshot"
    nvidia = "nvidia"
    ollama = "ollama"
    openai = "openai"
    openrouter = "openrouter"
    perplexity = "perplexity"
    together = "together"
    rits = "rits"
    other = "other"


class ModelCapability(StrEnum):
    llm = "llm"
    embedding = "embedding"


class ModelProvider(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Human-readable name for the model provider")
    type: ModelProviderType = Field(..., description="Type of model provider")
    base_url: str = Field(..., description="Base URL for the API (unique identifier)")
    created_at: AwareDatetime = Field(default_factory=utc_now)

    # WatsonX specific fields
    watsonx_project_id: str | None = Field(None, description="WatsonX project ID (required for watsonx providers)")
    watsonx_space_id: str | None = Field(None, description="WatsonX space ID (alternative to project ID)")

    # Additional metadata
    description: str | None = Field(None, description="Optional description of the provider")

    @model_validator(mode="after")
    def validate_watsonx_config(self):
        """Validate that watsonx providers have either project_id or space_id."""
        if self.type == ModelProviderType.watsonx and not (bool(self.watsonx_project_id) ^ bool(self.watsonx_space_id)):
            raise ValueError("WatsonX providers must have either watsonx_project_id or watsonx_space_id")
        return self

    @property
    def capabilities(self) -> set[ModelCapability]:
        """Get the capabilities for this provider type."""
        return _PROVIDER_CAPABILITIES.get(self.type, set())

    @property
    def supports_llm(self) -> bool:
        """Check if this provider supports LLM."""
        return ModelCapability.llm in self.capabilities

    @property
    def supports_embedding(self) -> bool:
        """Check if this provider supports embeddings."""
        return ModelCapability.embedding in self.capabilities


# Static mapping of provider types to their capabilities
_PROVIDER_CAPABILITIES: dict[ModelProviderType, set[ModelCapability]] = {
    ModelProviderType.anthropic: {ModelCapability.llm},
    ModelProviderType.cerebras: {ModelCapability.llm},
    ModelProviderType.chutes: {ModelCapability.llm},
    ModelProviderType.cohere: {ModelCapability.llm, ModelCapability.embedding},
    ModelProviderType.deepseek: {ModelCapability.llm},
    ModelProviderType.gemini: {ModelCapability.llm, ModelCapability.embedding},
    ModelProviderType.github: {ModelCapability.llm},
    ModelProviderType.groq: {ModelCapability.llm},
    ModelProviderType.watsonx: {ModelCapability.llm, ModelCapability.embedding},
    ModelProviderType.jan: {ModelCapability.llm},
    ModelProviderType.mistral: {ModelCapability.llm, ModelCapability.embedding},
    ModelProviderType.moonshot: {ModelCapability.llm},
    ModelProviderType.nvidia: {ModelCapability.llm},
    ModelProviderType.ollama: {ModelCapability.llm, ModelCapability.embedding},
    ModelProviderType.openai: {ModelCapability.llm, ModelCapability.embedding},
    ModelProviderType.openrouter: {ModelCapability.llm},
    ModelProviderType.perplexity: {ModelCapability.llm},
    ModelProviderType.together: {ModelCapability.llm},
    ModelProviderType.other: {ModelCapability.llm, ModelCapability.embedding},  # Other can support both
}
