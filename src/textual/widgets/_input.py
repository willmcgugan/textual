from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Iterable

from rich.cells import cell_len, get_character_cell_size
from rich.console import Console, ConsoleOptions, RenderableType
from rich.console import RenderResult as RichRenderResult
from rich.highlighter import Highlighter
from rich.segment import Segment
from rich.text import Text
from typing_extensions import Literal

from textual import events
from textual._segment_tools import line_crop

if TYPE_CHECKING:
    from textual.app import RenderResult

from textual.binding import Binding, BindingType
from textual.css._error_tools import friendly_list
from textual.events import Blur, Focus, Mount
from textual.geometry import Offset, Size
from textual.message import Message
from textual.reactive import Reactive, reactive, var
from textual.suggester import Suggester, SuggestionReady
from textual.timer import Timer
from textual.validation import ValidationResult, Validator
from textual.widget import Widget

InputValidationOn = Literal["blur", "changed", "submitted"]
"""Possible messages that trigger input validation."""
_POSSIBLE_VALIDATE_ON_VALUES = {"blur", "changed", "submitted"}
"""Set literal with the legal values for the type `InputValidationOn`."""

_RESTRICT_TYPES = {
    "integer": r"[-+]?(?:\d*|\d+_)*",
    "number": r"[-+]?(?:\d*|\d+_)*\.?(?:\d*|\d+_)*(?:\d[eE]?[-+]?(?:\d*|\d+_)*)?",
    "text": None,
}
InputType = Literal["integer", "number", "text"]


class _InputRenderable:
    """Render the input content."""

    def __init__(self, input: Input, cursor_visible: bool) -> None:
        self.input = input
        self.cursor_visible = cursor_visible

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> RichRenderResult:
        input = self.input
        result = input._value
        width = input.content_size.width

        # Add the completion with a faded style.
        value = input.value
        value_length = len(value)
        suggestion = input._suggestion
        show_suggestion = len(suggestion) > value_length and input.has_focus
        if show_suggestion:
            result += Text(
                suggestion[value_length:],
                input.get_component_rich_style("input--suggestion"),
            )

        if self.cursor_visible and input.has_focus:
            if not show_suggestion and input._cursor_at_end:
                result.pad_right(1)
            cursor_style = input.get_component_rich_style("input--cursor")
            cursor = input.cursor_position
            result.stylize(cursor_style, cursor, cursor + 1)

        segments = list(result.render(console))
        line_length = Segment.get_line_length(segments)
        if line_length < width:
            segments = Segment.adjust_line_length(segments, width)
            line_length = width

        line = line_crop(
            list(segments),
            input.view_position,
            input.view_position + width,
            line_length,
        )
        yield from line


