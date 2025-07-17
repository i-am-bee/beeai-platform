from pydantic import BaseModel, Field
from beeai_framework.tools import Tool, ToolRunOptions, StringToolOutput
from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter

class ClarificationSchema(BaseModel):
    thoughts: str = Field(..., description="")
    next_step: list[str] = Field(..., description="", min_length=1)



class ClarificationTool(Tool[ClarificationSchema]):
    name = "clarification"
    description = "Use when you are unsure which tool to use next."  # noqa: E501

    def __init__(self, *, extra_instructions: str = "") -> None:
        super().__init__()
        if extra_instructions:
            self.description += f" {extra_instructions}"

    @property
    def input_schema(self) -> type[ClarificationSchema]:
        return ClarificationSchema

    async def _run(self, input: ClarificationSchema, options: ToolRunOptions | None, context: RunContext) -> StringToolOutput:
        return StringToolOutput("Ask the user for clarification.")

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "clarification"],
            creator=self,
        )
