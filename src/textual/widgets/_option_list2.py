from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Iterable, Sequence

import rich.repr
from rich.segment import Segment

from textual import _widget_navigation, events
from textual._loop import loop_last
from textual.binding import Binding, BindingType
from textual.cache import LRUCache
from textual.css.styles import RulesMap
from textual.geometry import Region, Size
from textual.message import Message
from textual.reactive import reactive
from textual.scroll_view import ScrollView
from textual.strip import Strip
from textual.style import Style
from textual.visual import Visual, VisualType, visualize

if TYPE_CHECKING:
    from typing_extensions import Self


class OptionListError(Exception):
    """An error occurred in the option list."""


class DuplicateID(OptionListError):
    """Raised if a duplicate ID is used when adding options to an option list."""


class OptionDoesNotExist(OptionListError):
    """Raised when a request has been made for an option that doesn't exist."""


@rich.repr.auto
class Option:
    """This class holds details of options in the list."""

    def __init__(
        self, prompt: VisualType, id: str | None = None, disabled: bool = False
    ) -> None:
        """Initialise the option.

        Args:
            prompt: The prompt (text displayed) for the option.
            id: An option ID for the option.
            disabled: Disable the option (will be shown grayed out, and will not be selectable).

        """
        self._prompt = prompt
        self._visual: Visual | None = None
        self._id = id
        self._disabled = disabled
        self._divider = False

    @property
    def prompt(self) -> VisualType:
        """The original prompt."""
        return self._prompt

    @property
    def id(self) -> str | None:
        """Optional ID for the option."""
        return self._id

    @property
    def disabled(self) -> bool:
        return self._disabled

    def __rich_repr__(self) -> rich.repr.Result:
        yield self._prompt
        yield "id", self._id, None
        yield "disabled", self.disabled, False
        yield "_divider", self._divider, False


@dataclass
class _LineCache:
    """Cached line information."""

    lines: list[tuple[int, int]] = field(default_factory=list)
    heights: dict[int, int] = field(default_factory=dict)
    index_to_line: dict[int, int] = field(default_factory=dict)

    def clear(self) -> None:
        self.lines.clear()
        self.heights.clear()
        self.index_to_line.clear()


