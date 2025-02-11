from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Iterable, NamedTuple

from rich.cells import cell_len, get_character_cell_size
from rich.console import RenderableType
from rich.highlighter import Highlighter
from rich.text import Text
from typing_extensions import Literal

from textual import events
from textual.expand_tabs import expand_tabs_inline
from textual.scroll_view import ScrollView
from textual.strip import Strip

if TYPE_CHECKING:
    pass

from textual.binding import Binding, BindingType
from textual.css._error_tools import friendly_list
from textual.events import Blur, Focus, Mount
from textual.geometry import Offset, Region, Size, clamp
from textual.message import Message
from textual.reactive import Reactive, reactive, var
from textual.suggester import Suggester, SuggestionReady
from textual.timer import Timer
from textual.validation import ValidationResult, Validator

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


class Selection(NamedTuple):
    """A range of selected text within the Input.

    Text can be selected by clicking and dragging the mouse, or by pressing
    shift+arrow keys.

    Attributes:
        start: The start index of the selection.
        end: The end index of the selection.
    """

    start: int
    end: int

    @classmethod
    def cursor(cls, cursor_position: int) -> Selection:
        """Create a selection from a cursor position."""
        return cls(cursor_position, cursor_position)

    @property
    def is_empty(self) -> bool:
        """Return True if the selection is empty."""
        return self.start == self.end


