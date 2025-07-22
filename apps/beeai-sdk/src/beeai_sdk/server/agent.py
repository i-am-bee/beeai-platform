from typing import NamedTuple

from a2a.server.agent_execution import AgentExecutor
from a2a.types import AgentCard


class Agent(NamedTuple):
    card: AgentCard
    executor: AgentExecutor
