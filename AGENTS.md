# Kimi Code CLI

## Project overview

Kimi Code CLI is an AI agent that runs in the terminal, helping users complete software development tasks and terminal operations. It can read and edit code, execute shell commands, search and fetch web pages, and autonomously plan and adjust actions during execution.

The project is a Python-centric monorepo with multiple workspace packages, a React/TypeScript web UI, a visualization UI, and VitePress documentation. It ships as both PyPI packages (`kimi-cli`, `kimi-code`) and standalone PyInstaller binaries for Linux, macOS, and Windows.

Key capabilities:
- Interactive shell TUI with slash commands, autocomplete, and clipboard image paste
- ACP (Agent Client Protocol) server mode for IDE integrations (VS Code, Zed, JetBrains)
- MCP (Model Context Protocol) tool loading for extensible external tool integrations
- Web UI (FastAPI + React) for browser-based interaction
- Subagent system for delegating tasks to specialized agent instances
- Background task execution with notifications
- Plugin system for third-party extensions

## Quick commands

All Python workflow commands go through `uv`. Node.js/npm is required for web, vis, and docs development.

```bash
# Prepare development environment (sync deps + install git hooks)
make prepare

# Formatting
make format              # Format all Python packages + web
make format-kimi-cli     # Format only kimi-cli sources (ruff)
make format-web          # Format web sources (biome)

# Linting and type checking
make check               # Check all packages
make check-kimi-cli      # ruff + pyright + ty (ty is non-blocking)
make check-web           # biome lint + tsc typecheck

# Testing
make test                # Run all Python test suites
make test-kimi-cli       # Run tests/ + tests_e2e/ with pytest
make ai-test             # Run the AI test suite (tests_ai/)

# Building
make build               # Build all Python packages for release
make build-bin           # Build standalone PyInstaller binary (one-file)
make build-bin-onedir    # Build standalone PyInstaller binary (one-dir)
make build-web           # Build web UI and sync into package
make build-vis           # Build vis UI and sync into package

# Running services locally
make web-back            # Start web backend (uvicorn reload, port 5494)
make web-front           # Start web frontend (vite dev server)
make vis-back            # Start vis backend (uvicorn reload, port 5495)
make vis-front           # Start vis frontend (vite dev server)

# Generating artifacts
make gen-changelog       # Generate changelog with kimi --yolo --prompt /skill:gen-changelog
make gen-docs            # Generate user docs with kimi --yolo --prompt /skill:gen-docs
```

If running tools directly, use `uv run ...`.

## Technology stack

### Core (Python)
- **Python**: >=3.12 (CI tests 3.12, 3.13, 3.14; type checking targets 3.14)
- **CLI framework**: Typer
- **Async runtime**: asyncio
- **LLM framework**: kosong (workspace package) — abstraction over OpenAI, Anthropic, Google GenAI
- **MCP integration**: fastmcp (v3.x)
- **Web backend**: FastAPI + uvicorn + scalar-fastapi
- **WebSocket**: websockets
- **HTTP client**: httpx[socks], aiohttp
- **Data validation**: pydantic
- **Configuration**: tomlkit, pyyaml
- **Logging**: loguru
- **TUI**: prompt-toolkit, rich
- **Image processing**: pillow
- **Web scraping**: trafilatura
- **OS abstraction**: pykaos (workspace package) — local + SSH file/shell operations
- **Keyring**: keyring (for OAuth token storage)

### Web / Vis frontend
- **Framework**: React 19 + TypeScript 5.9
- **Build tool**: Vite 7
- **Styling**: Tailwind CSS 4 + tw-animate-css
- **UI components**: Radix UI primitives + shadcn/ui
- **State management**: zustand, swr
- **Code editing**: CodeMirror (@uiw/react-codemirror)
- **Diff rendering**: diff + gitdiff-parser
- **Markdown streaming**: streamdown
- **Syntax highlighting**: shiki, refractor
- **Lint/format**: Biome 2.3.8
- **Diagrams**: @xyflow/react (React Flow)

### Documentation
- **Framework**: VitePress 1.5
- **Diagrams**: mermaid

### Package management / build
- **Python**: uv (v0.8.5) + uv_build
- **Node**: npm (Node 20)
- **Binary packaging**: PyInstaller 6.18.0
- **Nix**: flake.nix with uv2nix for reproducible builds

