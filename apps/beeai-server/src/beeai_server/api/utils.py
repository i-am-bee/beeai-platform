# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import fastapi

from beeai_server.service_layer.services.acp import AcpServerResponse
from beeai_server.service_layer.services.mcp import McpServerResponse


def to_fastapi(response: AcpServerResponse | McpServerResponse):
    common = {"status_code": response.status_code, "headers": response.headers, "media_type": response.media_type}
    if response.stream:
        return fastapi.responses.StreamingResponse(content=response.stream, **common)
    else:
        return fastapi.responses.Response(content=response.content, **common)
