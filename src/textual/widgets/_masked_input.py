from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Flag, auto
from typing import TYPE_CHECKING, Iterable, Pattern

from rich.console import RenderableType
from rich.segment import Segment
from rich.text import Text
from typing_extensions import Literal

from textual import events
from textual.strip import Strip

if TYPE_CHECKING:
    pass

from textual.reactive import Reactive, var
from textual.validation import ValidationResult, Validator
from textual.widgets._input import Input

InputValidationOn = Literal["blur", "changed", "submitted"]
"""Possible messages that trigger input validation."""


class _CharFlags(Flag):
    """Misc flags for a single template character definition"""

    NONE = 0
    """Empty flags value"""

    REQUIRED = auto()
    """Is this character required for validation?"""

    SEPARATOR = auto()
    """Is this character a separator?"""

    UPPERCASE = auto()
    """Char is forced to be uppercase"""

    LOWERCASE = auto()
    """Char is forced to be lowercase"""


_TEMPLATE_CHARACTERS = {
    "A": (r"[A-Za-z]", _CharFlags.REQUIRED),
    "a": (r"[A-Za-z]", None),
    "N": (r"[A-Za-z0-9]", _CharFlags.REQUIRED),
    "n": (r"[A-Za-z0-9]", None),
    "X": (r"[^ ]", _CharFlags.REQUIRED),
    "x": (r"[^ ]", None),
    "9": (r"[0-9]", _CharFlags.REQUIRED),
    "0": (r"[0-9]", None),
    "D": (r"[1-9]", _CharFlags.REQUIRED),
    "d": (r"[1-9]", None),
    "#": (r"[0-9+\-]", None),
    "H": (r"[A-Fa-f0-9]", _CharFlags.REQUIRED),
    "h": (r"[A-Fa-f0-9]", None),
    "B": (r"[0-1]", _CharFlags.REQUIRED),
    "b": (r"[0-1]", None),
}


