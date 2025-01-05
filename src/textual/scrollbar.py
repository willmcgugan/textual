"""
Contains the widgets that manage Textual scrollbars.

!!! note

    You will not typically need this for most apps.

"""

from __future__ import annotations

from math import ceil
from typing import ClassVar, Type

import rich.repr
from rich.color import Color
from rich.console import Console, ConsoleOptions, RenderableType, RenderResult
from rich.segment import Segment, Segments
from rich.style import Style, StyleType

from textual import events
from textual.geometry import Offset
from textual.message import Message
from textual.reactive import Reactive
from textual.renderables.blank import Blank
from textual.widget import Widget


class ScrollMessage(Message, bubble=False):
    """Base class for all scrollbar messages."""


@rich.repr.auto
class ScrollUp(ScrollMessage, verbose=True):
    """Message sent when clicking above handle."""


@rich.repr.auto
class ScrollDown(ScrollMessage, verbose=True):
    """Message sent when clicking below handle."""


@rich.repr.auto
class ScrollLeft(ScrollMessage, verbose=True):
    """Message sent when clicking above handle."""


@rich.repr.auto
class ScrollRight(ScrollMessage, verbose=True):
    """Message sent when clicking below handle."""


class ScrollTo(ScrollMessage, verbose=True):
    """Message sent when click and dragging handle."""

    __slots__ = ["x", "y", "animate"]

    def __init__(
        self,
        x: float | None = None,
        y: float | None = None,
        animate: bool = True,
    ) -> None:
        self.x = x
        self.y = y
        self.animate = animate
        super().__init__()

    def __rich_repr__(self) -> rich.repr.Result:
        yield "x", self.x, None
        yield "y", self.y, None
        yield "animate", self.animate, True


