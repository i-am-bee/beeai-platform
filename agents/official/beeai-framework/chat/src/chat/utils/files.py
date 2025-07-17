# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import List
from acp_sdk import Message, MessagePart
from acp_sdk.server import Context
import httpx
from pydantic import AnyUrl, TypeAdapter


async def extract_files(
    context: Context,
    incoming_messages: List[Message],
) -> List[AnyUrl]:
    """
    Return all unique file URLs (as `AnyUrl`) that appear in
    - past conversation history (`context.session.load_history()`) and
    - the `incoming_messages` list for the current turn.

    Order is preserved (first occurrence wins) and every URL
    is validated with Pydantic.

    Parameters
    ----------
    context:
        Must expose an async generator `session.load_history()`
        that yields `Message` objects containing `.parts`.
    incoming_messages:
        The messages that belong to the current request/turn.

    Returns
    -------
    List[AnyUrl]
        Deduplicated, order-preserving list of validated URLs.
    """
    # 1. Combine historical messages with the current turn
    history = [msg async for msg in context.session.load_history()]
    all_messages = [*history, *incoming_messages]

    # 2. Flatten to all parts
    all_parts = (part for message in all_messages for part in message.parts)

    # 3. Collect, validate, deduplicate while preserving order
    seen: set[str] = set()
    result: List[AnyUrl] = []

    for part in all_parts:
        raw_url = getattr(part, "content_url", None)
        if raw_url and raw_url not in seen:
            # validate & cast to AnyUrl; will raise ValidationError if malformed
            url: AnyUrl = TypeAdapter.validate_python(AnyUrl, raw_url)
            result.append(url)
            seen.add(raw_url)

    return result


async def read_file(
    file_url: AnyUrl,
    page: int = 1,
) -> str:
    """
    Read a single page from a file at the given URL.

    Parameters
    ----------
    file_url : AnyUrl
        The URL of the file to read.
    page : int, optional
        The page number to read (1-based index), by default 1.

    Returns
    -------
    str
        The content of the requested page.
    """
    async with httpx.AsyncClient() as client:
        content = await client.get(file_url)
        content_type = content.headers.get("Content-Type")
        yield MessagePart(content=content.content, content_type=content_type)
