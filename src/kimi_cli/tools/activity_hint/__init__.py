from pathlib import Path
from typing import override

from kosong.tooling import CallableTool2, ToolReturnValue
from pydantic import BaseModel, Field

from kimi_cli.soul.agent import Runtime
from kimi_cli.tools.utils import load_desc
from kimi_cli.utils.logging import logger
from kimi_cli.wire.types import StatusUpdate


class Params(BaseModel):
    hint: str = Field(
        description="A one-sentence description of what the agent is currently doing (≤15 words).",
        min_length=1,
        max_length=80,
    )


class SetActivityHint(CallableTool2[Params]):
    name: str = "SetActivityHint"
    description: str = load_desc(Path(__file__).parent / "set_activity_hint.md")
    params: type[Params] = Params

    def __init__(self, runtime: Runtime) -> None:
        super().__init__()
        self._runtime = runtime

    @override
    async def __call__(self, params: Params) -> ToolReturnValue:
        old = self._runtime.activity_hint
        self._runtime.activity_hint = params.hint
        logger.debug(
            "Activity hint updated: {old} → {new}",
            old=old or "(empty)",
            new=params.hint,
        )
        # Push the update to the UI wire so the status bar refreshes immediately
        from kimi_cli.soul import wire_send

        wire_send(StatusUpdate(activity=params.hint))
        return ToolReturnValue(
            is_error=False,
            output="",
            message="",
            display=[],
        )
