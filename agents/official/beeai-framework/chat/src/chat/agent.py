# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os

from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.events import RequirementAgentStartEvent, RequirementAgentSuccessEvent
from beeai_framework.agents.experimental.requirements.conditional import (
    ConditionalRequirement,
)
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.tools.think import ThinkTool
from chat.tools.file_reader import FileReaderTool
from chat.utils.files import extract_files
from opentelemetry.propagate import extract
from requests import api

# os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:6006")
# os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import logging
from collections.abc import AsyncGenerator
from textwrap import dedent

import beeai_framework
from acp_sdk import AnyModel, GenericEvent, Message, Metadata, Link, LinkType, Annotations
from acp_sdk.models import MessagePart
from acp_sdk.server import Context, Server
from acp_sdk.models.platform import PlatformUIAnnotation, PlatformUIType, AgentToolInfo

from beeai_framework.agents.react import ReActAgentUpdateEvent
from beeai_framework.backend import AssistantMessage, UserMessage
from beeai_framework.backend.chat import ChatModel, ChatModelParameters
from beeai_framework.memory import UnconstrainedMemory
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.tool import AnyTool
from beeai_framework.tools.weather.openmeteo import OpenMeteoTool
from pydantic import AnyUrl
from openinference.instrumentation.beeai import BeeAIInstrumentor

BeeAIInstrumentor().instrument()
## TODO: https://github.com/phoenixframework/phoenix/issues/6224
logging.getLogger("opentelemetry.exporter.otlp.proto.http._log_exporter").setLevel(
    logging.CRITICAL
)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.metric_exporter").setLevel(
    logging.CRITICAL
)

server = Server()


def to_framework_message(role: str, content: str) -> beeai_framework.backend.Message:
    match role:
        case "user":
            return UserMessage(content)
        case _:
            return AssistantMessage(content)


@server.agent(
    metadata=Metadata(
        annotations=Annotations(
            beeai_ui=PlatformUIAnnotation(
                ui_type=PlatformUIType.CHAT,
                user_greeting="How can I help you?",
                display_name="Chat NEW",
                tools=[
                    AgentToolInfo(
                        name="Web Search (DuckDuckGo)",
                        description="Retrieves real-time search results.",
                    ),
                    AgentToolInfo(
                        name="Wikipedia Search",
                        description="Fetches summaries from Wikipedia.",
                    ),
                    AgentToolInfo(
                        name="Weather Information (OpenMeteo)",
                        description="Provides real-time weather updates.",
                    ),
                ],
            ),
        ),
        programming_language="Python",
        links=[
            Link(
                type=LinkType.SOURCE_CODE,
                url=AnyUrl(
                    f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
                    "/agents/official/beeai-framework/chat"
                ),
            )
        ],
        license="Apache 2.0",
        framework="BeeAI",
        documentation=dedent(
            """\
            The agent is an AI-powered conversational system designed to process user messages, maintain context,
            and generate intelligent responses. Built on the **BeeAI framework**, it leverages memory and external 
            tools to enhance interactions. It supports real-time web search, Wikipedia lookups, and weather updates,
            making it a versatile assistant for various applications.

            ## How It Works
            The agent processes incoming messages and maintains a conversation history using an **unconstrained 
            memory module**. It utilizes a language model (\`CHAT_MODEL\`) to generate responses and can optionally 
            integrate external tools for additional functionality.

            It supports:
            - **Web Search (DuckDuckGo)** – Retrieves real-time search results.
            - **Wikipedia Search** – Fetches summaries from Wikipedia.
            - **Weather Information (OpenMeteo)** – Provides real-time weather updates.

            The agent also includes an **event-based streaming mechanism**, allowing it to send partial responses
            to clients as they are generated.

            ## Key Features
            - **Conversational AI** – Handles multi-turn conversations with memory.
                - **Tool Integration** – Supports real-time search, Wikipedia lookups, and weather updates.
            - **Event-Based Streaming** – Can send partial updates to clients as responses are generated.
            - **Customizable Configuration** – Users can enable or disable specific tools for enhanced responses.
            """
        ),
        use_cases=[
            "**Chatbots** – Can be used in AI-powered chat applications with memory.",
            "**Research Assistance** – Retrieves relevant information from web search and Wikipedia.",
            "**Weather Inquiries** – Provides real-time weather updates based on location.",
            "**Agents with Long-Term Memory** – Maintains context across conversations for improved interactions.",
        ],
        env=[
            {
                "name": "LLM_MODEL",
                "description": "Model to use from the specified OpenAI-compatible API.",
            },
            {
                "name": "LLM_API_BASE",
                "description": "Base URL for OpenAI-compatible API endpoint",
            },
            {
                "name": "LLM_API_KEY",
                "description": "API key for OpenAI-compatible API endpoint",
            },
        ],
    )
)
async def chat_new(input: list[Message], context: Context) -> AsyncGenerator:
    """
    The agent is an AI-powered conversational system with memory, supporting real-time search, Wikipedia lookups,
    and weather updates through integrated tools.
    """

    # ensure the model is pulled before running
    os.environ["OPENAI_API_BASE"] = os.getenv(
        "LLM_API_BASE", "http://localhost:11434/v1"
    )
    os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY", "dummy")

    OpenAIChatModel.tool_choice_support = {"none", "single", "auto"}
    llm = OpenAIChatModel(
        "granite3.3:8b",
        base_url="PROXY_URL",
        api_key="RITS-API-KEY",
    )

    # os.environ["OPENAI_API_BASE"] = "http://localhost:12345/api/v1/llm"
    # llm = ChatModel.from_name(
    #     f"openai:{os.getenv('LLM_MODEL', 'llama3.1')}",
    #     ChatModelParameters(temperature=0),
    # )


    extracted_files = await extract_files(context=context, incoming_messages=input)

    # Base tool set
    tools = [
        ThinkTool(),
        WikipediaTool(),
        OpenMeteoTool(),
        DuckDuckGoSearchTool(),
    ]

    # Only add FileReaderTool if there are files
    if extracted_files:                       # truthy when the list is non-empty
        tools.append(FileReaderTool(extracted_files))        # or FileReaderTool(files=extracted_files) if it takes the files

    agent = RequirementAgent(
        llm=llm,
        tools=tools,
        requirements=[
            ConditionalRequirement(
                ThinkTool, force_at_step=1, force_after=Tool, consecutive_allowed=False
            )
        ],
        middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
    )

    history = [message async for message in context.session.load_history()]

    framework_messages = [
        to_framework_message(message.role, str(message)) for message in history + input
    ]
    await agent.memory.add_many(framework_messages)

    async for event, meta in agent.run():
        assert isinstance(
            event, RequirementAgentStartEvent | RequirementAgentSuccessEvent
        )

        last_step = event.state.steps[-1] if event.state.steps else None
        if last_step and last_step.tool is not None:
            last_tool_call = AnyModel(
                tool_name=last_step.tool.name,
                input=last_step.input,
                output=last_step.output,
                error=last_step.error,
            )
            yield GenericEvent(type=f"tool_{meta.trace.run_id}", generic=last_tool_call)

        if event.state.answer is not None:
            yield event.state.answer.text


def run():
    server.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 8000)),
        configure_telemetry=True,
    )


if __name__ == "__main__":
    run()
