# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from datetime import timedelta
import io

from httpx import AsyncClient
from pydantic import AnyUrl

from beeai_server.configuration import DoclingExtractionConfiguration
from beeai_server.domain.models.file import AsyncFile
from beeai_server.domain.repositories.file import ITextExtractionBackend


class DoclingTextExtractionBackend(ITextExtractionBackend):
    def __init__(self, config: DoclingExtractionConfiguration):
        self._config = config

    async def extract_text(self, *, file_url: AnyUrl, timeout: timedelta | None = None) -> AsyncFile:
        timeout = timeout or timedelta(minutes=2)
        async with AsyncClient(base_url=str(self._config.docling_service_url), timeout=timeout.seconds) as client:
            resp = await client.post(
                "/v1alpha/convert/source",
                json={
                    "to_formats": ["md"],
                    "document_timeout": timeout.total_seconds(),
                },
            )
            resp.raise_for_status()
            text_bytes = resp.json()["md_content"].encode("utf-8")

        text_stream = io.BytesIO(text_bytes)

        async def read_bytes(size: int = -1) -> bytes:
            return text_stream.read(size)

        return AsyncFile(
            filename="extracted_text.md", content_type="text/markdown", read=read_bytes, size=len(text_bytes)
        )
