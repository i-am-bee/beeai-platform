# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0


from urllib.parse import parse_qs

from a2a.types import DataPart
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from pydantic import AnyUrl

from beeai_sdk.a2a.extensions.services.mcp import Auth
from beeai_sdk.a2a.types import AgentMessage, AuthRequired, RunYieldResume
from beeai_sdk.server.context import RunContext


class InMemoryTokenStorage(TokenStorage):
    """Demo In-memory token storage implementation."""

    def __init__(self):
        self.tokens: OAuthToken | None = None
        self.client_info: OAuthClientInformationFull | None = None

    async def get_tokens(self) -> OAuthToken | None:
        """Get stored tokens."""
        return self.tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        """Store tokens."""
        self.tokens = tokens

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        """Get stored client information."""
        return self.client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        """Store client information."""
        self.client_info = client_info


def create_auth_provider(auth: Auth | None, context: RunContext):
    resume: RunYieldResume = None

    async def handle_redirect(auth_url: str) -> None:
        nonlocal resume
        if resume:
            raise RuntimeError("Another redirect pending")
        resume = await context.yield_async(
            AuthRequired(message=AgentMessage(parts=[DataPart(data={"authorization_endpoint_url": auth_url})]))  # type: ignore
        )

    async def handle_callback() -> tuple[str, str | None]:
        nonlocal resume
        try:
            if not resume:
                raise RuntimeError("Missing resume")
            if not resume.parts:
                raise ValueError("Missing data")
            if (
                not (data := resume.parts[0])
                or not isinstance(data, DataPart)
                or not (redirect_uri := data.data.get("redirect_uri"))
                or not isinstance(redirect_uri, str)
            ):
                raise ValueError("Invalid data")
            redirect_uri = AnyUrl(redirect_uri)
            params = parse_qs(redirect_uri.query)
            return params["code"][0], params.get("state", [None])[0]
        finally:
            resume = None

    # The provider currently only supports authorization code flow
    # A2A Client is responsible for catching the redirect_uri and forwarding it over the A2A connection
    oauth_auth = OAuthClientProvider(
        server_url="https://invalid",
        client_metadata=OAuthClientMetadata(
            redirect_uris=[(auth and auth.redirect_uri) or AnyUrl("http://localhost:3000/callback")],
        ),
        storage=InMemoryTokenStorage(),
        redirect_handler=handle_redirect,
        callback_handler=handle_callback,
    )
    return oauth_auth
