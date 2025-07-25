# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import logging
import os
import re
import uuid
from asyncio import TaskGroup
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import timedelta
from textwrap import dedent
from typing import Final

import beeai_framework
import httpx
from acp_sdk import (
    Annotations,
    Link,
    LinkType,
    Message,
    MessagePart,
    Metadata,
    PlatformUIAnnotation,
)
from acp_sdk.models.platform import AgentToolInfo, PlatformUIType
from acp_sdk.server import Context, Server
from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.agents.react import ReActAgent, ReActAgentUpdateEvent
from beeai_framework.backend import AssistantMessage, UserMessage
from beeai_framework.memory import UnconstrainedMemory
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openinference.instrumentation.beeai import BeeAIInstrumentor
from pydantic import AnyUrl
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_delay, wait_fixed

from rag_agent.vector_search_tool import VectorSearchTool

os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://127.0.0.1:6006"


BeeAIInstrumentor().instrument()
logging.getLogger("opentelemetry.exporter.otlp.proto.http._log_exporter").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.metric_exporter").setLevel(logging.CRITICAL)


server = Server()


PLATFORM_URL: Final = os.getenv("PLATFORM_URL", "http://127.0.0.1:8333")


@asynccontextmanager
async def platform_client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(base_url=f"{PLATFORM_URL}/api/v1") as client:
        yield client


async def create_vector_store(client: httpx.AsyncClient) -> str:
    """Create a new vector store and return its ID."""
    response = await client.post("llm/embeddings", json={"model": "text-embedding-model", "input": "dummy"})
    response.raise_for_status()
    response_data = response.json()
    dimension = len(response_data["data"][0]["embedding"])

    response = await client.post(
        "vector_stores",
        json={
            "name": "rag-vector-store",
            "dimension": dimension,
            "model_id": "text-embedding-model",
        },
    )
    response.raise_for_status()
    vector_store_data = response.json()
    return vector_store_data["id"]


async def extract_file(client: httpx.AsyncClient, file_id: str) -> str:
    await client.post(f"files/{file_id}/extraction")

    async for attempt in AsyncRetrying(
        stop=stop_after_delay(timedelta(minutes=2)),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(TimeoutError),
        reraise=True,
    ):
        with attempt:
            response = await client.get(f"files/{file_id}/extraction")
            response.raise_for_status()
            extraction_data = response.json()
            final_status = extraction_data["status"]
            if final_status == "failed":
                raise RuntimeError(f"Extraction for file {file_id} has failed: {extraction_data}")
            if final_status != "completed":
                raise TimeoutError("Text extraction is not finished yet")


async def chunk_and_embed(client: httpx.AsyncClient, file_id: str, vector_store_id: str):
    """
    Extract text from file, chunk it using RecursiveCharacterTextSplitter,
    generate embeddings, and store in vector database.
    """
    response = await client.get(f"files/{file_id}/text_content")
    response.raise_for_status()
    text = response.text

    if not text.strip():
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = text_splitter.split_text(text)

    if not chunks:
        return

    embed_response = await client.post("llm/embeddings", json={"model": "text-embedding-model", "input": chunks})
    embed_response.raise_for_status()
    embeddings_data = embed_response.json()

    vector_items = []
    for i, (chunk, embedding_data) in enumerate(zip(chunks, embeddings_data["data"], strict=False)):
        vector_items.append(
            {
                "document_id": file_id,
                "document_type": "platform_file",
                "model_id": "text-embedding-model",
                "text": chunk,
                "embedding": embedding_data["embedding"],
                "metadata": {
                    "file_id": file_id,
                    "chunk_index": str(i),
                    "chunk_id": str(uuid.uuid4()),
                    "total_chunks": str(len(chunks)),
                },
            }
        )

    upload_response = await client.put(f"vector_stores/{vector_store_id}", json=vector_items)
    upload_response.raise_for_status()


