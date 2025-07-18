# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
from beeai_framework.adapters.openai import OpenAIChatModel
from chat.helpers.local_settings import LocalSettings


from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.utils._tool import FinalAnswerTool
from beeai_framework.agents.experimental.events import (
    RequirementAgentStartEvent,
    RequirementAgentSuccessEvent,
)
import beeai_framework.backend
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from chat.tools.files.file_generator import FileGeneratorTool
from chat.tools.files.file_reader import create_file_reader_tool_class
from chat.tools.files.utils import extract_files
from beeai_framework.tools import Tool
from chat.tools.general.act import (
    ActTool,
    act_tool_middleware,
    ActAlwaysFirstRequirement,
)
from chat.tools.general.clarification import (
    ClarificationTool,
    clarification_tool_middleware,
)
from chat.tools.general.current_time import CurrentTimeTool


# os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:6006")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

import logging
from collections.abc import AsyncGenerator
from textwrap import dedent

import beeai_framework
from acp_sdk import (
    AnyModel,
    Message,
    Metadata,
    Link,
    LinkType,
    Annotations,
)
from acp_sdk.server import Context, Server
from acp_sdk.models.platform import PlatformUIAnnotation, PlatformUIType, AgentToolInfo

from beeai_framework.backend import AssistantMessage, UserMessage
from beeai_framework.backend.types import ChatModelParameters
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
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
    input_content_types=["none"],
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
            memory module**. It utilizes a language model (`CHAT_MODEL`) to generate responses and can optionally 
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
    )
)
async def chat_new(input: list[Message], context: Context) -> AsyncGenerator:
    """
    The agent is an AI-powered conversational system with memory, supporting real-time search, Wikipedia lookups,
    and weather updates through integrated tools.
    """

    OpenAIChatModel.tool_choice_support = {"none", "single", "auto"}
    llm = OpenAIChatModel(
        model_id=os.getenv("LLM_MODEL", "llama3.1"),
        api_key=os.getenv("LLM_API_KEY", "dummy"),
        base_url=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        parameters=ChatModelParameters(
            temperature=0.0,
        ),
    )

    history = [message async for message in context.session.load_history()]
    extracted_files = await extract_files(history=history, incoming_messages=input)

    FinalAnswerTool.description = "Sends the final answer to the user or ask a clarifying question."  # type: ignore

    # Base tool set
    tools = [
        ActTool(),
        WikipediaTool(),
        OpenMeteoTool(),
        DuckDuckGoSearchTool(),
        FileGeneratorTool(),
        ClarificationTool(),
        CurrentTimeTool(),
    ]

    requirements = [
        # ConditionalRequirement(ActTool, force_at_step=1, consecutive_allowed=False),
        ActAlwaysFirstRequirement(),
    ]

    # Only add FileReaderTool if there are files
    if extracted_files:  # truthy when the list is non-empty
        file_reader_tool_class = create_file_reader_tool_class(extracted_files)
        file_reader_tool = file_reader_tool_class()
        tools.append(file_reader_tool)

    local_settings = LocalSettings()
    OpenAIChatModel.tool_choice_support = {"none", "single", "auto"}
    llm = OpenAIChatModel(
        model_id=os.getenv("LLM_MODEL", "llama3.1"),
        api_key=os.getenv("LLM_API_KEY", "dummy"),
        base_url=os.getenv("LLM_API_BASE", "http://localhost:11434/v1"),
        parameters=ChatModelParameters(
            temperature=0.0,
        ),
    )

    agent = RequirementAgent(
        llm=llm,
        tools=tools,
        requirements=requirements,
        middlewares=[
            GlobalTrajectoryMiddleware(included=[Tool]),
            act_tool_middleware,
            clarification_tool_middleware,
        ],
    )

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
                tool_name=last_step.tool.name,  # type: ignore
                input=last_step.input,  # type: ignore
                output=last_step.output.get_text_content() or None,  # type: ignore
                error=last_step.error,  # type: ignore
            )
            if meta.trace is not None:
                yield {f"tool_{meta.trace.run_id}": str(last_tool_call)}

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
