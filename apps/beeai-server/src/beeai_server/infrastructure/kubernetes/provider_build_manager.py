# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Any, Final
from uuid import UUID

import anyio
import kr8s
import yaml
from jinja2 import Template
from kr8s.asyncio.objects import Job

from beeai_server.domain.models.provider_build import BuildState, ProviderBuild
from beeai_server.service_layer.build_manager import IProviderBuildManager
from beeai_server.utils.logs_container import LogsContainer

logger = logging.getLogger(__name__)


BUILD_AGENT_JOB_FILE_NAME: Final = "build-provider-job.yaml"
DEFAULT_TEMPLATE_DIR: Final = Path(__file__).parent / "default_templates"


class KubernetesProviderBuildManager(IProviderBuildManager):
    def __init__(
        self,
        api_factory: Callable[[], Awaitable[kr8s.asyncio.Api]],
        manifest_template_dir: Path | None = None,
    ):
        self._api_factory = api_factory
        self._create_lock = asyncio.Lock()
        self._template_dir = anyio.Path(manifest_template_dir or DEFAULT_TEMPLATE_DIR)
        self._template = None

    @asynccontextmanager
    async def api(self) -> AsyncIterator[kr8s.asyncio.Api]:
        client = await self._api_factory()
        yield client

    async def _render_template(self, **variables) -> dict[str, Any]:
        if self._template is None:
            self._template = await (self._template_dir / BUILD_AGENT_JOB_FILE_NAME).read_text()
        return yaml.safe_load(Template(self._template).render(**variables))

    def _get_k8s_name(self, provider_build_id: UUID):
        return f"beeai-build-{provider_build_id}"

    def _get_build_id_from_name(self, name: str) -> UUID:
        pattern = r"beeai-build-([0-9a-f-]+)$"
        if match := re.match(pattern, name):
            [provider_build_id] = match.groups()
            return UUID(provider_build_id)
        raise ValueError(f"Invalid provider name format: {name}")

    async def create_job(self, *, provider_build: ProviderBuild) -> bool:
        async with self.api() as api:
            label = self._get_k8s_name(provider_build.id)

            job = Job(
                await self._render_template(
                    provider_build_name=self._get_k8s_name(provider_build.id),
                    provider_build_label=label,
                    git_host=provider_build.source.host,
                    git_org=provider_build.source.org,
                    git_repo=provider_build.source.repo,
                    git_ref=provider_build.source.commit_hash,
                ),
                api=api,
            )
        return True

    async def cancel_job(self, *, provider_build_id: UUID) -> None: ...
    async def wait_for_completion(self, *, provider_build_id: UUID, timeout: timedelta) -> BuildState: ...  # noqa: ASYNC109 (the timeout actually corresponds to kubernetes timeout)
    async def stream_logs(self, *, provider_build_id: UUID, logs_container: LogsContainer) -> None: ...

    # async def delete(self, *, provider_id: UUID) -> None:
    #     with suppress(kr8s.NotFoundError):
    #         async with self.api() as api:
    #             deploy = await Deployment.get(name=self._get_k8s_name(provider_id, TemplateKind.DEPLOY), api=api)
    #             await deploy.delete(propagation_policy="Foreground", force=True)
    #             await deploy.wait(["delete"])
    #
    # async def remove_orphaned_providers(self, existing_providers: list[UUID]) -> None:
    #     errors = []
    #
    #     async def _delete(deploy: APIObject):
    #         try:
    #             with suppress(kr8s.NotFoundError):
    #                 await deploy.delete(propagation_policy="Foreground", force=True)
    #                 await deploy.wait(["delete"])
    #                 logger.info(f"Deleted orphaned provider {deploy.metadata.name}")
    #         except Exception as ex:
    #             errors.append(ex)
    #
    #     async with self.api() as api, TaskGroup() as tg:
    #         async for deployment in kr8s.asyncio.get(
    #             kind="deployment",
    #             label_selector={"managedBy": "beeai-platform"},
    #             api=api,
    #         ):
    #             provider_id = self._get_provider_id_from_name(deployment.metadata.name, TemplateKind.DEPLOY)
    #             if provider_id not in existing_providers:
    #                 tg.create_task(_delete(deployment))
    #     if errors:
    #         raise ExceptionGroup("Exceptions occurred when removing orphaned providers", errors)
    #
    # async def scale_down(self, *, provider_id: UUID) -> None:
    #     async with self.api() as api:
    #         deploy = await Deployment.get(name=self._get_k8s_name(provider_id, TemplateKind.DEPLOY), api=api)
    #         await deploy.scale(0)
    #
    # async def scale_up(self, *, provider_id: UUID) -> None:
    #     async with self.api() as api:
    #         deploy = await Deployment.get(name=self._get_k8s_name(provider_id, TemplateKind.DEPLOY), api=api)
    #         await deploy.scale(1)
    #
    # async def wait_for_startup(self, *, provider_id: UUID, timeout: timedelta) -> None:
    #     async with self.api() as api:
    #         deployment = await Deployment.get(name=self._get_k8s_name(provider_id, kind=TemplateKind.DEPLOY), api=api)
    #         await deployment.wait("condition=Available", timeout=int(timeout.total_seconds()))
    #         # For some reason the first request sometimes doesn't come through
    #         # (the service does not route immediately after deploy is available?)
    #         async for attempt in AsyncRetrying(
    #             stop=stop_after_delay(timedelta(seconds=10)),
    #             wait=wait_fixed(timedelta(seconds=0.5)),
    #             retry=retry_if_exception_type(HTTPError),
    #             reraise=True,
    #         ):
    #             with attempt:
    #                 async with AsyncClient(
    #                     base_url=str(await self.get_provider_url(provider_id=provider_id))
    #                 ) as client:
    #                     resp = await client.get(AGENT_CARD_WELL_KNOWN_PATH, timeout=2)
    #                     resp.raise_for_status()
    #
    # async def state(self, *, provider_ids: list[UUID]) -> list[ProviderDeploymentState]:
    #     async with self.api() as api:
    #         deployments = {
    #             self._get_provider_id_from_name(deployment.metadata.name, TemplateKind.DEPLOY): deployment
    #             async for deployment in kr8s.asyncio.get(
    #                 kind="deployment",
    #                 label_selector={"managedBy": "beeai-platform"},
    #                 api=api,
    #             )
    #         }
    #         provider_ids_set = set(provider_ids)
    #         deployments = {provider_id: d for provider_id, d in deployments.items() if provider_id in provider_ids_set}
    #         states = []
    #         for provider_id in provider_ids:
    #             deployment = deployments.get(provider_id)
    #             if not deployment:
    #                 state = ProviderDeploymentState.MISSING
    #             elif deployment.status.get("availableReplicas", 0) > 0:
    #                 state = ProviderDeploymentState.RUNNING
    #             elif deployment.status.get("replicas", 0) == 0:
    #                 state = ProviderDeploymentState.READY
    #             else:
    #                 state = ProviderDeploymentState.STARTING
    #             states.append(state)
    #         return states
    #
    # async def get_provider_url(self, *, provider_id: UUID) -> HttpUrl:
    #     return HttpUrl(f"http://{self._get_k8s_name(provider_id, TemplateKind.SVC)}:8000")
    #
    # async def stream_logs(self, *, provider_id: UUID, logs_container: LogsContainer):
    #     try:
    #         async with self.api() as api:
    #             missing_logged = False
    #             while True:
    #                 try:
    #                     deploy = await Deployment.get(
    #                         name=self._get_k8s_name(provider_id, kind=TemplateKind.DEPLOY),
    #                         api=api,
    #                     )
    #                     if pods := await deploy.pods():
    #                         break
    #                 except kr8s.NotFoundError:
    #                     ...
    #                 if not missing_logged:
    #                     logs_container.add_stdout("Provider is not running, run a query to start it up...")
    #                 missing_logged = True
    #                 await asyncio.sleep(1)
    #
    #             if deploy.status.get("availableReplicas", 0) == 0:
    #                 async for _event_stream_type, event in api.watch(
    #                     kind="event",
    #                     # TODO: we select for only one pod, for multi-pod agents this might hold up the logs for a while
    #                     field_selector=f"involvedObject.name=={pods[0].name},involvedObject.kind==Pod",
    #                 ):
    #                     message = event.raw.get("message", "")
    #                     logs_container.add_stdout(f"{event.raw.reason}: {message}")
    #                     if event.raw.reason == "Started":
    #                         break
    #
    #             for _ in range(10):
    #                 try:
    #                     _ = [log async for log in pods[0].logs(tail_lines=1)]
    #                     break
    #                 except kr8s.ServerError:
    #                     await asyncio.sleep(1)
    #             else:
    #                 logs_container.add_stdout("Container crashed or not starting up, attempting to get previous logs:")
    #                 with suppress(kr8s.ServerError):
    #                     previous_logs = [log async for log in pods[0].logs(previous=True)]
    #                     if previous_logs:
    #                         logs_container.add_stdout("Previous container logs:")
    #                         for log in previous_logs:
    #                             logs_container.add_stdout(f"Previous: {log}")
    #                 return
    #
    #             # Stream logs from pods
    #             async def stream_logs(pod: Pod):
    #                 async for line in pod.logs(follow=True):
    #                     logs_container.add_stdout(
    #                         f"{pod.name.replace(self._get_k8s_name(provider_id, TemplateKind.DEPLOY), '')}: {line}"
    #                     )
    #
    #             async with TaskGroup() as tg:
    #                 for pod in await deploy.pods():
    #                     tg.create_task(stream_logs(pod))
    #
    #     except Exception as ex:
    #         logs_container.add(
    #             ProcessLogMessage(stream=ProcessLogType.STDERR, message=extract_messages(ex), error=True)
    #         )
    #         logger.error(f"Error while streaming logs: {extract_messages(ex)}")
    #         raise