async def embed_all_files(client: httpx.AsyncClient, all_files: set[AnyUrl | None], vector_store_id: str):
    """Extract text from files and embed them into the vector store."""
    if not all_files:
        return

    response = await client.get(f"vector_stores/{vector_store_id}/documents")
    response.raise_for_status()
    documents = response.json()["items"]

    file_ids = {re.search(r"/([^/]+)/content", str(url)) for url in all_files}
    file_ids = {match.group(1) for match in file_ids if match}
    document_ids = {document["file_id"] for document in documents if "file_id" in document}
    to_embed = {file_id for file_id in file_ids if file_id not in document_ids}

    if not to_embed:
        return

    async with TaskGroup() as tg:
        for file_id in to_embed:
            tg.create_task(extract_file(client, file_id))

    async with TaskGroup() as tg:
        for file_id in to_embed:
            tg.create_task(chunk_and_embed(client, file_id, vector_store_id))


async def ensure_vectorstore(client: httpx.AsyncClient, all_parts: list[MessagePart]) -> tuple[str, bool]:
    """Ensure vector store exists and return its ID."""
    if vector_store_id := [part.content for part in all_parts if part.content_type == "session/vectorstore_id"]:
        return vector_store_id[0], False
    else:
        return await create_vector_store(client), True


def to_framework_messages(all_messages: list[Message]) -> Iterator[beeai_framework.backend.Message]:
    for message in all_messages:
        for part in message.parts:
            content = ""
            if part.content and part.content_type == "text/plain":
                content = part.content
            elif part.content_url:
                content = f"Attached file: {part.content_url} is indexed and available for semantic search"
            else:
                continue
            yield UserMessage(content) if message.role == "user" else AssistantMessage(content)


@server.agent(
    input_content_types=["text/plain", "application/pdf"],
    output_content_types=["text/plain"],
    metadata=Metadata(
        annotations=Annotations(
            beeai_ui=PlatformUIAnnotation(
                ui_type=PlatformUIType.CHAT,
                user_greeting="How can I help you?",
                display_name="RAG",
                tools=[AgentToolInfo(name="RAG Search", description="Search through your files")],
            ),
        ),
        programming_language="Python",
        links=[
            Link(
                type=LinkType.SOURCE_CODE,
                url=AnyUrl(
                    f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
                    "/agents/official/sequential-workflow"
                ),
            )
        ],
        license="Apache 2.0",
        framework="ACP",
        use_cases=[
            # TODO
        ],
        documentation=dedent(
            """\
            TODO
            """
        ),
        env=[
            {"name": "RITS_API_KEY", "description": "API key for OpenAI-compatible API endpoint"},
        ],
    ),
)
async def rag_agent(input: list[Message], context: Context) -> AsyncIterator:
    """
    RAG agent that combines document search capabilities with web search.
    It can search through uploaded documents using semantic search and also
    search the web for additional information.
    """
    all_messages = [*[message async for message in context.session.load_history()], *input]
    all_parts = [part for message in all_messages for part in message.parts]

    tools = []

    # Ensure vector store exists and get its ID
    if all_files := {part.content_url for part in all_parts if part.content_url}:
        async with platform_client() as client:
            vector_store_id, is_newly_created = await ensure_vectorstore(client, all_parts)
            if is_newly_created:
                # Yield vector store ID for session persistence
                yield MessagePart(content_type="session/vectorstore_id", content=vector_store_id)
            tools.append(VectorSearchTool(vector_store_id=vector_store_id))
            yield "Processing files...\n\n"
            await embed_all_files(client, all_files, vector_store_id)

    OpenAIChatModel.tool_choice_support = {"none", "single", "auto"}
    llm = OpenAIChatModel(
        model_id=os.getenv("LLM_MODEL"),
        base_url=os.getenv("LLM_API_BASE"),
        api_key=os.getenv("LLM_API_KEY"),
    )

    agent = ReActAgent(
        llm=llm,
        tools=tools,
        memory=UnconstrainedMemory(),
    )

    framework_messages = list(to_framework_messages(all_messages))

    await agent.memory.add_many(framework_messages)

    async for data, event in agent.run():
        match (data, event.name):
            case (ReActAgentUpdateEvent(), "partial_update"):
                update = data.update.value
                if not isinstance(update, str):
                    update = update.get_text_content()
                match data.update.key:
                    case "thought" | "tool_name" | "tool_input" | "tool_output":
                        yield {data.update.key: update}
                    case "final_answer":
                        yield MessagePart(content=update)


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)), configure_telemetry=True)


if __name__ == "__main__":
    run()
