# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import contextlib
import os
import ssl
import typing
import webbrowser
from collections.abc import AsyncIterator
from types import TracebackType

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from httpx import URL, AsyncBaseTransport, Request
from httpx._client import EventHook
from httpx._config import DEFAULT_LIMITS, DEFAULT_MAX_REDIRECTS, DEFAULT_TIMEOUT_CONFIG, Limits
from httpx._types import AuthTypes, CertTypes, CookieTypes, HeaderTypes, ProxyTypes, QueryParamTypes, TimeoutTypes
from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata
from pydantic import AnyUrl, Secret

from beeai_sdk.util import resource_context
from beeai_sdk.util.mcp.storage.memory import MemoryTokenStorageFactory


class PlatformClient(httpx.AsyncClient):
    context_id: str | None = None

    def __init__(
        self,
        context_id: str | None = None,  # Enter context scope
        auth_token: str | Secret | None = None,
        auth_redirect_host: str = "127.0.0.1",
        auth_redirect_port: int = 0,
        auth_client_id: str | None = None,
        auth_client_secret: str | None = None,
        *,
        auth: AuthTypes | None = None,
        params: QueryParamTypes | None = None,
        headers: HeaderTypes | None = None,
        cookies: CookieTypes | None = None,
        verify: ssl.SSLContext | str | bool = True,
        cert: CertTypes | None = None,
        http1: bool = True,
        http2: bool = False,
        proxy: ProxyTypes | None = None,
        mounts: None | (typing.Mapping[str, AsyncBaseTransport | None]) = None,
        timeout: TimeoutTypes = DEFAULT_TIMEOUT_CONFIG,
        follow_redirects: bool = False,
        limits: Limits = DEFAULT_LIMITS,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        event_hooks: None | (typing.Mapping[str, list[EventHook]]) = None,
        base_url: URL | str = "",
        transport: AsyncBaseTransport | None = None,
        trust_env: bool = True,
        default_encoding: str | typing.Callable[[bytes], str] = "utf-8",
    ) -> None:
        if not base_url:
            base_url = os.environ.get("PLATFORM_URL", "http://127.0.0.1:8333")
        super().__init__(
            auth=auth,
            params=params,
            headers=headers,
            cookies=cookies,
            verify=verify,
            cert=cert,
            http1=http1,
            http2=http2,
            proxy=proxy,
            mounts=mounts,
            timeout=timeout,
            follow_redirects=follow_redirects,
            limits=limits,
            max_redirects=max_redirects,
            event_hooks=event_hooks,
            base_url=base_url,
            transport=transport,
            trust_env=trust_env,
            default_encoding=default_encoding,
        )
        self.context_id = context_id

        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

        self._auth_redirect_host = auth_redirect_host
        self._auth_redirect_port = auth_redirect_port
        self._auth_client_id = auth_client_id
        self._auth_client_secret = auth_client_secret

        self._ref_count = 0
        self._context_manager_lock = asyncio.Lock()

        self._pending_callback: asyncio.Future[tuple[str, str | None]] | None = None
        self._callback_app_ready = asyncio.Event()

    async def __aenter__(self) -> typing.Self:
        async with self._context_manager_lock:
            self._ref_count += 1
            if self._ref_count == 1:
                self._callback_server = self._callback_app()
                await self._callback_server.__aenter__()
                await super().__aenter__()
            return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        async with self._context_manager_lock:
            self._ref_count -= 1
            if self._ref_count == 0:
                await super().__aexit__(exc_type, exc_value, traceback)
                await self._callback_server.__aexit__(exc_type, exc_value, traceback)
                self._resource = None

    async def _handle_redirect(self, auth_url: str) -> None:
        await self._callback_app_ready.wait()
        webbrowser.open(auth_url)

    async def _handle_callback(self) -> tuple[str, str | None]:
        self._pending_callback = asyncio.Future()
        return await asyncio.wait_for(self._pending_callback, timeout=5 * 60)

    async def _setup_auth(self, host: str, port: int) -> None:
        redirect_uris = [AnyUrl(f"http://{host}:{port}/callback")]
        storage = await MemoryTokenStorageFactory().create_storage()
        if self._auth_client_id:
            await storage.set_client_info(
                OAuthClientInformationFull(
                    redirect_uris=redirect_uris, client_id=self._auth_client_id, client_secret=self._auth_client_secret
                )
            )
        self.auth = OAuthClientProvider(
            server_url=str(self.base_url),
            client_metadata=OAuthClientMetadata(redirect_uris=redirect_uris),
            storage=storage,
            redirect_handler=self._handle_redirect,
            callback_handler=self._handle_callback,
        )

    @contextlib.asynccontextmanager
    async def _callback_app(self):
        if self.auth:
            yield
            return

        @contextlib.asynccontextmanager
        async def lifespan(app: FastAPI):
            self._callback_app_ready.set()
            yield
            self._callback_app_ready.clear()

        app = FastAPI(lifespan=lifespan)

        @app.get("/callback")
        async def callback(request: Request):
            code = request.url.params.get("code")
            state = request.url.params.get("state")
            error = request.url.params.get("error")

            if code and self._pending_callback and not self._pending_callback.done():
                self._pending_callback.set_result((code, state))
                html_content = """
                <!DOCTYPE html>
                <html>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window.</p>
                    <script>setTimeout(() => window.close(), 2000);</script>
                </body>
                </html>
                """
                return HTMLResponse(content=html_content, status_code=200)
            elif error:
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>Error: {error}</p>
                    <p>You can close this window.</p>
                </body>
                </html>
                """
                return HTMLResponse(content=html_content, status_code=200)
            else:
                return HTMLResponse(status_code=404)

        server = uvicorn.Server(uvicorn.Config(app, host=self._auth_redirect_host, port=self._auth_redirect_port))
        asyncio.get_running_loop().create_task(server.serve())

        sock = server.config.bind_socket()
        assigned_port = sock.getsockname()[1]

        await self._setup_auth(server.config.host, assigned_port)

        try:
            yield
        finally:
            server.should_exit = True


get_platform_client, set_platform_client = resource_context(factory=PlatformClient, default_factory=PlatformClient)

P = typing.ParamSpec("P")
T = typing.TypeVar("T", bound=PlatformClient)


def wrap_context(
    context: typing.Callable[P, contextlib.AbstractContextManager[T]],
) -> typing.Callable[P, contextlib.AbstractAsyncContextManager[T]]:
    @contextlib.asynccontextmanager
    async def use_async_resource(*args: P.args, **kwargs: P.kwargs) -> AsyncIterator[T]:
        with context(*args, **kwargs) as resource:
            async with resource:
                yield resource

    return use_async_resource


use_platform_client = wrap_context(set_platform_client)


__all__ = ["PlatformClient", "get_platform_client", "set_platform_client", "use_platform_client"]