class _Template(Validator):
    """Template mask enforcer."""

    @dataclass
    class CharDefinition:
        """Holds data for a single char of the template mask."""

        pattern: Pattern[str]
        """Compiled regular expression to check for matches."""

        flags: _CharFlags = _CharFlags.NONE
        """Flags defining special behaviors"""

        char: str = ""
        """Mask character (separator or blank or placeholder)"""

    def __init__(self, input: Input, template_str: str) -> None:
        """Initialise the mask enforcer, which is also a subclass of `Validator`.

        Args:
            input: The `MaskedInput` that owns this object.
            template_str: Template string controlling masked input behavior.
        """
        self.input = input
        self.template: list[_Template.CharDefinition] = []
        self.blank: str = " "
        escaped = False
        flags = _CharFlags.NONE
        template_chars: list[str] = list(template_str)

        while template_chars:
            char = template_chars.pop(0)
            if escaped:
                char_definition = self.CharDefinition(
                    re.compile(re.escape(char)), _CharFlags.SEPARATOR, char
                )
                escaped = False
            else:
                if char == "\\":
                    escaped = True
                    continue
                elif char == ";":
                    break

                new_flags = {
                    ">": _CharFlags.UPPERCASE,
                    "<": _CharFlags.LOWERCASE,
                    "!": _CharFlags.NONE,
                }.get(char, None)
                if new_flags is not None:
                    flags = new_flags
                    continue

                pattern, required_flag = _TEMPLATE_CHARACTERS.get(char, (None, None))
                if pattern:
                    char_flags = (
                        _CharFlags.REQUIRED if required_flag else _CharFlags.NONE
                    )
                    char_definition = self.CharDefinition(
                        re.compile(pattern), char_flags
                    )
                else:
                    char_definition = self.CharDefinition(
                        re.compile(re.escape(char)), _CharFlags.SEPARATOR, char
                    )

            char_definition.flags |= flags
            self.template.append(char_definition)

        if template_chars:
            self.blank = template_chars[0]

        if all(
            (_CharFlags.SEPARATOR in char_definition.flags)
            for char_definition in self.template
        ):
            raise ValueError(
                "Template must contain at least one non-separator character"
            )

        self.update_mask(input.placeholder)

    def validate(self, value: str) -> ValidationResult:
        """Checks if `value` matches this template, always returning a ValidationResult.

        Args:
            value: The string value to be validated.

        Returns:
            A ValidationResult with the validation outcome.

        """
        if self.check(value.ljust(len(self.template), chr(0)), False):
            return self.success()
        else:
            return self.failure("Value does not match template!", value)

    def check(self, value: str, allow_space: bool) -> bool:
        """Checks if `value matches this template, but returns result as a bool.

        Args:
            value: The string value to be validated.
            allow_space: Consider space character in `value` as valid.

        Returns:
            True if `value` is valid for this template, False otherwise.
        """
        for char, char_definition in zip(value, self.template):
            if (
                (_CharFlags.REQUIRED in char_definition.flags)
                and (not char_definition.pattern.match(char))
                and ((char != " ") or not allow_space)
            ):
                return False
        return True

    def insert_separators(self, value: str, cursor_position: int) -> tuple[str, int]:
        """Automatically inserts separators in `value` at `cursor_position` if expected, eventually advancing
        the current cursor position.

        Args:
            value: Current control value entered by user.
            cursor_position: Where to start inserting separators (if any).

        Returns:
            A tuple in the form `(value, cursor_position)` with new value and possibly advanced cursor position.
        """
        while cursor_position < len(self.template) and (
            _CharFlags.SEPARATOR in self.template[cursor_position].flags
        ):
            value = (
                value[:cursor_position]
                + self.template[cursor_position].char
                + value[cursor_position + 1 :]
            )
            cursor_position += 1
        return value, cursor_position

    def insert_text_at_cursor(self, text: str) -> tuple[str, int] | None:
        """Inserts `text` at current cursor position. If not present in `text`, any expected separator is automatically
        inserted at the correct position.

        Args:
            text: The text to be inserted.

        Returns:
            A tuple in the form `(value, cursor_position)` with the new control value and current cursor position if
                `text` matches the template, None otherwise.
        """
        value = self.input.value
        cursor_position = self.input.cursor_position
        separators = set(
            [
                char_definition.char
                for char_definition in self.template
                if _CharFlags.SEPARATOR in char_definition.flags
            ]
        )
        for char in text:
            if char in separators:
                if char == self.next_separator(cursor_position):
                    prev_position = self.prev_separator_position(cursor_position)
                    if (cursor_position > 0) and (prev_position != cursor_position - 1):
                        next_position = self.next_separator_position(cursor_position)
                        while cursor_position < next_position + 1:
                            if (
                                _CharFlags.SEPARATOR
                                in self.template[cursor_position].flags
                            ):
                                char = self.template[cursor_position].char
                            else:
                                char = " "
                            value = (
                                value[:cursor_position]
                                + char
                                + value[cursor_position + 1 :]
                            )
                            cursor_position += 1
                continue
            if cursor_position >= len(self.template):
                break
            char_definition = self.template[cursor_position]
            assert _CharFlags.SEPARATOR not in char_definition.flags
            if not char_definition.pattern.match(char):
                return None
            if _CharFlags.LOWERCASE in char_definition.flags:
                char = char.lower()
            elif _CharFlags.UPPERCASE in char_definition.flags:
                char = char.upper()
            value = value[:cursor_position] + char + value[cursor_position + 1 :]
            cursor_position += 1
            value, cursor_position = self.insert_separators(value, cursor_position)
        return value, cursor_position

    def move_cursor(self, delta: int) -> None:
        """Moves the cursor position by `delta` characters, skipping separators if
        running over them.

        Args:
            delta: The number of characters to move; positive moves right, negative
                moves left.
        """
        cursor_position = self.input.cursor_position
        if delta < 0 and all(
            [
                (_CharFlags.SEPARATOR in char_definition.flags)
                for char_definition in self.template[:cursor_position]
            ]
        ):
            return
        cursor_position += delta
        while (
            (cursor_position >= 0)
            and (cursor_position < len(self.template))
            and (_CharFlags.SEPARATOR in self.template[cursor_position].flags)
        ):
            cursor_position += delta
        self.input.cursor_position = cursor_position

    def delete_at_position(self, position: int | None = None) -> None:
        """Deletes character at `position`.

        Args:
            position: Position within the control value where to delete a character;
                if None the current cursor position is used.
        """
        value = self.input.value
        if position is None:
            position = self.input.cursor_position
        cursor_position = position
        if cursor_position < len(self.template):
            assert _CharFlags.SEPARATOR not in self.template[cursor_position].flags
            if cursor_position == len(value) - 1:
                value = value[:cursor_position]
            else:
                value = value[:cursor_position] + " " + value[cursor_position + 1 :]
        pos = len(value)
        while pos > 0:
            char_definition = self.template[pos - 1]
            if (_CharFlags.SEPARATOR not in char_definition.flags) and (
                value[pos - 1] != " "
            ):
                break
            pos -= 1
        value = value[:pos]
        if cursor_position > len(value):
            cursor_position = len(value)
        value, cursor_position = self.insert_separators(value, cursor_position)
        self.input.cursor_position = cursor_position
        self.input.value = value

    def at_separator(self, position: int | None = None) -> bool:
        """Checks if character at `position` is a separator.

        Args:
            position: Position within the control value where to check;
                if None the current cursor position is used.

        Returns:
            True if character is a separator, False otherwise.
        """
        if position is None:
            position = self.input.cursor_position
        if (position >= 0) and (position < len(self.template)):
            return _CharFlags.SEPARATOR in self.template[position].flags
        else:
            return False

    def prev_separator_position(self, position: int | None = None) -> int | None:
        """Obtains the position of the previous separator character starting from
        `position` within the template string.

        Args:
            position: Starting position from which to search previous separator.
                If None, current cursor position is used.

        Returns:
            The position of the previous separator, or None if no previous
                separator is found.
        """
        if position is None:
            position = self.input.cursor_position
        for index in range(position - 1, 0, -1):
            if _CharFlags.SEPARATOR in self.template[index].flags:
                return index
        else:
            return None

    def next_separator_position(self, position: int | None = None) -> int | None:
        """Obtains the position of the next separator character starting from
        `position` within the template string.

        Args:
            position: Starting position from which to search next separator.
                If None, current cursor position is used.

        Returns:
            The position of the next separator, or None if no next
                separator is found.
        """
        if position is None:
            position = self.input.cursor_position
        for index in range(position + 1, len(self.template)):
            if _CharFlags.SEPARATOR in self.template[index].flags:
                return index
        else:
            return None

    def next_separator(self, position: int | None = None) -> str | None:
        """Obtains the next separator character starting from `position`
        within the template string.

        Args:
            position: Starting position from which to search next separator.
                If None, current cursor position is used.

        Returns:
            The next separator character, or None if no next
                separator is found.
        """
        position = self.next_separator_position(position)
        if position is None:
            return None
        else:
            return self.template[position].char

    def display(self, value: str) -> str:
        """Returns `value` ready for display, with spaces replaced by
        placeholder characters.

        Args:
            value: String value to display.

        Returns:
            New string value with spaces replaced by placeholders.
        """
        result = []
        for char, char_definition in zip(value, self.template):
            if char == " ":
                char = char_definition.char
            result.append(char)
        return "".join(result)

    def update_mask(self, placeholder: str) -> None:
        """Updates template placeholder characters from `placeholder`. If
        given string is smaller than template string, template blank character
        is used to fill remaining template placeholder characters.

        Args:
            placeholder: New placeholder string.
        """
        for index, char_definition in enumerate(self.template):
            if _CharFlags.SEPARATOR not in char_definition.flags:
                if index < len(placeholder):
                    char_definition.char = placeholder[index]
                else:
                    char_definition.char = self.blank

    @property
    def mask(self) -> str:
        """Property returning the template placeholder mask."""
        return "".join([char_definition.char for char_definition in self.template])

    @property
    def empty_mask(self) -> str:
        """Property returning the template placeholder mask with all non-separators replaced by space."""
        return "".join(
            [
                (
                    " "
                    if (_CharFlags.SEPARATOR not in char_definition.flags)
                    else char_definition.char
                )
                for char_definition in self.template
            ]
        )


