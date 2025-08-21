# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from pydantic import AwareDatetime, BaseModel, Field

from beeai_server.utils.utils import utc_now


class SystemConfiguration(BaseModel):
    """Global system configuration that can be updated by administrators."""

    default_llm_model: str | None = Field(None, description="Default LLM model (e.g., 'openai/gpt-4o')")
    default_embedding_model: str | None = Field(
        None, description="Default embedding model (e.g., 'openai/text-embedding-3-small')"
    )

    # Metadata
    updated_at: AwareDatetime = Field(default_factory=utc_now, description="When this configuration was last updated")

    @property
    def has_defaults_configured(self) -> bool:
        """Check if both default models are configured."""
        return bool(self.default_llm_model and self.default_embedding_model)
