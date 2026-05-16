"""Interactive skill picker for enabling/disabling skills.

Provides a full-screen prompt_toolkit Application that lets the user browse
all discovered skills and toggle them on/off with the space bar.
"""

from __future__ import annotations

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Frame

from kimi_cli.skill import Skill, normalize_skill_name


def _scope_label(scope: str) -> str:
    labels = {
        "builtin": "Built-in",
        "user": "User",
        "project": "Project",
        "extra": "Extra",
    }
    return labels.get(scope, scope)


class SkillPickerApp:
    """Full-screen skill picker with space-to-toggle and escape-to-exit."""

    def __init__(
        self,
        *,
        skills: dict[str, Skill],
        disabled: set[str],
    ) -> None:
        self._skills = sorted(skills.values(), key=lambda s: (s.scope, s.name))
        self._disabled = set(disabled)
        self._selected_index = 0
        self._app = self._build_app()

    async def run(self) -> set[str]:
        """Run the picker and return the updated disabled skill names."""
        await self._app.run_async()
        return self._disabled

    def _header_fragments(self) -> StyleAndTextTuples:
        total = len(self._skills)
        disabled_count = len(self._disabled)
        enabled_count = total - disabled_count
        return [
            ("class:header.title", " SKILLS "),
            (
                "class:header.meta",
                f" [{enabled_count} enabled, {disabled_count} disabled] ",
            ),
        ]

    def _footer_fragments(self) -> StyleAndTextTuples:
        return [
            ("class:footer.text", " "),
            ("class:footer.text", "Up/Down to navigate"),
            ("class:footer.text", " \u00b7 "),
            ("class:footer.text", "Space to toggle"),
            ("class:footer.text", " \u00b7 "),
            ("class:footer.text", "Esc to save and exit "),
        ]

    def _list_fragments(self) -> StyleAndTextTuples:
        fragments: StyleAndTextTuples = []
        current_scope: str | None = None
        for idx, skill in enumerate(self._skills):
            if skill.scope != current_scope:
                current_scope = skill.scope
                fragments.append(("class:scope.header", f"\n{_scope_label(current_scope)}\n"))

            is_disabled = normalize_skill_name(skill.name) in self._disabled
            is_selected = idx == self._selected_index

            checkbox = "[✗]" if is_disabled else "[✓]"
            name = skill.name
            desc = skill.description or ""

            if is_selected:
                prefix = "> "
                style = "class:item.selected"
                checkbox_style = "class:checkbox.selected"
                name_style = "class:name.selected"
            else:
                prefix = "  "
                style = "class:item"
                checkbox_style = "class:checkbox"
                name_style = "class:name"

            fragments.append((style, prefix))
            fragments.append((checkbox_style, checkbox))
            fragments.append((style, " "))
            fragments.append((name_style, name))
            if desc:
                fragments.append((style, f"  \u2014 {desc}"))
            fragments.append((style, "\n"))

        if not self._skills:
            fragments.append(("class:empty", "No skills found."))

        return fragments

    def _move_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1

    def _move_down(self) -> None:
        if self._selected_index < len(self._skills) - 1:
            self._selected_index += 1

    def _toggle_current(self) -> None:
        if not self._skills:
            return
        skill = self._skills[self._selected_index]
        key = normalize_skill_name(skill.name)
        if key in self._disabled:
            self._disabled.discard(key)
        else:
            self._disabled.add(key)

    def _build_app(self) -> Application[None]:
        kb = KeyBindings()

        @kb.add("escape")
        @kb.add("c-c")
        def _exit(event: KeyPressEvent) -> None:
            event.app.exit(result=None)

        @kb.add("up")
        def _up(event: KeyPressEvent) -> None:
            self._move_up()

        @kb.add("down")
        def _down(event: KeyPressEvent) -> None:
            self._move_down()

        @kb.add("space")
        def _toggle(event: KeyPressEvent) -> None:
            self._toggle_current()

        # Mark handlers as used
        _ = (_exit, _up, _down, _toggle)

        header = Window(
            FormattedTextControl(self._header_fragments),
            height=1,
            style="class:header",
        )
        body = Frame(
            Box(
                Window(
                    FormattedTextControl(self._list_fragments),
                    wrap_lines=False,
                ),
                padding=1,
            ),
            title=lambda: " Skills ",
        )
        footer = Window(
            FormattedTextControl(self._footer_fragments),
            height=1,
            style="class:footer",
        )

        return Application(
            layout=Layout(HSplit([header, body, footer])),
            key_bindings=kb,
            full_screen=True,
            erase_when_done=True,
            mouse_support=False,
            style=Style.from_dict(
                {
                    "header": "bg:#005f87 fg:#ffffff",
                    "header.title": "bold",
                    "header.meta": "",
                    "footer": "bg:#3a3a3a fg:#bcbcbc",
                    "scope.header": "bold fg:#00afff",
                    "item": "fg:#d0d0d0",
                    "item.selected": "bg:#005f87 fg:#ffffff",
                    "checkbox": "fg:#878787",
                    "checkbox.selected": "fg:#ffffff bold",
                    "name": "fg:#afffff bold",
                    "name.selected": "fg:#ffffff bold",
                    "empty": "fg:#878787 italic",
                }
            ),
        )
