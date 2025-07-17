# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

from beeai_framework.tools import JSONToolOutput, Tool, ToolRunOptions
from pydantic import BaseModel, Field


class FileReadToolInputSchema(BaseModel):
    file_url: str = Field(description="The URL of the file to read from.")
    page: int = Field(
        description="The page number to read from the file. Defaults to 1.",
        default=1,
    )

class PageReadResult(BaseModel):
    """
    Data returned by :func:`read_page`.

    Attributes
    ----------
    page_text : str
        The full text of the requested page.
    current_page : int
        Zero-based index of the page that was read.
    pages_remaining : int
        How many pages are left after *current_page*.
    pages_from_start : int
        How many pages have been traversed from the beginning
        up to (but **not** including) *current_page*.
    """
    page_text: str = Field(..., description="The content of the requested page")
    current_page: int = Field(..., ge=0, description="Zero-based index of the page")
    pages_remaining: int = Field(..., ge=0, description="Pages left after this one")
    pages_from_start: int = Field(..., ge=0, description="Pages read before this one")

class FileReaderToolOutput(JSONToolOutput[PageReadResult]):
    pass

class FileReaderTool(Tool[FileReadToolInputSchema,ToolRunOptions, FileReaderToolOutput]):
    """
    Reads a single page from a file and returns detailed pagination information.

    Returns
    -------
    tuple[str, int, int, int]
        (page_text, current_page, pages_remaining, pages_from_start)

        - **page_text** (str): The content of the requested page.  
        - **current_page** (int): The zero-based index of the page that was read.  
        - **pages_remaining** (int): How many pages are left after this one.  
        - **pages_from_start** (int): How many pages have been traversed from the beginning up to (but not including) the current page.
    """