### Quality tools
- **Lint + format**: ruff (E, F, UP, B, SIM, I rules; line length 100)
- **Type checking**: pyright (strict for src/), ty (non-blocking)
- **Tests**: pytest + pytest-asyncio
- **Snapshots**: inline-snapshot[black]
- **Pre-commit**: make format-kimi-cli + make check-kimi-cli

## Monorepo workspace packages

| Package | Path | Description |
|---------|------|-------------|
| `kimi-cli` | root (`src/kimi_cli/`) | Main CLI application |
| `kimi-code` | `packages/kimi-code/` | Thin wrapper that depends on `kimi-cli==X.Y.Z`; provides `kimi-code` entry point |
| `kosong` | `packages/kosong/` | LLM abstraction layer — message structures, async tool orchestration, chat providers |
| `pykaos` | `packages/kaos/` | OS abstraction layer — file ops and command execution (local / SSH) |
| `kimi-sdk` | `sdks/kimi-sdk/` | Lightweight Python SDK for the Kimi API |

All packages share the same build backend (`uv_build`), line length (100), ruff rules, and pyright/ty config patterns. Versions are kept in sync where packages depend on each other.

## Architecture overview

### CLI entry and app setup
- `src/kimi_cli/__main__.py`: Entry point; installs crash handlers, normalizes proxy env, routes to CLI.
- `src/kimi_cli/cli/__init__.py`: Typer CLI definition; parses flags (UI mode, agent spec, config, MCP) and routes into `KimiCLI`.
- `src/kimi_cli/app.py`: `KimiCLI.create(...)` and `KimiCLI.run(...)` are the main programmatic entrypoints.

### Runtime and agent loop
- `src/kimi_cli/soul/agent.py`: `Runtime` (config, session, builtins), `Agent` (system prompt + toolset), and `LaborMarket` (builtin subagent type registry).
- `src/kimi_cli/soul/kimisoul.py`: `KimiSoul.run(...)` is the main agent loop boundary; emits Wire messages and executes tools via `KimiToolset`.
- `src/kimi_cli/soul/context.py`: Conversation history + checkpoints; used by DMail for checkpointed replies.
- `src/kimi_cli/soul/toolset.py`: Loads tools by import path, injects dependencies, and runs tool calls. Bridges to MCP tools.
- `src/kimi_cli/soul/compaction.py`: Context compaction when token limits are approached.
- `src/kimi_cli/soul/approval.py`: Tool-facing approval facade.
- `src/kimi_cli/soul/slash.py`: Soul-level slash commands.

### Agent specs and subagents
- `src/kimi_cli/agentspec.py`: Loads YAML agent specs.
- `src/kimi_cli/agents/`: Built-in agent YAML specs and system prompts. Specs can `extend` base agents, select tools by import path, and register builtin subagent types via the `subagents` field.
- `src/kimi_cli/tools/agent/`: The `Agent` tool creates or resumes subagent instances.
- `src/kimi_cli/subagents/`: `SubagentStore` persists instance metadata, prompts, wire logs, and context under `session/subagents/<agent_id>/`.

### Tools
- `src/kimi_cli/tools/`: Built-in tools — agent, ask_user, background, dmail, file, plan, shell, think, todo, web.
- MCP tools are loaded via `fastmcp`; CLI management is in `src/kimi_cli/mcp.py` and `src/kimi_cli/mcp_oauth.py`.

### UI / Wire
- `src/kimi_cli/soul/run_soul`: Connects `KimiSoul` to a `Wire` so UI loops can stream events.
- `src/kimi_cli/wire/`: Event types, protocol, JSON-RPC, transport between soul and UI.
- `src/kimi_cli/ui/shell/`: Interactive TUI (default); handles input, shell command mode, slash command autocomplete.
- `src/kimi_cli/ui/print/`: Non-interactive print mode.
- `src/kimi_cli/ui/acp/`: ACP server frontend.

### Web and Vis
- `src/kimi_cli/web/`: FastAPI application serving the React web UI and REST API.
  - `web/app.py`: FastAPI app factory with CORS, gzip, auth middleware.
  - `web/api/`: REST routers (sessions, config, open_in, work_dirs).
  - `web/runner/`: Manages subprocess runners for web-based sessions.
  - `web/store/`: Session store for web UI.
- `src/kimi_cli/vis/`: FastAPI application for visualization UI (session statistics, etc.).
- `web/`: React frontend source code (Vite + Tailwind + shadcn/ui).
- `vis/`: React visualization frontend.