class ScrollBarRender:
    VERTICAL_BARS: ClassVar[list[str]] = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", " "]
    """Glyphs used for vertical scrollbar ends, for smoother display."""
    HORIZONTAL_BARS: ClassVar[list[str]] = ["▉", "▊", "▋", "▌", "▍", "▎", "▏", " "]
    """Glyphs used for horizontal scrollbar ends, for smoother display."""
    BLANK_GLYPH: ClassVar[str] = " "
    """Glyph used for the main body of the scrollbar"""

    def __init__(
        self,
        virtual_size: int = 100,
        window_size: int = 0,
        position: float = 0,
        thickness: int = 1,
        vertical: bool = True,
        style: StyleType = "bright_magenta on #555555",
    ) -> None:
        self.virtual_size = virtual_size
        self.window_size = window_size
        self.position = position
        self.thickness = thickness
        self.vertical = vertical
        self.style = style

    @classmethod
    def render_bar(
        cls,
        size: int = 25,
        virtual_size: float = 50,
        window_size: float = 20,
        position: float = 0,
        thickness: int = 1,
        vertical: bool = True,
        back_color: Color = Color.parse("#555555"),
        bar_color: Color = Color.parse("bright_magenta"),
    ) -> Segments:
        if vertical:
            bars = cls.VERTICAL_BARS
        else:
            bars = cls.HORIZONTAL_BARS

        back = back_color
        bar = bar_color

        len_bars = len(bars)

        width_thickness = thickness if vertical else 1

        _Segment = Segment
        _Style = Style
        blank = cls.BLANK_GLYPH * width_thickness

        foreground_meta = {"@mouse.down": "grab"}
        if window_size and size and virtual_size and size != virtual_size:
            bar_ratio = virtual_size / size
            thumb_size = max(1, window_size / bar_ratio)

            position_ratio = position / (virtual_size - window_size)
            position = (size - thumb_size) * position_ratio

            start = int(position * len_bars)
            end = start + ceil(thumb_size * len_bars)

            start_index, start_bar = divmod(max(0, start), len_bars)
            end_index, end_bar = divmod(max(0, end), len_bars)

            upper = {"@mouse.up": "scroll_up"}
            lower = {"@mouse.up": "scroll_down"}

            upper_back_segment = Segment(blank, _Style(bgcolor=back, meta=upper))
            lower_back_segment = Segment(blank, _Style(bgcolor=back, meta=lower))

            segments = [upper_back_segment] * int(size)
            segments[end_index:] = [lower_back_segment] * (size - end_index)

            segments[start_index:end_index] = [
                _Segment(blank, _Style(color=bar, reverse=True, meta=foreground_meta))
            ] * (end_index - start_index)

            # Apply the smaller bar characters to head and tail of scrollbar for more "granularity"
            if start_index < len(segments):
                bar_character = bars[len_bars - 1 - start_bar]
                if bar_character != " ":
                    segments[start_index] = _Segment(
                        bar_character * width_thickness,
                        (
                            _Style(bgcolor=back, color=bar, meta=foreground_meta)
                            if vertical
                            else _Style(
                                bgcolor=back,
                                color=bar,
                                meta=foreground_meta,
                                reverse=True,
                            )
                        ),
                    )
            if end_index < len(segments):
                bar_character = bars[len_bars - 1 - end_bar]
                if bar_character != " ":
                    segments[end_index] = _Segment(
                        bar_character * width_thickness,
                        (
                            _Style(
                                bgcolor=back,
                                color=bar,
                                meta=foreground_meta,
                                reverse=True,
                            )
                            if vertical
                            else _Style(bgcolor=back, color=bar, meta=foreground_meta)
                        ),
                    )
        else:
            style = _Style(bgcolor=back)
            segments = [_Segment(blank, style=style)] * int(size)
        if vertical:
            return Segments(segments, new_lines=True)
        else:
            return Segments((segments + [_Segment.line()]) * thickness, new_lines=False)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        size = (
            (options.height or console.height)
            if self.vertical
            else (options.max_width or console.width)
        )
        thickness = (
            (options.max_width or console.width)
            if self.vertical
            else (options.height or console.height)
        )

        _style = console.get_style(self.style)

        bar = self.render_bar(
            size=size,
            window_size=self.window_size,
            virtual_size=self.virtual_size,
            position=self.position,
            vertical=self.vertical,
            thickness=thickness,
            back_color=_style.bgcolor or Color.parse("#555555"),
            bar_color=_style.color or Color.parse("bright_magenta"),
        )
        yield bar