class MaskedInput(Input, can_focus=True):
    """A masked text input widget."""

    template: Reactive[str] = var("")
    """Input template mask currently in use."""

    def __init__(
        self,
        template: str,
        value: str | None = None,
        placeholder: str = "",
        *,
        validators: Validator | Iterable[Validator] | None = None,
        validate_on: Iterable[InputValidationOn] | None = None,
        valid_empty: bool = False,
        select_on_focus: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        tooltip: RenderableType | None = None,
    ) -> None:
        """Initialise the `Input` widget.

        Args:
            template: Template string.
            value: An optional default value for the input.
            placeholder: Optional placeholder text for the input.
            validators: An iterable of validators that the MaskedInput value will be checked against.
            validate_on: Zero or more of the values "blur", "changed", and "submitted",
                which determine when to do input validation. The default is to do
                validation for all messages.
            valid_empty: Empty values are valid.
            name: Optional name for the masked input widget.
            id: Optional ID for the widget.
            classes: Optional initial classes for the widget.
            disabled: Whether the input is disabled or not.
            tooltip: Optional tooltip.
        """
        self._template: _Template = None
        super().__init__(
            placeholder=placeholder,
            validators=validators,
            validate_on=validate_on,
            valid_empty=valid_empty,
            select_on_focus=select_on_focus,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

        self._template = _Template(self, template)
        self.template = template

        value, _ = self._template.insert_separators(value or "", 0)
        self.value = value
        if tooltip is not None:
            self.tooltip = tooltip

    def validate_value(self, value: str) -> str:
        """Validates value against template."""
        if self._template is None:
            return value
        if not self._template.check(value, True):
            raise ValueError("Value does not match template!")
        return value[: len(self._template.mask)]

    def _watch_template(self, template: str) -> None:
        """Revalidate when template changes."""
        self._template = _Template(self, template) if template else None
        if self.is_mounted:
            self._watch_value(self.value)

    def _watch_placeholder(self, placeholder: str) -> None:
        """Update template display mask when placeholder changes."""
        if self._template is not None:
            self._template.update_mask(placeholder)
            self.refresh()

    def validate(self, value: str) -> ValidationResult | None:
        """Run all the validators associated with this MaskedInput on the supplied value.

        Same as `Input.validate()` but also validates against template which acts as an
        additional implicit validator.

        Returns:
            A ValidationResult indicating whether *all* validators succeeded or not.
                That is, if *any* validator fails, the result will be an unsuccessful
                validation.
        """

        def set_classes() -> None:
            """Set classes for valid flag."""
            valid = self._valid
            self.set_class(not valid, "-invalid")
            self.set_class(valid, "-valid")

        result = super().validate(value)
        validation_results: list[ValidationResult] = [self._template.validate(value)]
        if result is not None:
            validation_results.append(result)
        combined_result = ValidationResult.merge(validation_results)
        self._valid = combined_result.is_valid
        set_classes()

        return combined_result

    def render_line(self, y: int) -> Strip:
        if y != 0:
            return Strip.blank(self.size.width)

        result = self._value
        width = self.content_size.width

        # Add the completion with a faded style.
        value = self.value
        value_length = len(value)
        template = self._template
        style = self.get_component_rich_style("input--placeholder")
        result += Text(
            template.mask[value_length:],
            style,
            end="",
        )
        for index, (char, char_definition) in enumerate(zip(value, template.template)):
            if char == " ":
                result.stylize(style, index, index + 1)

        if self._cursor_visible and self.has_focus:
            if self._cursor_at_end:
                result.pad_right(1)
            cursor_style = self.get_component_rich_style("input--cursor")
            cursor = self.cursor_position
            result.stylize(cursor_style, cursor, cursor + 1)

        segments = list(result.render(self.app.console))
        line_length = Segment.get_line_length(segments)
        if line_length < width:
            segments = Segment.adjust_line_length(segments, width)
            line_length = width

        strip = Strip(segments).crop(self.scroll_offset.x, self.scroll_offset.x + width)
        return strip.apply_style(self.rich_style)

    @property
    def _value(self) -> Text:
        """Value rendered as text."""
        value = self._template.display(self.value)
        return Text(value, no_wrap=True, overflow="ignore", end="")

    async def _on_click(self, event: events.Click) -> None:
        """Ensure clicking on value does not leave cursor on a separator."""
        await super()._on_click(event)
        if self._template.at_separator():
            self._template.move_cursor(1)

    def insert_text_at_cursor(self, text: str) -> None:
        """Insert new text at the cursor, move the cursor to the end of the new text.

        Args:
            text: New text to insert.
        """

        new_value = self._template.insert_text_at_cursor(text)
        if new_value is not None:
            self.value, self.cursor_position = new_value
        else:
            self.restricted()

    def replace(self, text: str, start: int, end: int):
        """Replace the text between the start and end locations with the given text.

        Args:
            text: Text to replace the existing text with.
            start: Start index to replace (inclusive).
            end: End index to replace (inclusive).
        """

        self.cursor_position = start
        # Handle case where cursor start on a separator
        self._template.move_cursor(1)
        self._template.move_cursor(-1)
        if self.cursor_position < start:
            self._template.move_cursor(1)

        for char in text:
            if self.cursor_position >= end:
                return
            new_value_cursor_position = self._template.insert_text_at_cursor(char)
            if new_value_cursor_position is None:
                self.restricted()
                return
            self.value, self.cursor_position = new_value_cursor_position

        last_cursor_position = self.cursor_position
        while self.cursor_position < min(end, len(self.value)):
            self._template.delete_at_position()
            self._template.move_cursor(1)
        self.cursor_position = last_cursor_position

    def clear(self) -> None:
        """Clear the masked input."""
        self.value, self.cursor_position = self._template.insert_separators("", 0)

    def action_cursor_left(self) -> None:
        """Move the cursor one position to the left; separators are skipped."""
        self._template.move_cursor(-1)

    def action_cursor_right(self) -> None:
        """Move the cursor one position to the right; separators are skipped."""
        self._template.move_cursor(1)

    def action_home(self) -> None:
        """Move the cursor to the start of the input."""
        self._template.move_cursor(-len(self.template))

    def action_cursor_left_word(self) -> None:
        """Move the cursor left next to the previous separator. If no previous
        separator is found, moves the cursor to the start of the input."""
        if self._template.at_separator(self.cursor_position - 1):
            position = self._template.prev_separator_position(self.cursor_position - 1)
        else:
            position = self._template.prev_separator_position()
        if position:
            position += 1
        self.cursor_position = position or 0

    def action_cursor_right_word(self) -> None:
        """Move the cursor right next to the next separator. If no next
        separator is found, moves the cursor to the end of the input."""
        position = self._template.next_separator_position()
        if position is None:
            self.cursor_position = len(self._template.mask)
        else:
            self.cursor_position = position + 1

    def action_delete_right(self) -> None:
        """Delete one character at the current cursor position."""
        self._template.delete_at_position()

    def action_delete_right_word(self) -> None:
        """Delete the current character and all rightward to next separator or
        the end of the input."""
        position = self._template.next_separator_position()
        if position is not None:
            position += 1
        else:
            position = len(self.value)
        for index in range(self.cursor_position, position):
            self.cursor_position = index
            if not self._template.at_separator():
                self._template.delete_at_position()

    def action_delete_left(self) -> None:
        """Delete one character to the left of the current cursor position."""
        if self.cursor_position <= 0:
            # Cursor at the start, so nothing to delete
            return
        self._template.move_cursor(-1)
        self._template.delete_at_position()

    def action_delete_left_word(self) -> None:
        """Delete leftward of the cursor position to the previous separator or
        the start of the input."""
        if self.cursor_position <= 0:
            return
        if self._template.at_separator(self.cursor_position - 1):
            position = self._template.prev_separator_position(self.cursor_position - 1)
        else:
            position = self._template.prev_separator_position()
        if position:
            position += 1
        else:
            position = 0
        for index in range(position, self.cursor_position):
            self.cursor_position = index
            if not self._template.at_separator():
                self._template.delete_at_position()
        self.cursor_position = position

    def action_delete_left_all(self) -> None:
        """Delete all characters to the left of the cursor position."""
        if self.cursor_position > 0:
            cursor_position = self.cursor_position
            if cursor_position >= len(self.value):
                self.value = ""
            else:
                self.value = (
                    self._template.empty_mask[:cursor_position]
                    + self.value[cursor_position:]
                )
            self.cursor_position = 0
