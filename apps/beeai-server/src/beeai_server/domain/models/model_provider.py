# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from httpx import AsyncClient
from openai.types import Model
from pydantic import AwareDatetime, BaseModel, Field, HttpUrl, model_validator

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
    voyage = "voyage"
    rits = "rits"
    other = "other"


class ModelCapability(StrEnum):
    llm = "llm"
    embedding = "embedding"


class ModelProvider(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str | None = Field(None, description="Human-readable name for the model provider")
    description: str | None = Field(None, description="Optional description of the provider")

    type: ModelProviderType = Field(..., description="Type of model provider")
    base_url: HttpUrl = Field(..., description="Base URL for the API (unique)")
    created_at: AwareDatetime = Field(default_factory=utc_now)

    # WatsonX specific fields
    watsonx_project_id: str | None = Field(
        None,
        description="WatsonX project ID (required for watsonx providers)",
        exclude=True,
    )
    watsonx_space_id: str | None = Field(
        None,
        description="WatsonX space ID (alternative to project ID)",
        exclude=True,
    )

    @model_validator(mode="after")
    def validate_watsonx_config(self):
        """Validate that watsonx providers have either project_id or space_id."""
        if self.type == ModelProviderType.watsonx and not (bool(self.watsonx_project_id) ^ bool(self.watsonx_space_id)):
            raise ValueError("WatsonX providers must have either watsonx_project_id or watsonx_space_id")
        return self

    @property
    def capabilities(self) -> set[ModelCapability]:
        return _PROVIDER_CAPABILITIES.get(self.type, set())

    async def load_models(self, api_key: str) -> list[Model]:
        async with AsyncClient() as client:
            match self.type:
                case ModelProviderType.watsonx:
                    response = await client.get(f"{self.base_url}/ml/v1/foundation_model_specs?version=2025-08-27")
                    response_models = response.raise_for_status().json()["resources"]
                    available_models = []
                    for model in response_models:
                        events = {e["id"]: e for e in model["lifecycle"]}
                        if "withdrawn" in events:
                            continue
                        if "available" in events:
                            created = int(datetime.fromisoformat(events["available"]["start_date"]).timestamp())
                            available_models.append((model, created))
                    return [
                        Model.model_validate(
                            {
                                **model,
                                "id": f"{self.type}:{model['model_id']}",
                                "created": created,
                                "object": "model",
                                "owned_by": model["provider"],
                            }
                        )
                        for model, created in available_models
                    ]
                case ModelProviderType.voyage:
                    return [
                        Model(
                            id=f"{self.type}:{model_id}",
                            created=int(datetime.now().timestamp()),
                            object="model",
                            owned_by="voyage",
                        )
                        for model_id in {
                            "voyage-3-large",
                            "voyage-3.5",
                            "voyage-3.5-lite",
                            "voyage-code-3",
                            "voyage-finance-2",
                            "voyage-law-2",
                            "voyage-code-2",
                        }
                    ]
                case ModelProviderType.anthropic:
                    response = await client.get(
                        f"{self.base_url}/models", headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"}
                    )
                    models = response.raise_for_status().json()["data"]
                    return [
                        Model(
                            id=f"{self.type}:{model['id']}",
                            created=int(datetime.fromisoformat(model["created_at"]).timestamp()),
                            owned_by="Anthropic",
                            object="model",
                            display_name=model["display_name"],  # pyright: ignore [reportCallIssue]
                        )
                        for model in models
                    ]

                case ModelProviderType.rits:
                    response = await client.get(f"{self.base_url}/models", headers={"RITS_API_KEY": api_key})
                    models = response.raise_for_status().json()["data"]
                    return [Model.model_validate({**model, "id": f"{self.type}:{model['id']}"}) for model in models]
                case _:
                    response = await client.get(
                        f"{self.base_url}/models", headers={"Authorization": f"Bearer {api_key}"}
                    )
                    models = response.raise_for_status().json()["data"]
                    return [Model.model_validate({**model, "id": f"{self.type}:{model['id']}"}) for model in models]

    @property
    def supports_llm(self) -> bool:
        return ModelCapability.llm in self.capabilities

    @property
    def supports_embedding(self) -> bool:
        return ModelCapability.embedding in self.capabilities


class ModelWithScore(BaseModel):
    model_id: str
    score: float


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
    ModelProviderType.voyage: {ModelCapability.embedding},
    ModelProviderType.rits: {ModelCapability.llm},
    ModelProviderType.other: {ModelCapability.llm, ModelCapability.embedding},  # Other can support both
}
