# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from beeai_server.api.schema.mcp import CreateServerRequest, CreateToolkitRequest, Server, Tool, Toolkit
import fastapi

from beeai_server.api.dependencies import AdminUserDependency, AuthenticatedUserDependency, McpProxyServiceDependency
from beeai_server.service_layer.services.mcp import McpServerResponse

router = fastapi.APIRouter()


def _to_fastapi(response: McpServerResponse):
    common = {"status_code": response.status_code, "headers": response.headers, "media_type": response.media_type}
    if response.stream:
        return fastapi.responses.StreamingResponse(content=response.stream, **common)
    else:
        return fastapi.responses.Response(content=response.content, **common)


@router.post("/servers", response_model=Server)
async def create_server(
    request: CreateServerRequest,
    mcp_service: McpProxyServiceDependency,
    _: AdminUserDependency,
):
    server = await mcp_service.create_server(location=request.location)
    return server


@router.get("/servers", response_model=list[Server])
async def list_servers(mcp_service: McpProxyServiceDependency, _: AdminUserDependency):
    servers = await mcp_service.list_servers()
    return servers


@router.delete("/servers/{server_id}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
async def delete_server(server_id: str, mcp_service: McpProxyServiceDependency, _: AdminUserDependency):
    await mcp_service.delete_server(server_id=server_id)


@router.get("/tools", response_model=list[Tool])
async def list_tools(mcp_service: McpProxyServiceDependency):
    tools = await mcp_service.list_tools()
    return tools


@router.post("/toolkits", response_model=Toolkit)
async def create_toolkit(request: CreateToolkitRequest, mcp_service: McpProxyServiceDependency):
    toolkit = await mcp_service.create_toolkit(tools=request.tools)
    return toolkit


@router.post("/toolkit/{toolkit_id}/mcp")
@router.get("/toolkit/{toolkit_id}/mcp")
async def mcp(
    toolkit_id: str, request: fastapi.Request, mcp_service: McpProxyServiceDependency, user: AuthenticatedUserDependency
) -> None:
    context = await mcp_service.get_proxy_context(user=user)
    response = await mcp_service.send_request(context, request.method, f"/servers/{toolkit_id}/mcp")
    return _to_fastapi(response)
