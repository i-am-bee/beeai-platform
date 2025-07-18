# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from os import name
from beeai_framework.emitter import Emitter
from beeai_framework.tools import JSONToolOutput, Tool, ToolRunOptions
from chat.helpers.platform import upload_file, get_file_url
from chat.tools.files.model import FileChatInfo, OriginType
from pydantic import BaseModel


class FileGenerateInput(BaseModel):
    filename: str
    content_type: str
    content: str


class FileGeneratorToolOutput(JSONToolOutput[FileChatInfo]):
    pass


class FileGeneratorTool(
    Tool[FileGenerateInput, ToolRunOptions, FileGeneratorToolOutput]  # type: ignore
):
    """
    Creates a new file and writes the provided content into it.
    """
    name: str = "FileGenerator"
    description: str = "Create a new file with the specified content."
    input_schema: type[FileGenerateInput] = FileGenerateInput

    def __init__(
        self,
    ) -> None:
        super().__init__()

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "file_generator"],
            creator=self,
        )

    async def _run(self, input: FileGenerateInput, options, context) -> FileGeneratorToolOutput:
        result = await upload_file(
            filename=input.filename,
            content_type=input.content_type,
            content=input.content.encode(),
        )
        return FileGeneratorToolOutput(
            result=FileChatInfo(
                id=result.id,
                url=get_file_url(result.id),
                content_type=input.content_type,
                display_filename=input.filename,
                filename=input.filename,
                file_size_bytes=result.file_size_bytes,
                origin_type=OriginType.GENERATED,
            )
        )
