# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import fastapi

from beeai_server.api.routes.dependencies import EnvServiceDependency, AdminAuthDependency
from beeai_server.api.schema.env import UpdateVariablesRequest, ListVariablesSchema

router = fastapi.APIRouter()


@router.put("", status_code=fastapi.status.HTTP_201_CREATED)
async def update_variables(
    request: UpdateVariablesRequest, env_service: EnvServiceDependency, _: AdminAuthDependency
) -> None:
    await env_service.update_env(env=request.env)


@router.get("")
async def list_variables(env_service: EnvServiceDependency, _: AdminAuthDependency) -> ListVariablesSchema:
    return ListVariablesSchema(env=await env_service.list_env())
