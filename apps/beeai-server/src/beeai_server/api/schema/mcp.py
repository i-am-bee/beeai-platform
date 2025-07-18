# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime

from pydantic import AnyUrl, BaseModel

from beeai_server.domain.models.mcp_provider import McpProviderDeploymentState, McpProviderLocation


class CreateMcpProviderRequest(BaseModel):
    name: str
    location: McpProviderLocation


class McpProvider(BaseModel):
    id: str
    name: str
    location: McpProviderLocation
    state: McpProviderDeploymentState


class Tool(BaseModel):
    id: str
    name: str
    description: str | None = None


class CreateToolkitRequest(BaseModel):
    tools: list[str]


class Toolkit(BaseModel):
    id: str
    url: AnyUrl
    expires_at: datetime
