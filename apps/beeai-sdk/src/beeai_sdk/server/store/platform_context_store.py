from a2a.types import AgentExtension, Artifact, Message

from beeai_sdk.a2a.extensions.services.platform import PlatformApiExtensionServer, PlatformApiExtensionSpec
from beeai_sdk.server.dependencies import Depends
from beeai_sdk.server.store.context_store import ContextStore, ContextStoreInstance


class PlatformContextStore(ContextStore):
    def modify_extensions(self, extensions: list[AgentExtension]) -> list[AgentExtension]:
        platform_extension_found = False
        for extension in extensions:
            if extension.uri == PlatformApiExtensionSpec.URI:
                extension.required = True
                platform_extension_found = True
        return (
            extensions
            if platform_extension_found
            else [
                *extensions,
                *PlatformApiExtensionSpec().to_agent_card_extensions(required=True),
            ]
        )

    async def create(self, context_id: str, dependencies: list[Depends]) -> tuple[ContextStoreInstance, list[Depends]]:
        sdk_extensions = [dep.extension for dep in dependencies if dep.extension is not None]
        extra_deps = []
        platform_extension: PlatformApiExtensionServer

        for extension in sdk_extensions:
            if isinstance(extension, PlatformApiExtensionServer):
                platform_extension = extension
                break
        else:
            platform_extension = PlatformApiExtensionServer(PlatformApiExtensionSpec())
            extra_deps.append(Depends(platform_extension))
        return PlatformContextStoreInstance(context_id=context_id, platform_extension=platform_extension), extra_deps


class PlatformContextStoreInstance(ContextStoreInstance):
    def __init__(self, context_id: str, platform_extension: PlatformApiExtensionServer):
        self._context_id = context_id
        self._platform_extension = platform_extension

    async def load_history(self) -> list[Message | Artifact]: ...
    async def store(self, data: Message | Artifact) -> None: ...
    async def store_metadata_value(self, key: str, value: str): ...
    async def get_metadata_value(self, key: str) -> str | None: ...
