from pathlib import Path
from typing import override

from kosong.tooling import CallableTool2, ToolReturnValue
from pydantic import BaseModel, Field

from kimi_cli.soul.agent import Runtime
from kimi_cli.tools.utils import load_desc
from kimi_cli.utils.logging import logger
from kimi_cli.utils.proctitle import set_terminal_title


class Params(BaseModel):
    title: str = Field(
        description="A short task title (≤5 words) shown in the terminal tab.",
        min_length=1,
        max_length=40,
    )


class SetTerminalTitle(CallableTool2[Params]):
    name: str = "SetTerminalTitle"
    description: str = load_desc(Path(__file__).parent / "set_terminal_title.md")
    params: type[Params] = Params

    def __init__(self, runtime: Runtime) -> None:
        super().__init__()
        self._runtime = runtime

    @override
    async def __call__(self, params: Params) -> ToolReturnValue:
        old = self._runtime.terminal_title
        self._runtime.terminal_title = params.title
        set_terminal_title(params.title)
        logger.debug(
            "Terminal title updated: {old} → {new}",
            old=old or "(empty)",
            new=params.title,
        )
        return ToolReturnValue(
            is_error=False,
            output="",
            message="",
            display=[],
        )
