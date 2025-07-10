# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import os
import re
from typing import AsyncGenerator, Iterable
from acp_sdk import Message, MessagePart
from chat.tools.file_reader import BaseModel
from acp_sdk.server import Context
import httpx
from pydantic import AnyUrl


class FileInfo(BaseModel):
    id: str
    url: AnyUrl
    filename: str
    display_filename: str  # A sanitized version of the filename used for display, in case of naming conflicts.
    content_type: str | None = None
    file_size_bytes: int | None = None


async def extract_files(
    context: Context,
    incoming_messages: list[Message],
) -> list[FileInfo]:
    """
    Extracts file URLs from the chat history and the current turn's messages.

    Args:
        context (Context): The current context of the chat session.
        incoming_messages (list[Message]): The messages from the current turn.

    Returns:
        list[FileInfo]: A list of FileInfo objects containing file details.
    """
    # 1. Combine historical messages with the current turn
    history = [msg async for msg in context.session.load_history()]
    all_messages = [*history, *incoming_messages]

    # 2. Flatten to all parts
    all_parts = (part for message in all_messages for part in message.parts)

    # 3. Collect, validate, deduplicate while preserving order
    seen: set[str] = set()
    files: list[FileInfo] = []
    existing_filenames: list[str] = []

    for part in all_parts:
        url = getattr(part, "content_url", None)
        if url and url not in seen:
            fileInfo = await get_file_info(
                url,
                content_type=part.content_type,
                existing_filenames=existing_filenames,
            )
            if fileInfo:
                files.append(fileInfo)
                existing_filenames.append(fileInfo.display_filename)
            seen.add(url)

    return files


async def get_file_info(
    url: str, content_type: str, existing_filenames: list[str]
) -> FileInfo:
    # 1. Extract the file-ID from the signed-download URL
    file_id_match = re.search(r"/([^/]+)/content", str(url))
    if not file_id_match:
        raise ValueError(f"Could not extract file_id from: {url!r}")
    file_id = file_id_match.group(1)

    # 2. Ask the platform for the file metadata
    async with httpx.AsyncClient(
        base_url=os.getenv("PLATFORM_URL", "http://127.0.0.1:8333")
    ) as client:
        response = await client.get(f"api/v1/files/{file_id}")
        response.raise_for_status()
        api_payload = response.json()

    # 3. Merge the API data with the known url & content_type
    merged_payload = {
        **api_payload,  # → id, filename, file_size_bytes …
        "url": url,  # override / add
        "content_type": content_type,
        "display_filename": next_unused_filename(
            api_payload.get("filename", "unknown"), existing_filenames
        ),  # ensure unique display name
    }

    # 4. Validate & coerce with Pydantic
    file_info = FileInfo.model_validate(merged_payload)

    # 5. Extra safeguard: make sure filename is a string
    if not isinstance(file_info.filename, str):
        file_info.filename = str(file_info.filename)

    return file_info


def next_unused_filename(name: str, existing: Iterable[str]) -> str:
    """Return a filename that is not present in *existing* by appending
    '(n)' before the extension when needed.

    Return *name* unchanged if it is not in *existing*.
    Otherwise append / increment a numeric suffix in parentheses
    just before the extension:  foo.txt  ->  foo(1).txt  ->  foo(2).txt …

    Parameters
    ----------
    name      : the desired file name, e.g. 'todo.txt'
    existing  : iterable of names already taken (case-sensitive)

    Examples
    --------
    >>> next_unused_filename("todo.txt", ["todo.txt", "todo(1).txt"])
    'todo(2).txt'
    """
    existing_set = set(existing)
    if name not in existing_set:  # fast path – no clash
        return name

    # split off the last extension (handles .tar.gz etc. by design choice)
    if "." in name:
        base, ext = name.rsplit(".", 1)
        ext = f".{ext}"
    else:
        base, ext = name, ""

    # regex to capture already-numbered siblings: foo(12).txt
    numbered = re.compile(rf"^{re.escape(base)}\((\d+)\){re.escape(ext)}$")

    # collect the numbers already used for this base
    used = {int(m.group(1)) for n in existing_set if (m := numbered.match(n))}

    # smallest positive integer that isn’t taken
    i = 1
    while i in used:
        i += 1

    return f"{base}({i}){ext}"


async def read_file(
    file_url: AnyUrl,
) -> AsyncGenerator[MessagePart, None]:
    print(f"Reading file from {file_url}...")
    async with httpx.AsyncClient() as client:
        content = await client.get(str(file_url))
        content_type = content.headers.get("Content-Type")
        print(f"File read: {file_url}, content type: {content_type}, size: {len(content.content)} bytes")
        yield MessagePart(content=content.content, content_type=content_type)


def format_size(size: int | None) -> str:
    if size is None:
        return "unknown size"
    elif size < 1024:
        return f"{size} bytes"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"
