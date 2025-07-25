from typing import TypeAlias

from a2a.types import Artifact, Message, Part, TaskStatus

RunYield: TypeAlias = Message | Part | TaskStatus | Artifact | str | None | Exception
RunYieldResume: TypeAlias = Message


class ArtifactChunk(Artifact):
    last_chunk: bool = False
