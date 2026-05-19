from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast
from uuid import UUID

import pytest
from kaos.path import KaosPath

from kimi_cli.session import Session
from kimi_cli.session_state import load_session_state, save_session_state
from kimi_cli.web.api import sessions as sessions_api
from kimi_cli.web.models import GenerateTitleRequest

if TYPE_CHECKING:
    from kimi_cli.web.runner.process import KimiCLIRunner


@pytest.fixture
def isolated_share_dir(monkeypatch, tmp_path: Path) -> Path:
    share_dir = tmp_path / "share"
    share_dir.mkdir()

    def _get_share_dir() -> Path:
        share_dir.mkdir(parents=True, exist_ok=True)
        return share_dir

    monkeypatch.setattr("kimi_cli.share.get_share_dir", _get_share_dir)
    monkeypatch.setattr("kimi_cli.metadata.get_share_dir", _get_share_dir)
    return share_dir


@pytest.fixture
def work_dir(tmp_path: Path) -> KaosPath:
    path = tmp_path / "work"
    path.mkdir()
    return KaosPath.unsafe_from_local_path(path)


class _FakeRunner:
    """Stand-in for ``KimiCLIRunner`` for tests that bypass FastAPI dependency injection."""

    def get_session(self, _session_id: UUID) -> None:
        return None


@pytest.mark.anyio
async def test_generate_title_returns_existing_when_already_generated(
    isolated_share_dir: Path,
    work_dir: KaosPath,
) -> None:
    """If title was already set by SetTerminalTitle or manual rename, return it."""
    session = await Session.create(work_dir)

    state = load_session_state(session.dir)
    state.custom_title = "Manual Title"
    state.title_generated = True
    save_session_state(state, session.dir)

    response = await sessions_api.generate_session_title(
        UUID(session.id),
        GenerateTitleRequest(user_message="some message", assistant_response="response"),
        runner=cast("KimiCLIRunner", _FakeRunner()),
    )

    state = load_session_state(session.dir)
    assert response.title == "Manual Title"
    assert state.custom_title == "Manual Title"
    assert state.title_generated is True
    assert state.title_generate_attempts == 0


@pytest.mark.anyio
async def test_generate_title_fallback_to_shortened_user_message(
    isolated_share_dir: Path,
    work_dir: KaosPath,
) -> None:
    """If no title is set, fallback to shortening the first user message."""
    session = await Session.create(work_dir)

    response = await sessions_api.generate_session_title(
        UUID(session.id),
        GenerateTitleRequest(user_message="debug the flaky web session rename issue"),
        runner=cast("KimiCLIRunner", _FakeRunner()),
    )

    state = load_session_state(session.dir)
    assert response.title == "debug the flaky web session rename issue"
    assert state.custom_title == "debug the flaky web session rename issue"
    assert state.title_generated is True
    assert state.title_generate_attempts == 0


@pytest.mark.anyio
async def test_generate_title_returns_untitled_when_no_message(
    isolated_share_dir: Path,
    work_dir: KaosPath,
) -> None:
    """If there is no user message, return 'Untitled'."""
    session = await Session.create(work_dir)

    response = await sessions_api.generate_session_title(
        UUID(session.id),
        GenerateTitleRequest(),
        runner=cast("KimiCLIRunner", _FakeRunner()),
    )

    state = load_session_state(session.dir)
    assert response.title == "Untitled"
    assert state.title_generated is False
    assert state.custom_title is None
