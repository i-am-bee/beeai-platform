# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal
from beeai_framework.emitter import Emitter
from beeai_framework.tools import JSONToolOutput, StringToolOutput, Tool, ToolRunOptions
from beeai_framework.utils.strings import to_safe_word
from pydantic import BaseModel, Field, create_model
from chat.utils.files import FileInfo, format_size, read_file


class FileReaderToolOutput(StringToolOutput):
    pass


def create_file_reader_tool_class(files: list[FileInfo]) -> type[Tool]:
    # 1. create a tailor-made Pydantic model
    file_descriptions = "\n".join(
        f"- `{file.display_filename}`: {file.content_type or 'unknown type'}, {format_size(file.file_size_bytes)}"
        for file in files
    )

    description = f"Select one of the provided files:\n\n{file_descriptions}"

    FileReadInput = create_model(
        "FileReadInput",
        file_name=(
            Literal[tuple(file.display_filename for file in files)],
            Field(
                ...,
                description=description,
            ),
        ),
    )

    # 2. create a Tool subclass that *uses* that model
    class _FileReaderTool(
        Tool[FileReadInput, ToolRunOptions, FileReaderToolOutput]  # type: ignore
    ):
        """
        Reads and returns content of a file.
        """
        name = "FileReader"
        description = "Read content of one of the provided file."
        input_schema = FileReadInput

        def __init__(self) -> None:
            super().__init__()
            self.files = files
            self.files_dict = {file.display_filename: file for file in files}

        async def _run(self, input, options, context) -> FileReaderToolOutput:

            print(f"FileReaderTool: Reading file {input.file_name}...")

            # validate that the file_url is one of the provided files
            if input.file_name not in self.files_dict:
                raise ValueError(
                    f"Invalid file name: {input.file_name}. "
                    f"Expected one of: {', '.join(self.files_dict.keys())}."
                )

            # get the FileInfo object for the requested file
            file_info = self.files_dict[input.file_name]

            # pull the first (only) MessagePart from the async-generator
            async for part in read_file(file_info.url):
                text = part.content
                break  # we only need the first yield

            # wrap it in the expected output object
            return FileReaderToolOutput(text)

        def _create_emitter(self) -> Emitter:
            return Emitter.root().child(
                namespace=["tool", "file_reader"],
                creator=self,
            )

    return _FileReaderTool
