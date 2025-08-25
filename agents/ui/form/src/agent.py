# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os

import a2a.server.agent_execution
import a2a.server.apps
import a2a.server.events
import a2a.server.request_handlers
import a2a.server.tasks
from a2a.types import (
    Message,
)
from a2a.utils.message import get_message_text

from beeai_sdk.server import Server
from beeai_sdk.server.context import RunContext


import beeai_sdk.a2a.extensions
from beeai_sdk.a2a.extensions.services.llm import LLMServiceExtensionServer
from beeai_sdk.a2a.extensions.ui.form import DateField

from beeai_sdk.a2a.extensions.ui.trajectory import TrajectoryExtensionServer, TrajectoryExtensionSpec

agent_detail_extension_spec = beeai_sdk.a2a.extensions.AgentDetailExtensionSpec(
    params=beeai_sdk.a2a.extensions.AgentDetail(
        interaction_mode="single-turn",
    )
)

date_from=DateField(
    type="date",
    id="date",
    label="Date from",
    required=True,
)
date_to=DateField(
    type="date",
    id="date_to",
    label="Date to",
    required=True,
)

form_extension_spec = beeai_sdk.a2a.extensions.FormExtensionSpec(
    params=beeai_sdk.a2a.extensions.FormRender(
        id="xxx",
        title="Text form",
        fields=[date_from, date_to]
    )
)

server = Server()


@server.agent(
    name="Form Agent",
    documentation_url="https://github.com/i-am-bee/beeai-platform/blob/main/agents/official/beeai-framework/chat",
    version="1.0.0",
    default_input_modes=["text", "text/plain"],
    default_output_modes=["text", "text/plain"],
    capabilities=a2a.types.AgentCapabilities(
        streaming=True,
        push_notifications=False,
        state_transition_history=False,
        extensions=[
            *form_extension_spec.to_agent_card_extensions(),
            *agent_detail_extension_spec.to_agent_card_extensions(),
        ],
    ),
    skills=[
        a2a.types.AgentSkill(
            id="form",
            name="Form",
            description="Answer complex questions using web search sources",
            tags=["form"]
        )
    ],
)

async def agent(input: Message, context: RunContext,
):
    """
    The agent is an AI-powered conversational system with memory, supporting real-time search, Wikipedia lookups,
    and weather updates through integrated tools.
    """
    
    hello_template: str = os.getenv("HELLO_TEMPLATE", "Ciao %s!")
    yield a2a.types.AgentMessage(text=hello_template % get_message_text(input))

def serve():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 10000)),
        configure_telemetry=True,
    )


if __name__ == "__main__":
    serve()