from concurrent.futures import ThreadPoolExecutor

import httpx
from a2a.server.agent_execution import RequestContextBuilder
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from a2a.server.events import QueueManager
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import PushNotificationConfigStore, PushNotificationSender, TaskStore
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH, DEFAULT_RPC_URL, EXTENDED_AGENT_CARD_PATH
from fastapi import Depends, FastAPI
from fastapi.applications import AppType
from starlette.middleware.cors import CORSMiddleware
from starlette.types import Lifespan

from beeai_sdk.server.agent import Agent


def create_app(
    agent: Agent,
    task_store: TaskStore | None = None,
    queue_manager: QueueManager | None = None,
    push_config_store: PushNotificationConfigStore | None = None,
    push_sender: PushNotificationSender | None = None,
    request_context_builder: RequestContextBuilder | None = None,
    lifespan: Lifespan[AppType] | None = None,
    dependencies: list[Depends] | None = None,
    **kwargs,
) -> FastAPI:
    executor: ThreadPoolExecutor
    client = httpx.AsyncClient()

    # @asynccontextmanager
    # async def internal_lifespan(app: FastAPI) -> AsyncGenerator[None]:
    #     nonlocal executor
    #     async with client:
    #         with ThreadPoolExecutor() as exec:
    #             executor = exec
    #             if not lifespan:
    #                 yield None
    #             else:
    #                 async with lifespan(app) as state:
    #                     yield state

    app = A2AFastAPIApplication(
        agent_card=agent.card,
        http_handler=DefaultRequestHandler(
            agent_executor=agent.executor,
            task_store=task_store,
            queue_manager=queue_manager,
            push_config_store=push_config_store,
            push_sender=push_sender,
            request_context_builder=request_context_builder,
        ),
    ).build(
        rpc_url=DEFAULT_RPC_URL,
        agent_card_url=AGENT_CARD_WELL_KNOWN_PATH,
        extended_agent_card_url=EXTENDED_AGENT_CARD_PATH,
        lifespan=lifespan,
        dependencies=dependencies,
        **kwargs,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://beeai.dev"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    return app