@rich.repr.auto
class ScrollBar(Widget):
    renderer: ClassVar[Type[ScrollBarRender]] = ScrollBarRender
    """The class used for rendering scrollbars.
    This can be overridden and set to a ScrollBarRender-derived class
    in order to delegate all scrollbar rendering to that class. E.g.:

    ```
    class MyScrollBarRender(ScrollBarRender): ...

    app = MyApp()
    ScrollBar.renderer = MyScrollBarRender
    app.run()
    ```

    Because this variable is accessed through specific instances
    (rather than through the class ScrollBar itself) it is also possible
    to set this on specific scrollbar instance to change only that
    instance:

    ```
    my_widget.horizontal_scrollbar.renderer = MyScrollBarRender
    ```
    """

    DEFAULT_CLASSES = "-textual-system"

    def __init__(
        self, vertical: bool = True, name: str | None = None, *, thickness: int = 1
    ) -> None:
        self.vertical = vertical
        self.thickness = thickness
        self.grabbed_position: float = 0
        super().__init__(name=name)
        self.auto_links = False

    window_virtual_size: Reactive[int] = Reactive(100)
    window_size: Reactive[int] = Reactive(0)
    position: Reactive[float] = Reactive(0)
    mouse_over: Reactive[bool] = Reactive(False)
    grabbed: Reactive[Offset | None] = Reactive(None)

    def __rich_repr__(self) -> rich.repr.Result:
        yield from super().__rich_repr__()
        yield "window_virtual_size", self.window_virtual_size
        yield "window_size", self.window_size
        yield "position", self.position
        if self.thickness > 1:
            yield "thickness", self.thickness

    def render(self) -> RenderableType:
        assert self.parent is not None
        styles = self.parent.styles
        if self.grabbed:
            background = styles.scrollbar_background_active
            color = styles.scrollbar_color_active
        elif self.mouse_over:
            background = styles.scrollbar_background_hover
            color = styles.scrollbar_color_hover
        else:
            background = styles.scrollbar_background
            color = styles.scrollbar_color
        color = background + color
        scrollbar_style = Style.from_color(color.rich_color, background.rich_color)
        if self.screen.styles.scrollbar_color.a == 0:
            return self.renderer(vertical=self.vertical, style=scrollbar_style)
        return self._render_bar(scrollbar_style)

    def _render_bar(self, scrollbar_style: Style) -> RenderableType:
        """Get a renderable for the scrollbar with given style.

        Args:
            scrollbar_style: Scrollbar style.

        Returns:
            Scrollbar renderable.
        """
        window_size = (
            self.window_size if self.window_size < self.window_virtual_size else 0
        )
        virtual_size = self.window_virtual_size

        return self.renderer(
            virtual_size=ceil(virtual_size),
            window_size=ceil(window_size),
            position=self.position,
            thickness=self.thickness,
            vertical=self.vertical,
            style=scrollbar_style,
        )

    def _on_hide(self, event: events.Hide) -> None:
        if self.grabbed:
            self.release_mouse()
            self.grabbed = None

    def _on_enter(self, event: events.Enter) -> None:
        if event.node is self:
            self.mouse_over = True

    def _on_leave(self, event: events.Leave) -> None:
        if event.node is self:
            self.mouse_over = False

    def action_scroll_down(self) -> None:
        """Scroll vertical scrollbars down, horizontal scrollbars right."""
        if not self.grabbed:
            self.post_message(ScrollDown() if self.vertical else ScrollRight())

    def action_scroll_up(self) -> None:
        """Scroll vertical scrollbars up, horizontal scrollbars left."""
        if not self.grabbed:
            self.post_message(ScrollUp() if self.vertical else ScrollLeft())

    def action_grab(self) -> None:
        """Begin capturing the mouse cursor."""
        self.capture_mouse()

    async def _on_mouse_down(self, event: events.MouseDown) -> None:
        # We don't want mouse events on the scrollbar bubbling
        event.stop()

    async def _on_mouse_up(self, event: events.MouseUp) -> None:
        if self.grabbed:
            self.release_mouse()
            self.grabbed = None
        event.stop()

    def _on_mouse_capture(self, event: events.MouseCapture) -> None:
        self.grabbed = event.mouse_position
        self.grabbed_position = self.position

    def _on_mouse_release(self, event: events.MouseRelease) -> None:
        self.grabbed = None
        event.stop()

    async def _on_mouse_move(self, event: events.MouseMove) -> None:
        if self.grabbed and self.window_size:
            x: float | None = None
            y: float | None = None
            if self.vertical:
                virtual_size = self.window_virtual_size
                y = self.grabbed_position + (
                    (event._screen_y - self.grabbed.y)
                    * (virtual_size / self.window_size)
                )
            else:
                virtual_size = self.window_virtual_size
                x = self.grabbed_position + (
                    (event._screen_x - self.grabbed.x)
                    * (virtual_size / self.window_size)
                )
            print(event)
            self.post_message(ScrollTo(x=x, y=y))
        event.stop()

    async def _on_click(self, event: events.Click) -> None:
        event.stop()


class ScrollBarCorner(Widget):
    """Widget which fills the gap between horizontal and vertical scrollbars,
    should they both be present."""

    def __init__(self, name: str | None = None):
        super().__init__(name=name)

    def render(self) -> RenderableType:
        assert self.parent is not None
        styles = self.parent.styles
        color = styles.scrollbar_corner_color
        return Blank(color)
