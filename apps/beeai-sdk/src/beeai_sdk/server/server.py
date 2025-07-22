import asyncio
import functools
import os
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from a2a.server.agent_execution import RequestContextBuilder
from a2a.server.events import QueueManager
from a2a.server.tasks import PushNotificationConfigStore, PushNotificationSender, TaskStore
from fastapi import FastAPI

from beeai_sdk.server.agent import Agent
from beeai_sdk.server.logging import configure_logger as configure_logger_func
from beeai_sdk.server.telemetry import configure_telemetry as configure_telemetry_func


class Server:
    def __init__(self) -> None:
        self.agent: Agent | None = None
        self.server: uvicorn.Server | None = None

    def agent(
        self,
        name: str | None = None,
        description: str | None = None,
        *,
        metadata: Metadata | None = None,
    ) -> Callable:
        """Decorator to register an agent."""
        if self.agent:
            raise ValueError("Server can have only one agent.")

        def decorator(fn: Callable) -> Callable:
            agent = agent_decorator(name=name, description=description, metadata=metadata)(fn)
            self.register(agent)
            return fn

        return decorator

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None]:
        yield

    async def serve(
        self,
        *,
        configure_logger: bool = True,
        configure_telemetry: bool = False,
        self_registration: bool = True,
        task_store: TaskStore | None = None,
        queue_manager: QueueManager | None = None,
        push_config_store: PushNotificationConfigStore | None = None,
        push_sender: PushNotificationSender | None = None,
        request_context_builder: RequestContextBuilder | None = None,
        host: str = "127.0.0.1",
        port: int = 8000,
        uds: str | None = None,
        fd: int | None = None,
        loop: uvicorn.config.LoopSetupType = "auto",
        http: type[asyncio.Protocol] | uvicorn.config.HTTPProtocolType = "auto",
        ws: type[asyncio.Protocol] | uvicorn.config.WSProtocolType = "auto",
        ws_max_size: int = 16 * 1024 * 1024,
        ws_max_queue: int = 32,
        ws_ping_interval: float | None = 20.0,
        ws_ping_timeout: float | None = 20.0,
        ws_per_message_deflate: bool = True,
        lifespan: uvicorn.config.LifespanType = "auto",
        env_file: str | os.PathLike[str] | None = None,
        log_config: dict[str, Any]
        | str
        | uvicorn.config.RawConfigParser
        | uvicorn.config.IO[Any]
        | None = uvicorn.config.LOGGING_CONFIG,
        log_level: str | int | None = None,
        access_log: bool = True,
        use_colors: bool | None = None,
        interface: uvicorn.config.InterfaceType = "auto",
        reload: bool = False,
        reload_dirs: list[str] | str | None = None,
        reload_delay: float = 0.25,
        reload_includes: list[str] | str | None = None,
        reload_excludes: list[str] | str | None = None,
        workers: int | None = None,
        proxy_headers: bool = True,
        server_header: bool = True,
        date_header: bool = True,
        forwarded_allow_ips: list[str] | str | None = None,
        root_path: str = "",
        limit_concurrency: int | None = None,
        limit_max_requests: int | None = None,
        backlog: int = 2048,
        timeout_keep_alive: int = 5,
        timeout_notify: int = 30,
        timeout_graceful_shutdown: int | None = None,
        callback_notify: Callable[..., Awaitable[None]] | None = None,
        ssl_keyfile: str | os.PathLike[str] | None = None,
        ssl_certfile: str | os.PathLike[str] | None = None,
        ssl_keyfile_password: str | None = None,
        ssl_version: int = uvicorn.config.SSL_PROTOCOL_VERSION,
        ssl_cert_reqs: int = uvicorn.config.ssl.CERT_NONE,
        ssl_ca_certs: str | None = None,
        ssl_ciphers: str = "TLSv1",
        headers: list[tuple[str, str]] | None = None,
        factory: bool = False,
        h11_max_incomplete_event_size: int | None = None,
    ) -> None:
        if self.server:
            raise RuntimeError("The server is already running")

        if headers is None:
            headers = [("server", "a2a")]
        elif not any(k.lower() == "server" for k, _ in headers):
            headers.append(("server", "a2a"))

        import uvicorn

        from beeai_sdk.server.app import create_app

        app = create_app(
            self.agent,
            lifespan=self.lifespan,
            task_store=task_store,
            queue_manager=queue_manager,
            push_config_store=push_config_store,
            push_sender=push_sender,
            request_context_builder=request_context_builder,
        )

        if configure_logger:
            configure_logger_func()

        if configure_telemetry:
            configure_telemetry_func(app)

        config = uvicorn.Config(
            app,
            host,
            port,
            uds,
            fd,
            loop,
            http,
            ws,
            ws_max_size,
            ws_max_queue,
            ws_ping_interval,
            ws_ping_timeout,
            ws_per_message_deflate,
            lifespan,
            env_file,
            log_config,
            log_level,
            access_log,
            use_colors,
            interface,
            reload,
            reload_dirs,
            reload_delay,
            reload_includes,
            reload_excludes,
            workers,
            proxy_headers,
            server_header,
            date_header,
            forwarded_allow_ips,
            root_path,
            limit_concurrency,
            limit_max_requests,
            backlog,
            timeout_keep_alive,
            timeout_notify,
            timeout_graceful_shutdown,
            callback_notify,
            ssl_keyfile,
            ssl_certfile,
            ssl_keyfile_password,
            ssl_version,
            ssl_cert_reqs,
            ssl_ca_certs,
            ssl_ciphers,
            headers,
            factory,
            h11_max_incomplete_event_size,
        )
        self.server = uvicorn.Server(config)
        await self._serve(self_registration=self_registration)

    @functools.wraps(serve)
    def run(self, **kwargs) -> None:
        asyncio.run(self.serve(**kwargs))

    async def _serve(self, self_registration: bool = True) -> None:
        registration_task = asyncio.create_task(self._register_agent()) if self_registration else None
        await self.server.serve()
        if registration_task:
            registration_task.cancel()

    @property
    def should_exit(self) -> bool:
        return self.server.should_exit if self.server else False

    @should_exit.setter
    def should_exit(self, value: bool) -> None:
        self.server.should_exit = value

    async def _register_agent(self) -> None:
        """If not in PRODUCTION mode, register agent to the beeai platform and provide missing env variables"""
        if os.getenv("PRODUCTION_MODE", "").lower() in ["true", "1"]:
            logger.debug("Agent is not automatically registered in the production mode.")
            return

        url = os.getenv("PLATFORM_URL", "http://127.0.0.1:8333")
        host = re.sub(r"localhost|127\.0\.0\.1", "host.docker.internal", self.server.config.host)
        request_data = {
            "location": f"http://{host}:{self.server.config.port}",
        }
        try:
            await async_request_with_retry(lambda client, data=request_data: client.get(f"{url}/api/v1/providers"))
            await async_request_with_retry(
                lambda client, data=request_data: client.post(
                    f"{url}/api/v1/providers", json=data, params={"auto_remove": True}
                )
            )
            logger.debug("Agent registered to the beeai server.")

            # check missing env keyes
            envs_request = await async_request_with_retry(lambda client: client.get(f"{url}/api/v1/variables"))
            envs = envs_request.get("env")
            os.environ["LLM_MODEL"] = "dummy"
            os.environ["LLM_API_KEY"] = "dummy"
            os.environ["LLM_API_BASE"] = f"{url.rstrip('/')}/api/v1/llm"

            for agent in self.agents:
                # register all available envs
                missing_keyes = []
                for env in agent.metadata.model_dump().get("env", []):
                    # Those envs are set to use LLM gateway from platform server
                    if env["name"] in {"LLM_MODEL", "LLM_API_KEY", "LLM_API_BASE"}:
                        continue
                    server_env = envs.get(env.get("name"))
                    if server_env:
                        logger.debug(f"Env variable {env['name']} = '{server_env}' added dynamically")
                        os.environ[env["name"]] = server_env
                    elif env.get("required"):
                        missing_keyes.append(env)
                if len(missing_keyes):
                    logger.debug(f"Can not run agent, missing required env variables: {missing_keyes}")
                    raise Exception("Missing env variables")

        except requests.exceptions.ConnectionError as e:
            logger.debug(f"Can not reach server, check if running on {url} : {e}")
        except (requests.exceptions.HTTPError, Exception) as e:
            try:
                error_message = e.response.json().get("detail")
                if error_message:
                    logger.debug(f"Agent can not be registered to beeai server: {error_message}")
                else:
                    logger.debug(f"Agent can not be registered to beeai server: {e}")
            except Exception:
                logger.debug(f"Agent can not be registered to beeai server: {e}")
