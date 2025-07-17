# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing

import typer

from beeai_cli.api import api_request
from beeai_cli.async_typer import AsyncTyper, console
from beeai_cli.utils import (
    status,
)

app = AsyncTyper()


@app.command("add")
async def add_provider(
    location: typing.Annotated[str, typer.Argument(help="MCP server location (URL of http/sse transport)")],
) -> None:
    """Add local MCP server"""

    with status("Registering server to platform"):
        await api_request("POST", "mcp/providers", json={"location": location})
    console.print("Registering server to platform [[green]DONE[/green]]")
    await list_providers()


@app.command("list")
async def list_providers():
    """List providers."""

    providers = await api_request("GET", "mcp/providers")
    console.print(providers)


@app.command("remove | uninstall | rm | delete")
async def uninstall_provider(id: typing.Annotated[str, typer.Argument(help="ID of an MCP provider")]) -> None:
    """Remove provider"""
    await api_request("delete", f"mcp/providers/{id}")
    await list_providers()


@app.command("tools")
async def list_tools() -> None:
    """List MCP tools available"""

    tools = await api_request("GET", "mcp/tools")
    console.print(tools)


@app.command("toolkit")
async def toolkit(
    tools: typing.Annotated[list[str], typer.Argument(help="Tools for the toolkit")],
) -> None:
    """Create a toolkit"""

    toolkit = await api_request("POST", "mcp/toolkits", json={"tools": tools})
    console.print(toolkit)