> **注意**：修改 `web/` 或 `vis/` 目录下的前端源码后，必须运行 `make build-web`（或 `make build-vis`）重新构建，并将产物同步到 `src/kimi_cli/web/static/`（或 `src/kimi_cli/vis/static/`）。未重新构建直接运行后端会导致前端页面加载失败。

### ACP server
- `src/kimi_cli/acp/`: Agent Client Protocol server components for IDE integration.

### Supporting systems
- `src/kimi_cli/auth/`: OAuth and platform authentication.
- `src/kimi_cli/background/`: Background task manager, worker, and store.
- `src/kimi_cli/notifications/`: Notification manager and wire bridge.
- `src/kimi_cli/telemetry/`: Crash reporting and telemetry.
- `src/kimi_cli/plugin/`: Plugin manager and tool loading.
- `src/kimi_cli/skill/`: Skill registry and flow execution.
- `src/kimi_cli/hooks/`: Hook engine and runner.

## Code organization

```
src/kimi_cli/
  __main__.py              # CLI entry point
  app.py                   # KimiCLI orchestration
  cli/                     # Typer CLI commands (mcp, plugin, web, vis, export, etc.)
  agents/                  # Built-in agent specs (YAML + system prompts)
  agentspec.py             # Agent spec loader
  config.py                # User configuration (~/.kimi/config.toml)
  llm.py                   # Model/provider selection
  mcp.py, mcp_oauth.py     # MCP tool management and OAuth
  soul/                    # Core agent runtime
    agent.py               # Runtime, Agent, LaborMarket
    kimisoul.py            # Main agent loop
    context.py             # Conversation history
    toolset.py             # Tool loading and execution
    compaction.py          # Context compaction
    approval.py            # Approval facade
    slash.py               # Soul-level slash commands
    run_soul.py            # Wire connection setup
  tools/                   # Built-in tool implementations
  ui/                      # Frontends (shell, print, acp)
  wire/                    # Event protocol and transport
  web/                     # FastAPI web backend
  vis/                     # FastAPI vis backend
  acp/                     # ACP server
  auth/                    # Authentication
  background/              # Background tasks
  notifications/           # Notifications
  telemetry/               # Crash/telemetry
  plugin/                  # Plugin system
  skill/                   # Skills and flows
  skills/                  # Built-in skills (kimi-cli-help, skill-creator)
  subagents/               # Subagent persistence
  utils/                   # Utilities (rich rendering, path, env, etc.)
```

## Testing strategy

### Test suites
- `tests/`: Unit and integration tests for kimi-cli. Organized by module (e.g., `tests/core/`, `tests/tools/`, `tests/ui/`, `tests/web/`, `tests/auth/`, `tests/background/`).
- `tests_e2e/`: End-to-end wire protocol tests. These test the full soul+wire loop without a real LLM (mocked). Files are named `test_wire_*.py`.
- `tests_ai/`: AI-powered smoke tests that run the actual CLI against real prompts and verify behavior.

### Running tests
```bash
make test-kimi-cli        # tests/ + tests_e2e/
make test-kosong          # kosong package (+ doctests)
make test-pykaos          # pykaos package
make test-kimi-sdk        # kimi-sdk package
make ai-test              # AI smoke tests
```

### Test conventions
- Test files: `tests/test_*.py`
- Use pytest + pytest-asyncio for async tests.
- `tests/conftest.py` contains shared fixtures.
- E501 (line too long) is ignored in `tests/` and `tests_e2e/`.

## Development conventions

### Python style
- Line length: 100
- Ruff rules: E, F, UP, B, SIM, I
- Import sorting via ruff (isort compatible)
- Type checking: pyright in strict mode for `src/kimi_cli/**/*.py`; standard mode for tests.
- `from __future__ import annotations` is used in source files.
- FastAPI `Depends()` usage is allowed despite B008 (see `per-file-ignores`).

### Git hooks
Pre-commit hooks run `make format-kimi-cli` and `make check-kimi-cli` automatically. They are installed via `prek` (a uv tool) during `make prepare`.

### Git commit messages
Use Conventional Commits:

```
<type>(<scope>): <subject>
```

Allowed types: `feat`, `fix`, `test`, `refactor`, `chore`, `style`, `docs`, `perf`, `build`, `ci`, `revert`.

### Versioning
**Minor-bump-only** scheme (`MAJOR.MINOR.PATCH`):
- Patch is always `0`. Never bump it.
- Minor is bumped for any change (features, improvements, bug fixes).
- Major is only changed by explicit manual decision.

