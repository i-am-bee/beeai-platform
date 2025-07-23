from typing import Union

from a2a.types import Message, Part, TaskStatus

RunYield = Union[Message, Part, TaskStatus, str, None, Exception]
RunYieldResume = Message
