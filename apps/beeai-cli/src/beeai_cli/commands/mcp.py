# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import typing

import typer
from rich.table import Column

from beeai_cli.api import api_request
from beeai_cli.async_typer import AsyncTyper, console, create_table
from beeai_cli.utils import (
    status,
)

app = AsyncTyper()


@app.command("add")
async def add_provider(
    name: typing.Annotated[str, typer.Argument(help="Name for the MCP server")],
    location: typing.Annotated[str, typer.Argument(help="MCP server location (URL of http/sse transport)")],
) -> None:
    """Add local MCP server"""

    with status("Registering server to platform"):
        await api_request("POST", "mcp/providers", json={"name": name, "location": location})
    console.print("Registering server to platform [[green]DONE[/green]]")
    await list_providers()


@app.command("list")
async def list_providers():
    """List providers."""

    providers = await api_request("GET", "mcp/providers")
    console.print(providers)
    # with create_table(
    #     Column("ID"),
    #     Column("Name"),
    #     Column("Description", max_width=30),
    #     no_wrap=True,
    # ) as table:
    #     for provider in providers:
    #         table.add_row(tool["id"], tool["name"], tool["description"])
    # console.print()
    # console.print(table)


@app.command("remove | uninstall | rm | delete")
async def uninstall_provider(id: typing.Annotated[str, typer.Argument(help="ID of an MCP provider")]) -> None:
    """Remove provider"""
    await api_request("delete", f"mcp/providers/{id}")
    await list_providers()


@app.command("tools")
async def list_tools() -> None:
    """List MCP tools available"""

    tools = await api_request("GET", "mcp/tools")
    with create_table(
        Column("Name"),
        Column("Description", max_width=30),
        no_wrap=True,
    ) as table:
        for tool in tools:
            table.add_row(tool["name"], tool["description"])
    console.print()
    console.print(table)


@app.command("toolkit")
async def toolkit(
    tools: typing.Annotated[list[str], typer.Argument(help="Tools for the toolkit")],
) -> None:
    """Create a toolkit"""

    toolkit = await api_request("POST", "mcp/toolkits", json={"tools": tools})
    with create_table(Column("URL"), Column("Expiration")) as table:
        table.add_row(toolkit["url"], toolkit["expires_at"])
    console.print()
    console.print(table)
