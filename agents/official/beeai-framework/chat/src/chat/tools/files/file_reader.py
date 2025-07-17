# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Literal
from beeai_framework.emitter import Emitter
from beeai_framework.tools import StringToolOutput, Tool, ToolRunOptions, ToolOutput
from chat.helpers.platform import read_file
from chat.tools.files.model import FileChatInfo
from chat.tools.files.utils import format_size
from pydantic import BaseModel, Field, create_model


class FileReaderToolOutput(StringToolOutput):
    pass


class FileReadInputBase(BaseModel):
    """Base class for file read input to enable proper typing"""
    filename: str


def create_file_reader_tool_class(files: list[FileChatInfo]) -> type[Tool]:
    # 1. create a tailor-made Pydantic model
    file_descriptions = "\n".join(
        f"- `{file.display_filename}`[{file.origin_type.value}]: {file.content_type or 'unknown type'}, {format_size(file.file_size_bytes)}"
        for file in files
    )

    description = f"Select one of the provided files:\n\n{file_descriptions}"

    FileReadInput = create_model(
        "FileReadInput",
        filename=(
            Literal[tuple(file.display_filename for file in files)],
            Field(
                ...,
                description=description,
            ),
        ),
    )

    # 2. create a Tool subclass that *uses* that model
    class _FileReaderTool(Tool[FileReadInput, ToolRunOptions, FileReaderToolOutput]):
        """
        Reads and returns content of a file.
        """
        name: str = "FileReader"
        description: str = "Read content of one of the provided file."

        @property
        def input_schema(self):
            return FileReadInput

        def __init__(self) -> None:
            super().__init__()
            self.files = files
            self.files_dict = {file.display_filename: file for file in files}

        async def _run(
            self, input: FileReadInputBase, options, context
        ) -> FileReaderToolOutput:
            # validate that the file_url is one of the provided files
            if input.filename not in self.files_dict:
                raise ValueError(
                    f"Invalid file name: {input.filename}. "
                    f"Expected one of: {', '.join(self.files_dict.keys())}."
                )

            # get the FileInfo object for the requested file
            file_info = self.files_dict[input.filename]

            # pull the first (only) MessagePart from the async-generator
            msg = await read_file(file_info.url)
            if msg.content is None:
                raise ValueError("File content is None.")

            # wrap it in the expected output object
            return FileReaderToolOutput(result=msg.content)

        def _create_emitter(self) -> Emitter:
            return Emitter.root().child(
                namespace=["tool", "file_reader"],
                creator=self,
            )

    return _FileReaderTool  # type: ignore[return-value]