class OptionList(ScrollView, can_focus=True):
    ALLOW_SELECT = False
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("down", "cursor_down", "Down", show=False),
        Binding("end", "last", "Last", show=False),
        Binding("enter", "select", "Select", show=False),
        Binding("home", "first", "First", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("up", "cursor_up", "Up", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | down | Move the highlight down. |
    | end | Move the highlight to the last option. |
    | enter | Select the current option. |
    | home | Move the highlight to the first option. |
    | pagedown | Move the highlight down a page of options. |
    | pageup | Move the highlight up a page of options. |
    | up | Move the highlight up. |
    """

    DEFAULT_CSS = """
    OptionList {
        height: auto;
        max-height: 100%;
        color: $foreground;
        overflow-x: hidden;
        border: tall $border-blurred;
        padding: 0 1;
        background: $surface;
        & > .option-list--option-highlighted {
            color: $block-cursor-blurred-foreground;
            background: $block-cursor-blurred-background;
            text-style: $block-cursor-blurred-text-style;
        }
        &:focus {
            border: tall $border;
            background-tint: $foreground 5%;
            & > .option-list--option-highlighted {
                color: $block-cursor-foreground;
                background: $block-cursor-background;
                text-style: $block-cursor-text-style;
            }
        }
        & > .option-list--separator {
            color: $foreground 15%;
        }
        & > .option-list--option-highlighted {
            color: $foreground;
            background: $block-cursor-blurred-background;
        }
        & > .option-list--option-disabled {
            color: $text-disabled;
        }
        & > .option-list--option-hover {
            background: $block-hover-background;
        }
    }
    """

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "option-list--option",
        "option-list--option-disabled",
        "option-list--option-highlighted",
        "option-list--option-hover",
        "option-list--separator",
    }
    """
    | Class | Description |
    | :- | :- |
    | `option-list--option` | Target options that are not disabled, highlighted or have the mouse over them. |
    | `option-list--option-disabled` | Target disabled options. |
    | `option-list--option-highlighted` | Target the highlighted option. |
    | `option-list--option-hover` | Target an option that has the mouse over it. |
    | `option-list--separator` | Target the separators. |
    """

    highlighted: reactive[int | None] = reactive(None)
    """The index of the currently-highlighted option, or `None` if no option is highlighted."""

    hover_option_index: reactive[int | None] = reactive(None)
    """The index of the option under the mouse or `None`."""

    class OptionMessage(Message):
        """Base class for all option messages."""

        def __init__(self, option_list: OptionList, option: Option, index: int) -> None:
            """Initialise the option message.

            Args:
                option_list: The option list that owns the option.
                index: The index of the option that the message relates to.
            """
            super().__init__()
            self.option_list: OptionList = option_list
            """The option list that sent the message."""
            self.option: Option = option
            """The highlighted option."""
            self.option_id: str | None = option.id
            """The ID of the option that the message relates to."""
            self.option_index: int = index
            """The index of the option that the message relates to."""

        @property
        def control(self) -> OptionList:
            """The option list that sent the message.

            This is an alias for [`OptionMessage.option_list`][textual.widgets.OptionList.OptionMessage.option_list]
            and is used by the [`on`][textual.on] decorator.
            """
            return self.option_list

        def __rich_repr__(self) -> rich.repr.Result:
            try:
                yield "option_list", self.option_list
                yield "option", self.option
                yield "option_id", self.option_id
                yield "option_index", self.option_index
            except AttributeError:
                return

    class OptionHighlighted(OptionMessage):
        """Message sent when an option is highlighted.

        Can be handled using `on_option_list_option_highlighted` in a subclass of
        `OptionList` or in a parent node in the DOM.
        """

    class OptionSelected(OptionMessage):
        """Message sent when an option is selected.

        Can be handled using `on_option_list_option_selected` in a subclass of
        `OptionList` or in a parent node in the DOM.
        """

    def __init__(
        self,
        *content: Option | VisualType | None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        wrap: bool = True,
        markup: bool = True,
        tooltip: VisualType | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._option_id = 0
        self._wrap = wrap
        self._markup = markup
        self._options: list[Option] = []
        self._id_to_option: dict[str, Option] = {}
        self._option_to_index: dict[Option, int] = {}

        self._visuals: dict[int, Visual] = {}
        self._option_render_cache: LRUCache[tuple[Option, Style], list[Strip]]
        self._option_render_cache = LRUCache(maxsize=1024)

        self._line_cache = _LineCache()

        if tooltip is not None:
            self.tooltip = tooltip

        self.add_options(content)

    @property
    def options(self) -> Sequence[Option]:
        """Sequence of options in the OptionList.

        !!! note "This is read-only"

        """
        return self._options

    @property
    def option_count(self) -> int:
        """The number of options."""
        return len(self._options)

    def clear_options(self) -> Self:
        """Clear the content of the option list.

        Returns:
            The `OptionList` instance.
        """
        self._line_cache.clear()
        self._option_render_cache.clear()
        self.highlighted = None
        self.refresh()
        return self

    def add_options(self, new_options: Iterable[Option | VisualType | None]) -> Self:
        """Add new options.

        Args:
            new_options: Content of new options.
        """

        options = self._options
        add_option = self._options.append
        for prompt in new_options:
            if isinstance(prompt, Option):
                option = prompt
            elif prompt is None:
                if options:
                    options[-1]._divider = True
                continue
            else:
                option = Option(prompt)
            self._option_to_index[option] = len(options)
            add_option(option)
            if option._id is not None:
                if option._id in self._id_to_option:
                    raise DuplicateID("Unable to add {option!r} due to duplicate ID")
                self._id_to_option[option._id] = option

        return self

    def add_option(self, option: Option | VisualType | None) -> Self:
        """Add a new option to the end of the option list.

        Args:
            option: New option to add, or `None` for a separator.

        Returns:
            The `OptionList` instance.

        Raises:
            DuplicateID: If there is an attempt to use a duplicate ID.
        """
        self.add_options([option])
        return self

    def get_option(self, option_id: str) -> Option:
        """Get the option with the given ID.

        Args:
            option_id: The ID of the option to get.

        Returns:
            The option with the ID.

        Raises:
            OptionDoesNotExist: If no option has the given ID.
        """
        try:
            return self._id_to_option[option_id]
        except KeyError:
            raise OptionDoesNotExist(
                f"There is no option with an ID of {option_id!r}"
            ) from None

    def get_option_index(self, option_id: str) -> int:
        """Get the index (offset in `self.options`) of the option with the given ID.

        Args:
            option_id: The ID of the option to get the index of.

        Returns:
            The index of the item with the given ID.

        Raises:
            OptionDoesNotExist: If no option has the given ID.
        """
        option = self.get_option(option_id)
        return self._option_to_index[option]

    def get_option_at_index(self, index: int) -> Option:
        """Get the option at the given index.

        Args:
            index: The index of the option to get.

        Returns:
            The option at that index.

        Raises:
            OptionDoesNotExist: If there is no option with the given index.
        """
        try:
            return self._options[index]
        except IndexError:
            raise OptionDoesNotExist(
                f"There is no option with an index of {index}"
            ) from None

    def _set_option_disabled(self, index: int, disabled: bool) -> Self:
        """Set the disabled state of an option in the list.

        Args:
            index: The index of the option to set the disabled state of.
            disabled: The disabled state to set.

        Returns:
            The `OptionList` instance.
        """
        self._options[index]._disabled = disabled
        if index == self.highlighted:
            self.highlighted = _widget_navigation.find_next_enabled(
                self._options, anchor=index, direction=1
            )
        # TODO: Refresh only if the affected option is visible.
        self.refresh()
        return self

    def enable_option_at_index(self, index: int) -> Self:
        """Enable the option at the given index.

        Returns:
            The `OptionList` instance.

        Raises:
            OptionDoesNotExist: If there is no option with the given index.
        """
        try:
            return self._set_option_disabled(index, False)
        except IndexError:
            raise OptionDoesNotExist(
                f"There is no option with an index of {index}"
            ) from None

    def disable_option_at_index(self, index: int) -> Self:
        """Disable the option at the given index.

        Returns:
            The `OptionList` instance.

        Raises:
            OptionDoesNotExist: If there is no option with the given index.
        """
        try:
            return self._set_option_disabled(index, True)
        except IndexError:
            raise OptionDoesNotExist(
                f"There is no option with an index of {index}"
            ) from None

    def enable_option(self, option_id: str) -> Self:
        """Enable the option with the given ID.

        Args:
            option_id: The ID of the option to enable.

        Returns:
            The `OptionList` instance.

        Raises:
            OptionDoesNotExist: If no option has the given ID.
        """
        return self.enable_option_at_index(self.get_option_index(option_id))

    def disable_option(self, option_id: str) -> Self:
        """Disable the option with the given ID.

        Args:
            option_id: The ID of the option to disable.

        Returns:
            The `OptionList` instance.

        Raises:
            OptionDoesNotExist: If no option has the given ID.
        """
        return self.disable_option_at_index(self.get_option_index(option_id))

    def remove_option(self, option_id: str) -> Self:
        """Remove the option with the given ID.

        Args:
            option_id: The ID of the option to remove.

        Returns:
            The `OptionList` instance.

        Raises:
            OptionDoesNotExist: If no option has the given ID.
        """

        index = self.get_option_index(option_id)

        for option in self.options[index + 1 :]:
            current_index = self._option_to_index[option]
            self._option_to_index[option] = current_index - 1

        option = self._options[index]
        del self._options[index]
        del self._id_to_option[option_id]
        del self._option_to_index[option]
        self.refresh()

        return self

    @property
    def _lines(self) -> Sequence[tuple[int, int]]:
        """A sequence of pairs of ints for each line, used internally.

        The first int is the index of the option, and second is the line offset.

        !!! note "This is read-only"

        Returns:
            A sequence of tuples.
        """
        self._update_lines()
        return self._line_cache.lines

    @property
    def _heights(self) -> dict[int, int]:
        self._update_lines()
        return self._line_cache.heights

    @property
    def _index_to_line(self) -> dict[int, int]:
        self._update_lines()
        return self._line_cache.index_to_line

    def _clear_caches(self) -> None:
        self._option_render_cache.clear()
        self._line_cache.clear()

    def notify_style_update(self) -> None:
        self._clear_caches()

    def _on_resize(self):
        self._clear_caches()
        self.refresh()

    def on_show(self) -> None:
        self.scroll_to_highlight()

    async def _on_click(self, event: events.Click) -> None:
        """React to the mouse being clicked on an item.

        Args:
            event: The click event.
        """
        clicked_option: int | None = event.style.meta.get("option")
        if (
            clicked_option is not None
            and clicked_option >= 0
            and not self._options[clicked_option].disabled
        ):
            self.highlighted = clicked_option
            self.action_select()

    def _left_gutter_width(self) -> int:
        """Returns the size of any left gutter that should be taken into account.

        Returns:
            The width of the left gutter.
        """
        return 0

    def _on_mouse_move(self, event: events.MouseMove) -> None:
        """React to the mouse moving.

        Args:
            event: The mouse movement event.
        """
        self.hover_option_index = event.style.meta.get("option")

    def _on_leave(self, _: events.Leave) -> None:
        """React to the mouse leaving the widget."""
        self._mouse_hovering_over = None

    def _get_visual(self, option: Option) -> Visual:
        if (visual := option._visual) is None:
            visual = visualize(self, option.prompt, markup=self._markup)
            option._visual = visual
        return visual

    def _get_visual_from_index(self, index: int) -> Visual:
        option = self.get_option_at_index(index)
        if (visual := option._visual) is None:
            visual = visualize(self, option.prompt, markup=self._markup)
            option._visual = visual
        return visual

    def _get_option_render(self, option: Option, style: Style) -> list[Strip]:
        """Get rendered option with a given style.

        Args:
            style: Style of render.
            index: Index of the option.

        Returns:
            A list of strips.
        """
        width = self.content_region.width
        cache_key = (option, style)
        if (strips := self._option_render_cache.get(cache_key)) is None:
            visual = self._get_visual(option)
            index = self._option_to_index[option]
            strips = visual.to_strips(self, visual, width, None, style)
            strips = [
                strip.extend_cell_length(width, style.rich_style).apply_meta(
                    {"option": index}
                )
                for strip in strips
            ]
            if option._divider:
                style = self.get_visual_style("option-list--separator")
                rule_segments = [Segment("─" * width, style.rich_style)]
                strips.append(Strip(rule_segments, width))
            self._option_render_cache[cache_key] = strips
        return strips

    def _update_lines(self) -> None:
        line_cache = self._line_cache
        lines = line_cache.lines
        last_index = lines[-1][0] if lines else 0
        get_visual = self._get_visual
        width = self.scrollable_content_region.width

        if last_index < len(self.options) - 1:
            styles = self.get_component_styles("option-list--option")

            for index, option in enumerate(self.options[last_index:], last_index):
                line_cache.index_to_line[index] = len(line_cache.lines)
                line_count = (
                    get_visual(option).get_height(styles, width) + option._divider
                )
                line_cache.heights[index] = line_count
                line_cache.lines.extend(
                    [(index, line_no) for line_no in range(0, line_count)]
                )

        last_divider = self.options and self.options[-1]._divider
        self.virtual_size = Size(
            self.content_region.width, len(lines) - (1 if last_divider else 0)
        )

    def get_content_width(self, container: Size, viewport: Size) -> int:
        """Get maximum width of options."""
        container_width = container.width
        styles = self.styles
        get_visual_from_index = self._get_visual_from_index
        padding = self.get_component_styles("option-list--option").padding
        width = (
            max(
                get_visual_from_index(index).get_optimal_width(styles, container_width)
                for index in range(len(self.options))
            )
            + padding.width
        )
        return width

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        """Get height for the given width."""
        styles: RulesMap = self.get_component_styles("option-list--option")
        get_visual = self._get_visual
        height = sum(
            (
                get_visual(option).get_height(styles, width)
                + (1 if option._divider and not last else 0)
            )
            for last, option in loop_last(self.options)
        )
        return height

    def _get_line(self, style: Style, y: int) -> Strip:
        index, line_offset = self._lines[y]
        option = self.get_option_at_index(index)
        strips = self._get_option_render(option, style)
        return strips[line_offset]

    def render_line(self, y: int) -> Strip:
        line_number = self.scroll_offset.y + y
        try:
            option_index, line_offset = self._lines[line_number]
        except IndexError:
            return Strip.blank(self.scrollable_content_region.width)
        option = self.options[option_index]
        mouse_over = self.hover_option_index == option_index
        if option.disabled:
            component_class = "option-list--option-disabled"
        elif self.highlighted == option_index:
            component_class = "option-list--option-highlighted"
        elif mouse_over:
            component_class = "option-list--option-hover"
        else:
            component_class = "option-list--option"

        style = self.get_visual_style(component_class)
        strips = self._get_option_render(option, style)
        strip = strips[line_offset]
        return strip

    def validate_highlighted(self, highlighted: int | None) -> int | None:
        """Validate the `highlighted` property value on access."""
        if highlighted is None or not self.options:
            return None
        elif highlighted < 0:
            return 0
        elif highlighted >= len(self.options):
            return len(self.options) - 1
        return highlighted

    def watch_highlighted(self, highlighted: int | None) -> None:
        """React to the highlighted option having changed."""
        if highlighted is None:
            return

        if not self._options[highlighted].disabled:
            self.scroll_to_highlight()

        option: Option
        if highlighted is None:
            option = None
        else:
            option = self.options[highlighted]
        self.post_message(self.OptionHighlighted(self, option, highlighted))

    def scroll_to_highlight(self, top: bool = False) -> None:
        highlighted = self.highlighted
        if highlighted is None or not self.is_mounted:
            return

        y = self._index_to_line[highlighted]
        option = self.options[highlighted]
        height = self._heights[highlighted] - option._divider

        self.scroll_to_region(
            Region(0, y, self.scrollable_content_region.width, height),
            force=True,
            animate=False,
            top=top,
            immediate=True,
        )

    def action_cursor_up(self) -> None:
        """Move the highlight up to the previous enabled option."""
        self.highlighted = _widget_navigation.find_next_enabled(
            self.options,
            anchor=self.highlighted,
            direction=-1,
        )

    def action_cursor_down(self) -> None:
        """Move the highlight down to the next enabled option."""
        self.highlighted = _widget_navigation.find_next_enabled(
            self.options,
            anchor=self.highlighted,
            direction=1,
        )

    def action_first(self) -> None:
        """Move the highlight to the first enabled option."""
        self.highlighted = _widget_navigation.find_first_enabled(self.options)

    def action_last(self) -> None:
        """Move the highlight to the last enabled option."""
        self.highlighted = _widget_navigation.find_last_enabled(self.options)

    def _move_page(self, direction: _widget_navigation.Direction) -> None:
        """Move the height roughly by one page in the given direction.

        This method will attempt to avoid selecting a disabled option.

        Args:
            direction: `-1` to move up a page, `1` to move down a page.
        """

        height = self.content_region.height

        option_index = self.highlighted or 0

        y = min(
            self._index_to_line[option_index] + direction * height,
            len(self._lines) - 1,
        )
        option_index = self._lines[y][0]

        target_option = _widget_navigation.find_next_enabled_no_wrap(
            candidates=self._options,
            anchor=option_index,
            direction=direction,
            with_anchor=True,
        )
        if target_option is not None:
            self.highlighted = target_option

    def action_page_up(self):
        """Move the highlight up one page."""
        self._move_page(-1)

    def action_page_down(self):
        """Move the highlight down one page."""
        self._move_page(1)

    def action_select(self) -> None:
        """Select the currently highlighted option.

        If an option is selected then a
        [OptionList.OptionSelected][textual.widgets.OptionList.OptionSelected] will be posted.
        """
        if self.highlighted is None:
            return
        highlighted = self.highlighted
        option = self._options[highlighted]
        if highlighted is not None and not option.disabled:
            self.post_message(self.OptionSelected(self, option, highlighted))


if __name__ == "__main__":
    from textual.app import App, ComposeResult

    TEXT = """I must not fear.
Fear is the [u]mind-killer[/u].
Fear is the little-death that brings total obliteration.
I will face my fear.
I will permit it to pass over me and through me.
And when it has gone past, I will turn the inner eye to see its path.
Where the fear has gone there will be nothing. Only I will remain."""

    class OLApp(App):

        def compose(self) -> ComposeResult:
            yield OptionList(
                *(
                    ["Hello", "World!", None, TEXT, None, "Foo", "Bar", "Baz", None]
                    * 100
                )
            )

    app = OLApp()
    app.run()