class Input(ScrollView):
    """A text input widget."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("left", "cursor_left", "Move cursor left", show=False),
        Binding(
            "shift+left",
            "cursor_left(True)",
            "Move cursor left and select",
            show=False,
        ),
        Binding("ctrl+left", "cursor_left_word", "Move cursor left a word", show=False),
        Binding(
            "ctrl+shift+left",
            "cursor_left_word(True)",
            "Move cursor left a word and select",
            show=False,
        ),
        Binding(
            "right",
            "cursor_right",
            "Move cursor right or accept the completion suggestion",
            show=False,
        ),
        Binding(
            "shift+right",
            "cursor_right(True)",
            "Move cursor right and select",
            show=False,
        ),
        Binding(
            "ctrl+right", "cursor_right_word", "Move cursor right a word", show=False
        ),
        Binding(
            "ctrl+shift+right",
            "cursor_right_word(True)",
            "Move cursor right a word and select",
            show=False,
        ),
        Binding("backspace", "delete_left", "Delete character left", show=False),
        Binding("home,ctrl+a", "home", "Go to start", show=False),
        Binding("end,ctrl+e", "end", "Go to end", show=False),
        Binding("shift+home", "home(True)", "Select line start", show=False),
        Binding("shift+end", "end(True)", "Select line end", show=False),
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
        Binding("ctrl+x", "cut", "Cut selected text", show=False),
        Binding("ctrl+c", "copy", "Copy selected text", show=False),
        Binding("ctrl+v", "paste", "Paste text from the clipboard", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | left | Move the cursor left. |
    | shift+left | Move cursor left and select. |
    | ctrl+left | Move the cursor one word to the left. |
    | right | Move the cursor right or accept the completion suggestion. |
    | ctrl+shift+left | Move cursor left a word and select. |
    | shift+right | Move cursor right and select. |
    | ctrl+right | Move the cursor one word to the right. |
    | backspace | Delete the character to the left of the cursor. |
    | ctrl+shift+right | Move cursor right a word and select. |
    | home,ctrl+a | Go to the beginning of the input. |
    | end,ctrl+e | Go to the end of the input. |
    | shift+home | Select up to the input start. |
    | shift+end | Select up to the input end. |
    | delete,ctrl+d | Delete the character to the right of the cursor. |
    | enter | Submit the current value of the input. |
    | ctrl+w | Delete the word to the left of the cursor. |
    | ctrl+u | Delete everything to the left of the cursor. |
    | ctrl+f | Delete the word to the right of the cursor. |
    | ctrl+k | Delete everything to the right of the cursor. |
    | ctrl+x | Cut selected text. |
    | ctrl+c | Copy selected text. |
    | ctrl+v | Paste text from the clipboard. | 
    """

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "input--cursor",
        "input--placeholder",
        "input--suggestion",
        "input--selection",
    }
    """
    | Class | Description |
    | :- | :- |
    | `input--cursor` | Target the cursor. |
    | `input--placeholder` | Target the placeholder text (when it exists). |
    | `input--suggestion` | Target the auto-completion suggestion (when it exists). |
    | `input--selection` | Target the selected text. |
    """

    DEFAULT_CSS = """
    Input {
        background: $surface;
        color: $foreground;
        padding: 0 2;
        border: tall $border-blurred;
        width: 100%;
        height: 3;
        scrollbar-size-horizontal: 0;

        &:focus {
            border: tall $border;
            background-tint: $foreground 5%;
        }
        &>.input--cursor {
            background: $input-cursor-background;
            color: $input-cursor-foreground;
            text-style: $input-cursor-text-style;
        }
        &>.input--selection {
            background: $input-selection-background;
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
    # TODO - check with width: auto to see if layout=True is needed
    value: Reactive[str] = reactive("", init=False)

    @property
    def cursor_position(self) -> int:
        """The current position of the cursor, corresponding to the end of the selection."""
        return self.selection.end

    @cursor_position.setter
    def cursor_position(self, position: int) -> None:
        """Set the current position of the cursor."""
        self.selection = Selection.cursor(position)

    selection: Reactive[Selection] = reactive(Selection.cursor(0))
    """The currently selected range of text."""

    placeholder = reactive("")
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

    @dataclass
    class Blurred(Message):
        """Posted when the widget is blurred (loses focus).

        Can be handled using `on_input_blurred` in a subclass of `Input` or in a parent
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
        select_on_focus: bool = True,
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
            select_on_focus: Whether to select all text on focus.
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

        self._selecting = False
        """True if the user is selecting text with the mouse."""

        self._initial_value = True
        """Indicates if the value has been set for the first time yet."""
        if value is not None:
            self.value = value

        if tooltip is not None:
            self.tooltip = tooltip

        self.select_on_focus = select_on_focus

    def _position_to_cell(self, position: int) -> int:
        """Convert an index within the value to cell position.

        Args:
            position: The index within the value to convert.

        Returns:
            The cell position corresponding to the index.
        """
        return cell_len(expand_tabs_inline(self.value[:position], 4))

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
        return self.cursor_position == len(self.value)

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

    def validate_selection(self, selection: Selection) -> Selection:
        start, end = selection
        value_length = len(self.value)
        return Selection(clamp(start, 0, value_length), clamp(end, 0, value_length))

    def _watch_selection(self, selection: Selection) -> None:
        self.app.cursor_position = self.cursor_screen_offset
        if not self._initial_value:
            self.scroll_to_region(
                Region(self._cursor_offset, 0, width=1, height=1),
                force=True,
                animate=False,
            )

    def _watch_cursor_blink(self, blink: bool) -> None:
        """Ensure we handle updating the cursor blink at runtime."""
        if self._blink_timer is not None:
            if blink:
                self._blink_timer.resume()
            else:
                self._pause_blink()
                self._cursor_visible = True

    @property
    def cursor_screen_offset(self) -> Offset:
        """The offset of the cursor of this input in screen-space. (x, y)/(column, row)"""
        x, y, _width, _height = self.content_region
        scroll_x, _ = self.scroll_offset
        return Offset(x + self._cursor_offset - scroll_x, y)

    def _watch_value(self, value: str) -> None:
        """Update the virtual size and suggestion when the value changes."""
        self.virtual_size = Size(self.content_width, 1)
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

    def render_line(self, y: int) -> Strip:
        if y != 0:
            return Strip.blank(self.size.width)

        console = self.app.console
        max_content_width = self.scrollable_content_region.width

        if not self.value:
            placeholder = Text(self.placeholder, justify="left", end="")
            placeholder.stylize(self.get_component_rich_style("input--placeholder"))
            if self.has_focus:
                cursor_style = self.get_component_rich_style("input--cursor")
                if self._cursor_visible:
                    # If the placeholder is empty, there's no characters to stylise
                    # to make the cursor flash, so use a single space character
                    if len(placeholder) == 0:
                        placeholder = Text(" ", end="")
                    placeholder.stylize(cursor_style, 0, 1)

            strip = Strip(
                console.render(
                    placeholder, console.options.update_width(max_content_width + 1)
                )
            )
        else:
            result = self._value

            # Add the completion with a faded style.
            value = self.value
            value_length = len(value)
            suggestion = self._suggestion
            show_suggestion = len(suggestion) > value_length and self.has_focus
            if show_suggestion:
                result += Text(
                    suggestion[value_length:],
                    self.get_component_rich_style("input--suggestion"),
                    end="",
                )

            if self.has_focus:
                if not self.selection.is_empty:
                    start, end = self.selection
                    start, end = sorted((start, end))
                    selection_style = self.get_component_rich_style("input--selection")
                    result.stylize_before(selection_style, start, end)

                if self._cursor_visible:
                    cursor_style = self.get_component_rich_style("input--cursor")
                    cursor = self.cursor_position
                    if not show_suggestion and self._cursor_at_end:
                        result.pad_right(1)
                    result.stylize(cursor_style, cursor, cursor + 1)

            segments = list(
                console.render(result, console.options.update_width(self.content_width))
            )

            strip = Strip(segments)
            scroll_x, _ = self.scroll_offset
            strip = strip.crop(scroll_x, scroll_x + max_content_width + 1)
            strip = strip.extend_cell_length(max_content_width + 1)

        return strip.apply_style(self.rich_style)

    @property
    def _value(self) -> Text:
        """Value rendered as text."""
        if self.password:
            return Text("•" * len(self.value), no_wrap=True, overflow="ignore", end="")
        else:
            text = Text(self.value, no_wrap=True, overflow="ignore", end="")
            if self.highlighter is not None:
                text = self.highlighter(text)
            return text

    @property
    def content_width(self) -> int:
        """The width of the content."""
        if self.placeholder and not self.value:
            return cell_len(self.placeholder)

        # Extra space for cursor at the end.
        return self._value.cell_len + 1

    def get_content_width(self, container: Size, viewport: Size) -> int:
        """Get the widget of the content."""
        return self.content_width

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
        self._pause_blink()
        validation_result = (
            self.validate(self.value) if "blur" in self.validate_on else None
        )
        self.post_message(self.Blurred(self, self.value, validation_result))

    def _on_focus(self, event: Focus) -> None:
        self._restart_blink()
        if self.select_on_focus and not event.from_app_focus:
            self.selection = Selection(0, len(self.value))
        self.app.cursor_position = self.cursor_screen_offset
        self._suggestion = ""

    async def _on_key(self, event: events.Key) -> None:
        self._restart_blink()

        if event.is_printable:
            event.stop()
            assert event.character is not None
            selection = self.selection
            if selection.is_empty:
                self.insert_text_at_cursor(event.character)
            else:
                self.replace(event.character, *selection)
            event.prevent_default()

    def _on_paste(self, event: events.Paste) -> None:
        if event.text:
            line = event.text.splitlines()[0]
            selection = self.selection
            if selection.is_empty:
                self.insert_text_at_cursor(line)
            else:
                self.replace(line, *selection)
        event.stop()

    def _cell_offset_to_index(self, offset: int) -> int:
        """Convert a cell offset to a character index, accounting for character width.

        Args:
            offset: The cell offset to convert.

        Returns:
            The character index corresponding to the cell offset.
        """
        cell_offset = 0
        _cell_size = get_character_cell_size
        scroll_x, _ = self.scroll_offset
        offset += scroll_x
        for index, char in enumerate(self.value):
            cell_width = _cell_size(char)
            if cell_offset <= offset < (cell_offset + cell_width):
                return index
            cell_offset += cell_width
        return clamp(offset, 0, len(self.value))

    async def _on_mouse_down(self, event: events.MouseDown) -> None:
        self._pause_blink(visible=True)
        offset_x, _ = event.get_content_offset_capture(self)
        self.selection = Selection.cursor(self._cell_offset_to_index(offset_x))
        self._selecting = True
        self.capture_mouse()

    async def _on_mouse_up(self, event: events.MouseUp) -> None:
        if self._selecting:
            self._selecting = False
            self.release_mouse()
            self._restart_blink()

    async def _on_mouse_move(self, event: events.MouseMove) -> None:
        if self._selecting:
            # As we drag the mouse, we update the end position of the selection,
            # keeping the start position fixed.
            offset = event.get_content_offset_capture(self)
            selection_start, _ = self.selection
            self.selection = Selection(
                selection_start, self._cell_offset_to_index(offset.x)
            )

    async def _on_suggestion_ready(self, event: SuggestionReady) -> None:
        """Handle suggestion messages and set the suggestion when relevant."""
        if event.value == self.value:
            self._suggestion = event.suggestion

    def _restart_blink(self) -> None:
        """Restart the cursor blink cycle."""
        self._cursor_visible = True
        if self.cursor_blink and self._blink_timer:
            self._blink_timer.reset()

    def _pause_blink(self, visible: bool = False) -> None:
        """Hide the blinking cursor and pause the blink cycle."""
        self._cursor_visible = visible
        if self._blink_timer:
            self._blink_timer.pause()

    def insert_text_at_cursor(self, text: str) -> None:
        """Insert new text at the cursor, move the cursor to the end of the new text.

        Args:
            text: New text to insert.
        """
        self.insert(text, self.cursor_position)

    def restricted(self) -> None:
        """Called when a character has been restricted.

        The default behavior is to play the system bell.
        You may want to override this method if you want to disable the bell or do something else entirely.
        """
        self.app.bell()

    def clear(self) -> None:
        """Clear the input."""
        self.value = ""

    @property
    def selected_text(self) -> str:
        """The text between the start and end points of the current selection."""
        start, end = sorted(self.selection)
        return self.value[start:end]

    def action_cursor_left(self, select: bool = False) -> None:
        """Move the cursor one position to the left.

        Args:
            select: If `True`, select the text to the left of the cursor.
        """
        start, end = self.selection
        if select:
            self.selection = Selection(start, end - 1)
        else:
            if self.selection.is_empty:
                self.cursor_position -= 1
            else:
                self.cursor_position = min(start, end)

    def action_cursor_right(self, select: bool = False) -> None:
        """Accept an auto-completion or move the cursor one position to the right.

        Args:
            select: If `True`, select the text to the right of the cursor.
        """
        start, end = self.selection
        if select:
            self.selection = Selection(start, end + 1)
        else:
            if self._cursor_at_end and self._suggestion:
                self.value = self._suggestion
                self.cursor_position = len(self.value)
            else:
                if self.selection.is_empty:
                    self.cursor_position += 1
                else:
                    self.cursor_position = max(start, end)

    def action_home(self, select: bool = False) -> None:
        """Move the cursor to the start of the input.

        Args:
            select: If `True`, select the text between the old and new cursor positions.
        """
        if select:
            self.selection = Selection(self.cursor_position, 0)
        else:
            self.cursor_position = 0

    def action_end(self, select: bool = False) -> None:
        """Move the cursor to the end of the input.

        Args:
            select: If `True`, select the text between the old and new cursor positions.
        """
        if select:
            self.selection = Selection(self.cursor_position, len(self.value))
        else:
            self.cursor_position = len(self.value)

    _WORD_START = re.compile(r"(?<=\W)\w")

    def action_cursor_left_word(self, select: bool = False) -> None:
        """Move the cursor left to the start of a word.

        Args:
            select: If `True`, select the text between the old and new cursor positions.
        """
        if self.password:
            # This is a password field so don't give any hints about word
            # boundaries, even during movement.
            self.action_home(select)
        else:
            start, _ = self.selection
            try:
                *_, hit = re.finditer(
                    self._WORD_START, self.value[: self.cursor_position]
                )
            except ValueError:
                target = 0
            else:
                target = hit.start()

            if select:
                self.selection = Selection(start, target)
            else:
                self.cursor_position = target

    def action_cursor_right_word(self, select: bool = False) -> None:
        """Move the cursor right to the start of a word.

        Args:
            select: If `True`, select the text between the old and new cursor positions.
        """
        if self.password:
            # This is a password field so don't give any hints about word
            # boundaries, even during movement.
            self.action_end(select)
        else:
            hit = re.search(self._WORD_START, self.value[self.cursor_position :])

            start, end = self.selection
            if hit is None:
                target = len(self.value)
            else:
                target = end + hit.start()

            if select:
                self.selection = Selection(start, target)
            else:
                self.cursor_position = target

    def replace(self, text: str, start: int, end: int) -> None:
        """Replace the text between the start and end locations with the given text.

        Args:
            text: Text to replace the existing text with.
            start: Start index to replace (inclusive).
            end: End index to replace (inclusive).
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

        value = self.value
        start, end = sorted((max(0, start), min(len(value), end)))
        new_value = f"{value[:start]}{text}{value[end:]}"
        if check_allowed_value(new_value):
            self.value = new_value
            self.cursor_position = start + len(text)
        else:
            self.restricted()

    def insert(self, text: str, index: int) -> None:
        """Insert text at the given index.

        Args:
            text: Text to insert.
            index: Index to insert the text at (inclusive).
        """
        self.replace(text, index, index)

    def delete(self, start: int, end: int) -> None:
        """Delete the text between the start and end locations.

        Args:
            start: Start index to delete (inclusive).
            end: End index to delete (inclusive).
        """
        self.replace("", start, end)

    def delete_selection(self) -> None:
        """Delete the current selection."""
        self.delete(*self.selection)

    def action_delete_right(self) -> None:
        """Delete one character at the current cursor position."""
        if self.selection.is_empty:
            self.delete(self.cursor_position, self.cursor_position + 1)
        else:
            self.delete_selection()

    def action_delete_right_word(self) -> None:
        """Delete the current character and all rightward to the start of the next word."""
        if not self.selection.is_empty:
            self.delete_selection()
            return

        if self.password:
            # This is a password field so don't give any hints about word
            # boundaries, even during deletion.
            self.action_delete_right_all()
        else:
            after = self.value[self.cursor_position :]
            hit = re.search(self._WORD_START, after)
            if hit is None:
                self.action_delete_right_all()
            else:
                start = self.cursor_position
                end = start + hit.end() - 1
                self.delete(start, end)

    def action_delete_right_all(self) -> None:
        """Delete the current character and all characters to the right of the cursor position."""
        if self.selection.is_empty:
            self.delete(self.cursor_position, len(self.value))
        else:
            self.delete_selection()

    def action_delete_left(self) -> None:
        """Delete one character to the left of the current cursor position."""
        if self.selection.is_empty:
            self.delete(self.cursor_position - 1, self.cursor_position)
        else:
            self.delete_selection()

    def action_delete_left_word(self) -> None:
        """Delete leftward of the cursor position to the start of a word."""
        if not self.selection.is_empty:
            self.delete_selection()
            return

        if self.password:
            # This is a password field so don't give any hints about word
            # boundaries, even during deletion.
            self.action_delete_left_all()
        else:
            try:
                *_, hit = re.finditer(
                    self._WORD_START, self.value[: self.cursor_position]
                )
            except ValueError:
                target = 0
            else:
                target = hit.start()

            self.delete(target, self.cursor_position)

    def action_delete_left_all(self) -> None:
        """Delete all characters to the left of the cursor position."""
        if self.selection.is_empty:
            self.delete(0, self.cursor_position)
        else:
            self.delete_selection()

    async def action_submit(self) -> None:
        """Handle a submit action.

        Normally triggered by the user pressing Enter. This may also run any validators.
        """
        validation_result = (
            self.validate(self.value) if "submitted" in self.validate_on else None
        )
        self.post_message(self.Submitted(self, self.value, validation_result))

    def action_cut(self) -> None:
        """Cut the current selection (copy to clipboard and remove from input)."""
        self.app.copy_to_clipboard(self.selected_text)
        self.delete_selection()

    def action_copy(self) -> None:
        """Copy the current selection to the clipboard."""
        self.app.copy_to_clipboard(self.selected_text)

    def action_paste(self) -> None:
        """Paste from the local clipboard."""
        clipboard = self.app.clipboard
        start, end = self.selection
        self.replace(clipboard, start, end)