Applies to all packages: root, `packages/*`, `sdks/*`.

### Environment / config
- User config: `~/.kimi/config.toml`
- Logs, sessions, and MCP config live in `~/.kimi/`
- OAuth MCP tokens stored in `~/.kimi/mcp-oauth/` (FastMCP 3 persistent storage)

## CI / CD

### GitHub Actions workflows
- `ci-kimi-cli.yml`: Checks (Python 3.14), tests (3.12–3.14), binary builds (Linux x64/ARM, macOS ARM, Windows x64), release validation, and Nix tests.
- `ci-kosong.yml`, `ci-pykaos.yml`, `ci-kimi-sdk.yml`: Independent CI for workspace packages.
- `ci-docs.yml`: Builds VitePress docs.
- `docs-pages.yml`: Deploys docs to GitHub Pages.
- `release-kimi-cli.yml`: Triggered on version tags (`[0-9]*`). Builds signed binaries for all platforms, uploads to GitHub Releases, and publishes to PyPI.
- `release-kosong.yml`, `release-pykaos.yml`, `release-kimi-sdk.yml`: Package-specific releases.
- `pr-title-checker.yml`: Validates PR titles follow conventions.
- `translator.yml`: Documentation translation automation.
- `typos.yml`: Spell checking.

### Binary distribution
PyInstaller builds `kimi` as a standalone executable:
- **One-file**: `make build-bin` → `dist/onefile/kimi`
- **One-dir**: `make build-bin-onedir` → `dist/onedir/kimi/`
- macOS binaries are code-signed in CI via `APPLE_SIGNING_IDENTITY`.
- Build SHA is injected at build time via `scripts/inject_build_sha.py`.

### Nix
A `flake.nix` is provided for reproducible builds. CI runs `nix run .#kimi-cli -- --version` on Linux x64/ARM and macOS ARM.

## Deployment processes

### PyPI release
1. Ensure `main` is up to date.
2. Create a release branch (e.g., `bump-1.44`).
3. Update `CHANGELOG.md`: add a new `## 1.44 (YYYY-MM-DD)` section below `## Unreleased` (do not rename `## Unreleased`).
4. Update `pyproject.toml` version (and `packages/kimi-code/pyproject.toml` to match).
5. Run `uv sync` to align `uv.lock`.
6. Commit, open PR, merge.
7. Switch back to `main`, pull latest.
8. Tag and push: `git tag 1.44 && git push --tags`
9. GitHub Actions handles the rest (validate, build binaries, upload to GitHub Releases, publish to PyPI).

### Web UI release
The web frontend is built with `make build-web` and embedded into the Python package as static files. The vis UI is similarly built with `make build-vis`.

> **开发约束**：任何修改了 `web/`、`vis/` 或 `src/kimi_cli/web/`、`src/kimi_cli/vis/` 的 PR，在提交前必须执行对应的构建命令（`make build-web` / `make build-vis`），确保静态资源已同步到 Python 包目录。CI 不会自动代为构建前端资源。

## Security considerations

- **OAuth tokens**: Stored in the system keyring when possible; OAuth MCP tokens use FastMCP 3 persistent storage in `~/.kimi/mcp-oauth/`.
- **Shell execution**: The Shell tool runs arbitrary commands. Approvals are required by default unless `--yolo` or `--afk` is active.
- **File access**: File tools operate within the working directory. Absolute paths outside the working directory require explicit approval.
- **Windows defense**: On Windows, hallucinated CMD-style `2>nul` redirects are rewritten to `2>/dev/null` to avoid creating files named `nul` (a reserved device name).
- **Dependencies**: Pillow is pinned to address known CVEs. Dependencies are generally pinned or tightly bounded in `pyproject.toml`.
- **Proxy normalization**: `normalize_proxy_env()` is called early in startup to ensure consistent proxy behavior.
- **Crash reporting**: `install_crash_handlers()` captures unhandled exceptions for telemetry.

## Useful reference

- CLI entry points: `kimi` / `kimi-cli` → `src/kimi_cli/__main__.py`
- Built-in skills location: `src/kimi_cli/skills/`
- Project skills location: `.agents/skills/`
- User skills location: `~/.claude/skills/` (or similar, depending on the agent environment)
- KLIPs (improvement proposals): `klips/`
- Documentation source: `docs/` (VitePress, bilingual en/zh)
