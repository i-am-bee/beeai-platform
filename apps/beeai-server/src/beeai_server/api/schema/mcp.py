# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Optional
from pydantic import AnyUrl, BaseModel

from beeai_server.domain.models.gateway import GatewayLocation


class CreateServerRequest(BaseModel):
    location: GatewayLocation


class Server(BaseModel):
    id: str
    location: GatewayLocation


class Tool(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


class CreateToolkitRequest(BaseModel):
    tools: list[str]


class Toolkit(BaseModel):
    id: str
    name: str
    description: Optional[str]
    tools: list[str]
    mcp_url: AnyUrl