class Input(Widget, can_focus=True):
    """A text input widget."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("left", "cursor_left", "Move cursor left", show=False),
        Binding("ctrl+left", "cursor_left_word", "Move cursor left a word", show=False),
        Binding("right", "cursor_right", "Move cursor right", show=False),
        Binding(
            "ctrl+right", "cursor_right_word", "Move cursor right a word", show=False
        ),
        Binding("backspace", "delete_left", "Delete character left", show=False),
        Binding("home,ctrl+a", "home", "Go to start", show=False),
        Binding("end,ctrl+e", "end", "Go to end", show=False),
        Binding("delete,ctrl+d", "delete_right", "Delete character right", show=False),
        Binding("enter", "submit", "Submit", show=False),
        Binding(
            "ctrl+w", "delete_left_word", "Delete left to start of word", show=False
        ),
        Binding("ctrl+u", "delete_left_all", "Delete all to the left", show=False),
        Binding(
            "ctrl+f", "delete_right_word", "Delete right to start of word", show=False
        ),
        Binding("ctrl+k", "delete_right_all", "Delete all to the right", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | left | Move the cursor left. |
    | ctrl+left | Move the cursor one word to the left. |
    | right | Move the cursor right or accept the completion suggestion. |
    | ctrl+right | Move the cursor one word to the right. |
    | backspace | Delete the character to the left of the cursor. |
    | home,ctrl+a | Go to the beginning of the input. |
    | end,ctrl+e | Go to the end of the input. |
    | delete,ctrl+d | Delete the character to the right of the cursor. |
    | enter | Submit the current value of the input. |
    | ctrl+w | Delete the word to the left of the cursor. |
    | ctrl+u | Delete everything to the left of the cursor. |
    | ctrl+f | Delete the word to the right of the cursor. |
    | ctrl+k | Delete everything to the right of the cursor. |
    """

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "input--cursor",
        "input--placeholder",
        "input--suggestion",
    }
    """
    | Class | Description |
    | :- | :- |
    | `input--cursor` | Target the cursor. |
    | `input--placeholder` | Target the placeholder text (when it exists). |
    | `input--suggestion` | Target the auto-completion suggestion (when it exists). |
    """

    DEFAULT_CSS = """
    Input {
        background: $surface;
        color: $foreground;
        padding: 0 2;
        border: tall $border-blurred;
        width: 100%;
        height: 3;

        &:focus {
            border: tall $border;
            background-tint: $foreground 5%;
        }
        &>.input--cursor {
            background: $input-cursor-background;
            color: $input-cursor-foreground;
            text-style: $input-cursor-text-style;
        }
        &>.input--placeholder, &>.input--suggestion {
            color: $text-disabled;
        }
        &.-invalid {
            border: tall $error 60%;
        }
        &.-invalid:focus {
            border: tall $error;
        }    

        &:ansi {
            background: ansi_default;
            color: ansi_default;
            &>.input--cursor {     
                text-style: reverse;
            }
            &>.input--placeholder, &>.input--suggestion {
                text-style: dim;
                color: ansi_default;
            }
            &.-invalid {
                border: tall ansi_red;
            }
            &.-invalid:focus {
                border: tall ansi_red;
            }  
            
        }
    }

    """

    cursor_blink = reactive(True, init=False)
    value = reactive("", layout=True, init=False)
    input_scroll_offset = reactive(0)
    cursor_position: Reactive[int] = reactive(0)
    view_position = reactive(0)
    placeholder = reactive("", init=False)
    complete = reactive("")
    width = reactive(1)
    _cursor_visible = reactive(True)
    password = reactive(False)
    suggester: Suggester | None
    """The suggester used to provide completions as the user types."""
    _suggestion = reactive("")
    """A completion suggestion for the current value in the input."""
    restrict = var["str | None"](None)
    """A regular expression to limit changes in value."""
    type = var[InputType]("text")
    """The type of the input."""
    max_length = var["int | None"](None)
    """The maximum length of the input, in characters."""
    valid_empty = var(False)
    """Empty values should pass validation."""

    @dataclass
    class Changed(Message):
        """Posted when the value changes.

        Can be handled using `on_input_changed` in a subclass of `Input` or in a parent
        widget in the DOM.
        """

        input: Input
        """The `Input` widget that was changed."""

        value: str
        """The value that the input was changed to."""

        validation_result: ValidationResult | None = None
        """The result of validating the value (formed by combining the results from each validator), or None
            if validation was not performed (for example when no validators are specified in the `Input`s init)"""

        @property
        def control(self) -> Input:
            """Alias for self.input."""
            return self.input

    @dataclass
    class Submitted(Message):
        """Posted when the enter key is pressed within an `Input`.

        Can be handled using `on_input_submitted` in a subclass of `Input` or in a
        parent widget in the DOM.
        """

        input: Input
        """The `Input` widget that is being submitted."""
        value: str
        """The value of the `Input` being submitted."""
        validation_result: ValidationResult | None = None
        """The result of validating the value on submission, formed by combining the results for each validator.
        This value will be None if no validation was performed, which will be the case if no validators are supplied
        to the corresponding `Input` widget."""

        @property
        def control(self) -> Input:
            """Alias for self.input."""
            return self.input

    def __init__(
        self,
        value: str | None = None,
        placeholder: str = "",
        highlighter: Highlighter | None = None,
        password: bool = False,
        *,
        restrict: str | None = None,
        type: InputType = "text",
        max_length: int = 0,
        suggester: Suggester | None = None,
        validators: Validator | Iterable[Validator] | None = None,
        validate_on: Iterable[InputValidationOn] | None = None,
        valid_empty: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        tooltip: RenderableType | None = None,
    ) -> None:
        """Initialise the `Input` widget.

        Args:
            value: An optional default value for the input.
            placeholder: Optional placeholder text for the input.
            highlighter: An optional highlighter for the input.
            password: Flag to say if the field should obfuscate its content.
            restrict: A regex to restrict character inputs.
            type: The type of the input.
            max_length: The maximum length of the input, or 0 for no maximum length.
            suggester: [`Suggester`][textual.suggester.Suggester] associated with this
                input instance.
            validators: An iterable of validators that the Input value will be checked against.
            validate_on: Zero or more of the values "blur", "changed", and "submitted",
                which determine when to do input validation. The default is to do
                validation for all messages.
            valid_empty: Empty values are valid.
            name: Optional name for the input widget.
            id: Optional ID for the widget.
            classes: Optional initial classes for the widget.
            disabled: Whether the input is disabled or not.
            tooltip: Optional tooltip.
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

        self._blink_timer: Timer | None = None
        """Timer controlling the blinking of the cursor, instantiated in `on_mount`."""

        self.placeholder = placeholder
        self.highlighter = highlighter
        self.password = password
        self.suggester = suggester

        # Ensure we always end up with an Iterable of validators
        if isinstance(validators, Validator):
            self.validators: list[Validator] = [validators]
        elif validators is None:
            self.validators = []
        else:
            self.validators = list(validators)

        self.validate_on: set[str] = (
            (_POSSIBLE_VALIDATE_ON_VALUES & set(validate_on))
            if validate_on is not None
            else _POSSIBLE_VALIDATE_ON_VALUES
        )
        """Set with event names to do input validation on.

        Validation can only be performed on blur, on input changes and on input submission.

        Example:
            This creates an `Input` widget that only gets validated when the value
            is submitted explicitly:

            ```py
            input = Input(validate_on=["submitted"])
            ```
        """
        self._reactive_valid_empty = valid_empty
        self._valid = True

        self.restrict = restrict
        if type not in _RESTRICT_TYPES:
            raise ValueError(
                f"Input type must be one of {friendly_list(_RESTRICT_TYPES.keys())}; not {type!r}"
            )
        self.type = type
        self.max_length = max_length
        if not self.validators:
            from textual.validation import Integer, Number

            if self.type == "integer":
                self.validators.append(Integer())
            elif self.type == "number":
                self.validators.append(Number())

        self._initial_value = True
        """Indicates if the value has been set for the first time yet."""
        if value is not None:
            self.value = value

        if tooltip is not None:
            self.tooltip = tooltip

    def _position_to_cell(self, position: int) -> int:
        """Convert an index within the value to cell position."""
        cell_offset = cell_len(self.value[:position])
        return cell_offset

    @property
    def _cursor_offset(self) -> int:
        """The cell offset of the cursor."""
        offset = self._position_to_cell(self.cursor_position)
        if self._cursor_at_end:
            offset += 1
        return offset

    @property
    def _cursor_at_end(self) -> bool:
        """Flag to indicate if the cursor is at the end"""
        return self.cursor_position >= len(self.value)

    def check_consume_key(self, key: str, character: str | None) -> bool:
        """Check if the widget may consume the given key.

        As an input we are expecting to capture printable keys.

        Args:
            key: A key identifier.
            character: A character associated with the key, or `None` if there isn't one.

        Returns:
            `True` if the widget may capture the key in it's `Key` message, or `False` if it won't.
        """
        return character is not None and character.isprintable()

    def validate_cursor_position(self, cursor_position: int) -> int:
        return min(max(0, cursor_position), len(self.value))

    def validate_view_position(self, view_position: int) -> int:
        width = self.content_size.width
        new_view_position = max(0, min(view_position, self.cursor_width - width))
        return new_view_position

    def _watch_cursor_position(self) -> None:
        width = self.content_size.width
        if width == 0:
            # If the input has no width the view position can't be elsewhere.
            self.view_position = 0
            return

        view_start = self.view_position
        view_end = view_start + width
        cursor_offset = self._cursor_offset

        if cursor_offset >= view_end or cursor_offset < view_start:
            view_position = cursor_offset - width // 2
            self.view_position = view_position
        else:
            self.view_position = self.view_position

        self.app.cursor_position = self.cursor_screen_offset

    def _watch_cursor_blink(self, blink: bool) -> None:
        """Ensure we handle updating the cursor blink at runtime."""
        if self._blink_timer is not None:
            if blink:
                self._blink_timer.resume()
            else:
                self._pause_blink_cycle()
                self._cursor_visible = True

    def _watch_placeholder(self) -> None:
        self.refresh()

    @property
    def cursor_screen_offset(self) -> Offset:
        """The offset of the cursor of this input in screen-space. (x, y)/(column, row)"""
        x, y, _width, _height = self.content_region
        return Offset(x + self._cursor_offset - self.view_position, y)

    def _watch_value(self, value: str) -> None:
        self._suggestion = ""
        if self.suggester and value:
            self.run_worker(self.suggester._get_suggestion(self, value))
        if self.styles.auto_dimensions:
            self.refresh(layout=True)

        validation_result = (
            self.validate(value) if "changed" in self.validate_on else None
        )
        self.post_message(self.Changed(self, value, validation_result))

        # If this is the first time the value has been updated, set the cursor position to the end
        if self._initial_value:
            self.cursor_position = len(self.value)
            self._initial_value = False

    def _watch_valid_empty(self) -> None:
        """Repeat validation when valid_empty changes."""
        self._watch_value(self.value)

    def validate(self, value: str) -> ValidationResult | None:
        """Run all the validators associated with this Input on the supplied value.

        Runs all validators, combines the result into one. If any of the validators
        failed, the combined result will be a failure. If no validators are present,
        None will be returned. This also sets the `-invalid` CSS class on the Input
        if the validation fails, and sets the `-valid` CSS class on the Input if
        the validation succeeds.

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

        # If no validators are supplied, and therefore no validation occurs, we return None.
        if not self.validators:
            self._valid = True
            set_classes()
            return None

        if self.valid_empty and not value:
            self._valid = True
            set_classes()
            return None

        validation_results: list[ValidationResult] = [
            validator.validate(value) for validator in self.validators
        ]
        combined_result = ValidationResult.merge(validation_results)
        self._valid = combined_result.is_valid
        set_classes()

        return combined_result

    @property
    def is_valid(self) -> bool:
        """Check if the value has passed validation."""
        return self._valid

    @property
    def cursor_width(self) -> int:
        """The width of the input (with extra space for cursor at the end)."""
        if self.placeholder and not self.value:
            return cell_len(self.placeholder)
        return self._position_to_cell(len(self.value)) + 1

    def render(self) -> RenderResult:
        self.view_position = self.view_position
        if not self.value:
            placeholder = Text(self.placeholder, justify="left")
            placeholder.stylize(self.get_component_rich_style("input--placeholder"))
            if self.has_focus:
                cursor_style = self.get_component_rich_style("input--cursor")
                if self._cursor_visible:
                    # If the placeholder is empty, there's no characters to stylise
                    # to make the cursor flash, so use a single space character
                    if len(placeholder) == 0:
                        placeholder = Text(" ")
                    placeholder.stylize(cursor_style, 0, 1)
            return placeholder
        return _InputRenderable(self, self._cursor_visible)

    @property
    def _value(self) -> Text:
        """Value rendered as text."""
        if self.password:
            return Text("•" * len(self.value), no_wrap=True, overflow="ignore")
        else:
            text = Text(self.value, no_wrap=True, overflow="ignore")
            if self.highlighter is not None:
                text = self.highlighter(text)
            return text

    def get_content_width(self, container: Size, viewport: Size) -> int:
        return self.cursor_width

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        return 1

    def _toggle_cursor(self) -> None:
        """Toggle visibility of cursor."""
        self._cursor_visible = not self._cursor_visible

    def _on_mount(self, event: Mount) -> None:
        self._blink_timer = self.set_interval(
            0.5,
            self._toggle_cursor,
            pause=not (self.cursor_blink and self.has_focus),
        )

    def _on_blur(self, event: Blur) -> None:
        self._pause_blink_cycle()
        if "blur" in self.validate_on:
            self.validate(self.value)

    def _on_focus(self, event: Focus) -> None:
        self._restart_blink_cycle()
        self.app.cursor_position = self.cursor_screen_offset
        self._suggestion = ""

    async def _on_key(self, event: events.Key) -> None:
        self._restart_blink_cycle()

        if event.is_printable:
            event.stop()
            assert event.character is not None
            self.insert_text_at_cursor(event.character)
            event.prevent_default()

    def _on_paste(self, event: events.Paste) -> None:
        if event.text:
            line = event.text.splitlines()[0]
            self.insert_text_at_cursor(line)
        event.stop()

    async def _on_click(self, event: events.Click) -> None:
        offset = event.get_content_offset(self)
        if offset is None:
            return
        event.stop()
        click_x = offset.x + self.view_position
        cell_offset = 0
        _cell_size = get_character_cell_size
        for index, char in enumerate(self.value):
            cell_width = _cell_size(char)
            if cell_offset <= click_x < (cell_offset + cell_width):
                self.cursor_position = index
                break
            cell_offset += cell_width
        else:
            self.cursor_position = len(self.value)

    async def _on_mouse_down(self, event: events.MouseDown) -> None:
        self._pause_blink_cycle()

    async def _on_mouse_up(self, event: events.MouseUp) -> None:
        self._restart_blink_cycle()

    async def _on_suggestion_ready(self, event: SuggestionReady) -> None:
        """Handle suggestion messages and set the suggestion when relevant."""
        if event.value == self.value:
            self._suggestion = event.suggestion

    def _restart_blink_cycle(self) -> None:
        """Restart the cursor blink cycle."""
        self._cursor_visible = True
        if self.cursor_blink and self._blink_timer:
            self._blink_timer.reset()

    def _pause_blink_cycle(self) -> None:
        """Hide the blinking cursor and pause the blink cycle."""
        self._cursor_visible = False
        if self._blink_timer:
            self._blink_timer.pause()

    def insert_text_at_cursor(self, text: str) -> None:
        """Insert new text at the cursor, move the cursor to the end of the new text.

        Args:
            text: New text to insert.
        """

        def check_allowed_value(value: str) -> bool:
            """Check if new value is restricted."""
            # Check max length
            if self.max_length and len(value) > self.max_length:
                return False
            # Check explicit restrict
            if self.restrict and re.fullmatch(self.restrict, value) is None:
                return False
            # Check type restrict
            if self.type:
                type_restrict = _RESTRICT_TYPES.get(self.type, None)
                if (
                    type_restrict is not None
                    and re.fullmatch(type_restrict, value) is None
                ):
                    return False
            # Character is allowed
            return True

        if self.cursor_position >= len(self.value):
            new_value = self.value + text
            if check_allowed_value(new_value):
                self.value = new_value
                self.cursor_position = len(self.value)
            else:
                self.restricted()
        else:
            value = self.value
            before = value[: self.cursor_position]
            after = value[self.cursor_position :]
            new_value = f"{before}{text}{after}"
            if check_allowed_value(new_value):
                self.value = new_value
                self.cursor_position += len(text)
            else:
                self.restricted()

    def restricted(self) -> None:
        """Called when a character has been restricted.

        The default behavior is to play the system bell.
        You may want to override this method if you want to disable the bell or do something else entirely.
        """
        self.app.bell()

    def clear(self) -> None:
        """Clear the input."""
        self.value = ""

    def action_cursor_left(self) -> None:
        """Move the cursor one position to the left."""
        self.cursor_position -= 1

    def action_cursor_right(self) -> None:
        """Accept an auto-completion or move the cursor one position to the right."""
        if self._cursor_at_end and self._suggestion:
            self.value = self._suggestion
            self.cursor_position = len(self.value)
        else:
            self.cursor_position += 1

    def action_home(self) -> None:
        """Move the cursor to the start of the input."""
        self.cursor_position = 0

    def action_end(self) -> None:
        """Move the cursor to the end of the input."""
        self.cursor_position = len(self.value)

    _WORD_START = re.compile(r"(?<=\W)\w")

    def action_cursor_left_word(self) -> None:
        """Move the cursor left to the start of a word."""
        if self.password:
            # This is a password field so don't give any hints about word
            # boundaries, even during movement.
            self.action_home()
        else:
            try:
                *_, hit = re.finditer(
                    self._WORD_START, self.value[: self.cursor_position]
                )
            except ValueError:
                self.cursor_position = 0
            else:
                self.cursor_position = hit.start()

    def action_cursor_right_word(self) -> None:
        """Move the cursor right to the start of a word."""
        if self.password:
            # This is a password field so don't give any hints about word
            # boundaries, even during movement.
            self.action_end()
        else:
            hit = re.search(self._WORD_START, self.value[self.cursor_position :])
            if hit is None:
                self.cursor_position = len(self.value)
            else:
                self.cursor_position += hit.start()

    def action_delete_right(self) -> None:
        """Delete one character at the current cursor position."""
        value = self.value
        delete_position = self.cursor_position
        before = value[:delete_position]
        after = value[delete_position + 1 :]
        self.value = f"{before}{after}"
        self.cursor_position = delete_position

    def action_delete_right_word(self) -> None:
        """Delete the current character and all rightward to the start of the next word."""
        if self.password:
            # This is a password field so don't give any hints about word
            # boundaries, even during deletion.
            self.action_delete_right_all()
        else:
            after = self.value[self.cursor_position :]
            hit = re.search(self._WORD_START, after)
            if hit is None:
                self.value = self.value[: self.cursor_position]
            else:
                self.value = (
                    f"{self.value[: self.cursor_position]}{after[hit.end() - 1:]}"
                )

    def action_delete_right_all(self) -> None:
        """Delete the current character and all characters to the right of the cursor position."""
        self.value = self.value[: self.cursor_position]

    def action_delete_left(self) -> None:
        """Delete one character to the left of the current cursor position."""
        if self.cursor_position <= 0:
            # Cursor at the start, so nothing to delete
            return
        if self.cursor_position == len(self.value):
            # Delete from end
            self.value = self.value[:-1]
            self.cursor_position = len(self.value)
        else:
            # Cursor in the middle
            value = self.value
            delete_position = self.cursor_position - 1
            before = value[:delete_position]
            after = value[delete_position + 1 :]
            self.value = f"{before}{after}"
            self.cursor_position = delete_position

    def action_delete_left_word(self) -> None:
        """Delete leftward of the cursor position to the start of a word."""
        if self.cursor_position <= 0:
            return
        if self.password:
            # This is a password field so don't give any hints about word
            # boundaries, even during deletion.
            self.action_delete_left_all()
        else:
            after = self.value[self.cursor_position :]
            try:
                *_, hit = re.finditer(
                    self._WORD_START, self.value[: self.cursor_position]
                )
            except ValueError:
                self.cursor_position = 0
            else:
                self.cursor_position = hit.start()
            new_value = f"{self.value[: self.cursor_position]}{after}"
            self.value = new_value

    def action_delete_left_all(self) -> None:
        """Delete all characters to the left of the cursor position."""
        if self.cursor_position > 0:
            self.value = self.value[self.cursor_position :]
            self.cursor_position = 0

    async def action_submit(self) -> None:
        """Handle a submit action.

        Normally triggered by the user pressing Enter. This may also run any validators.
        """
        validation_result = (
            self.validate(self.value) if "submitted" in self.validate_on else None
        )
        self.post_message(self.Submitted(self, self.value, validation_result))
