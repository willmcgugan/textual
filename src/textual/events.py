"""

Builtin events sent by Textual.

Events may be marked as "Bubbles" and "Verbose".
See the [events guide](/guide/events/#bubbling) for an explanation of bubbling.
Verbose events are excluded from the textual console, unless you explicitly request them with the `-v` switch as follows:

```
textual console -v
```
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Type, TypeVar

import rich.repr
from rich.style import Style
from typing_extensions import Self

from textual._types import CallbackType
from textual.geometry import Offset, Size
from textual.keys import _get_key_aliases
from textual.message import Message

MouseEventT = TypeVar("MouseEventT", bound="MouseEvent")

if TYPE_CHECKING:
    from textual.dom import DOMNode
    from textual.timer import Timer as TimerClass
    from textual.timer import TimerCallback
    from textual.widget import Widget


@rich.repr.auto
class Event(Message):
    """The base class for all events."""


@rich.repr.auto
class Callback(Event, bubble=False, verbose=True):
    """Sent by Textual to invoke a callback
    (see [call_next][textual.message_pump.MessagePump.call_next] and
    [call_later][textual.message_pump.MessagePump.call_later]).
    """

    def __init__(self, callback: CallbackType) -> None:
        self.callback = callback
        super().__init__()

    def __rich_repr__(self) -> rich.repr.Result:
        yield "callback", self.callback


@dataclass
class CursorPosition(Event, bubble=False):
    """Internal event used to retrieve the terminal's cursor position."""

    x: int
    y: int


class Load(Event, bubble=False):
    """
    Sent when the App is running but *before* the terminal is in application mode.

    Use this event to run any setup that doesn't require any visuals such as loading
    configuration and binding keys.

    - [ ] Bubbles
    - [ ] Verbose
    """


class Idle(Event, bubble=False):
    """Sent when there are no more items in the message queue.

    This is a pseudo-event in that it is created by the Textual system and doesn't go
    through the usual message queue.

    - [ ] Bubbles
    - [ ] Verbose
    """


class Action(Event):
    __slots__ = ["action"]

    def __init__(self, action: str) -> None:
        super().__init__()
        self.action = action

    def __rich_repr__(self) -> rich.repr.Result:
        yield "action", self.action


class Resize(Event, bubble=False):
    """Sent when the app or widget has been resized.

    - [ ] Bubbles
    - [ ] Verbose

    Args:
        size: The new size of the Widget.
        virtual_size: The virtual size (scrollable size) of the Widget.
        container_size: The size of the Widget's container widget.
    """

    __slots__ = ["size", "virtual_size", "container_size"]

    def __init__(
        self,
        size: Size,
        virtual_size: Size,
        container_size: Size | None = None,
        pixel_size: Size | None = None,
    ) -> None:
        self.size = size
        """The new size of the Widget."""
        self.virtual_size = virtual_size
        """The virtual size (scrollable size) of the Widget."""
        self.container_size = size if container_size is None else container_size
        """The size of the Widget's container widget."""
        self.pixel_size = pixel_size
        """Size of terminal window in pixels if known, or `None` if not known."""
        super().__init__()

    @classmethod
    def from_dimensions(
        cls, cells: tuple[int, int], pixels: tuple[int, int] | None
    ) -> Resize:
        """Construct from basic dimensions.

        Args:
            cells: tuple of (<width>, <height>) in cells.
            pixels: tuple of (<width>, <height>) in pixels if known, or `None` if not known.

        """
        size = Size(*cells)
        pixel_size = Size(*pixels) if pixels is not None else None
        return Resize(size, size, size, pixel_size)

    def can_replace(self, message: "Message") -> bool:
        return isinstance(message, Resize)

    def __rich_repr__(self) -> rich.repr.Result:
        yield "size", self.size
        yield "virtual_size", self.virtual_size, self.size
        yield "container_size", self.container_size, self.size
        yield "pixel_size", self.pixel_size, None


class Compose(Event, bubble=False, verbose=True):
    """Sent to a widget to request it to compose and mount children.

    This event is used internally by Textual.
    You won't typically need to explicitly handle it,

    - [ ] Bubbles
    - [X] Verbose
    """


class Mount(Event, bubble=False, verbose=False):
    """Sent when a widget is *mounted* and may receive messages.

    - [ ] Bubbles
    - [ ] Verbose
    """


class Unmount(Event, bubble=False, verbose=False):
    """Sent when a widget is unmounted and may no longer receive messages.

    - [ ] Bubbles
    - [ ] Verbose
    """


class Show(Event, bubble=False):
    """Sent when a widget is first displayed.

    - [ ] Bubbles
    - [ ] Verbose
    """


class Hide(Event, bubble=False):
    """Sent when a widget has been hidden.

    - [ ] Bubbles
    - [ ] Verbose

    Sent when any of the following conditions apply:

    - The widget is removed from the DOM.
    - The widget is no longer displayed because it has been scrolled or clipped from the terminal or its container.
    - The widget has its `display` attribute set to `False`.
    - The widget's `display` style is set to `"none"`.
    """


class Ready(Event, bubble=False):
    """Sent to the `App` when the DOM is ready and the first frame has been displayed.

    - [ ] Bubbles
    - [ ] Verbose
    """


@rich.repr.auto
class MouseCapture(Event, bubble=False):
    """Sent when the mouse has been captured.

    - [ ] Bubbles
    - [ ] Verbose

    When a mouse has been captured, all further mouse events will be sent to the capturing widget.

    Args:
        mouse_position: The position of the mouse when captured.
    """

    def __init__(self, mouse_position: Offset) -> None:
        super().__init__()
        self.mouse_position = mouse_position
        """The position of the mouse when captured."""

    def __rich_repr__(self) -> rich.repr.Result:
        yield None, self.mouse_position


@rich.repr.auto
class MouseRelease(Event, bubble=False):
    """Mouse has been released.

    - [ ] Bubbles
    - [ ] Verbose

    Args:
        mouse_position: The position of the mouse when released.
    """

    def __init__(self, mouse_position: Offset) -> None:
        super().__init__()
        self.mouse_position = mouse_position
        """The position of the mouse when released."""

    def __rich_repr__(self) -> rich.repr.Result:
        yield None, self.mouse_position


class InputEvent(Event):
    """Base class for input events."""


@rich.repr.auto
class Key(InputEvent):
    """Sent when the user hits a key on the keyboard.

    - [X] Bubbles
    - [ ] Verbose

    Args:
        key: The key that was pressed.
        character: A printable character or `None` if it is not printable.
    """

    __slots__ = ["key", "character", "aliases"]

    def __init__(self, key: str, character: str | None) -> None:
        super().__init__()
        self.key = key
        """The key that was pressed."""
        self.character = (
            (key if len(key) == 1 else None) if character is None else character
        )
        """A printable character or ``None`` if it is not printable."""
        self.aliases: list[str] = _get_key_aliases(key)
        """The aliases for the key, including the key itself."""

    def __rich_repr__(self) -> rich.repr.Result:
        yield "key", self.key
        yield "character", self.character
        yield "name", self.name
        yield "is_printable", self.is_printable
        yield "aliases", self.aliases, [self.key]

    @property
    def name(self) -> str:
        """Name of a key suitable for use as a Python identifier."""
        return _key_to_identifier(self.key).lower()

    @property
    def name_aliases(self) -> list[str]:
        """The corresponding name for every alias in `aliases` list."""
        return [_key_to_identifier(key) for key in self.aliases]

    @property
    def is_printable(self) -> bool:
        """Check if the key is printable (produces a unicode character).

        Returns:
            `True` if the key is printable.
        """
        return False if self.character is None else self.character.isprintable()


def _key_to_identifier(key: str) -> str:
    """Convert the key string to a name suitable for use as a Python identifier."""
    key_no_modifiers = key.split("+")[-1]
    if len(key_no_modifiers) == 1 and key_no_modifiers.isupper():
        if "+" in key:
            key = f"{key.rpartition('+')[0]}+upper_{key_no_modifiers}"
        else:
            key = f"upper_{key_no_modifiers}"
    return key.replace("+", "_").lower()


@rich.repr.auto
class MouseEvent(InputEvent, bubble=True):
    """Sent in response to a mouse event.

    - [X] Bubbles
    - [ ] Verbose

    Args:
        widget: The widget under the mouse.
        x: The relative x coordinate.
        y: The relative y coordinate.
        delta_x: Change in x since the last message.
        delta_y: Change in y since the last message.
        button: Indexed of the pressed button.
        shift: True if the shift key is pressed.
        meta: True if the meta key is pressed.
        ctrl: True if the ctrl key is pressed.
        screen_x: The absolute x coordinate.
        screen_y: The absolute y coordinate.
        style: The Rich Style under the mouse cursor.
    """

    __slots__ = [
        "widget",
        "_x",
        "_y",
        "_delta_x",
        "_delta_y",
        "button",
        "shift",
        "meta",
        "ctrl",
        "_screen_x",
        "_screen_y",
        "_style",
    ]

    def __init__(
        self,
        widget: Widget | None,
        x: float,
        y: float,
        delta_x: float,
        delta_y: float,
        button: int,
        shift: bool,
        meta: bool,
        ctrl: bool,
        screen_x: float | None = None,
        screen_y: float | None = None,
        style: Style | None = None,
    ) -> None:
        super().__init__()
        self.widget: Widget | None = widget
        """The widget under the mouse at the time of a click."""
        self._x = x
        """The relative x coordinate."""
        self._y = y
        """The relative y coordinate."""
        self._delta_x = delta_x
        """Change in x since the last message."""
        self._delta_y = delta_y
        """Change in y since the last message."""
        self.button = button
        """Indexed of the pressed button."""
        self.shift = shift
        """`True` if the shift key is pressed."""
        self.meta = meta
        """`True` if the meta key is pressed."""
        self.ctrl = ctrl
        """`True` if the ctrl key is pressed."""
        self._screen_x = x if screen_x is None else screen_x
        """The absolute x coordinate."""
        self._screen_y = y if screen_y is None else screen_y
        """The absolute y coordinate."""
        self._style = style or Style()

    @property
    def x(self) -> int:
        return int(self._x)

    @property
    def y(self) -> int:
        return int(self._y)

    @property
    def delta_x(self) -> int:
        return int(self._delta_x)

    @property
    def delta_y(self) -> int:
        return int(self._delta_y)

    @property
    def screen_x(self) -> int:
        return int(self._screen_x)

    @property
    def screen_y(self) -> int:
        return int(self._screen_y)

    @classmethod
    def from_event(
        cls: Type[MouseEventT], widget: Widget, event: MouseEvent
    ) -> MouseEventT:
        new_event = cls(
            widget,
            event._x,
            event._y,
            event._delta_x,
            event._delta_y,
            event.button,
            event.shift,
            event.meta,
            event.ctrl,
            event._screen_x,
            event._screen_y,
            event._style,
        )
        return new_event

    def __rich_repr__(self) -> rich.repr.Result:
        yield self.widget
        yield "x", self._x
        yield "y", self._y
        yield "delta_x", self._delta_x, 0
        yield "delta_y", self._delta_y, 0
        if self.screen_x != self.x:
            yield "screen_x", self._screen_x
        if self.screen_y != self.y:
            yield "screen_y", self._screen_y
        yield "button", self.button, 0
        yield "shift", self.shift, False
        yield "meta", self.meta, False
        yield "ctrl", self.ctrl, False

    @property
    def control(self) -> Widget | None:
        return self.widget

    @property
    def offset(self) -> Offset:
        """The mouse coordinate as an offset.

        Returns:
            Mouse coordinate.
        """
        return Offset(self.x, self.y)

    @property
    def screen_offset(self) -> Offset:
        """Mouse coordinate relative to the screen."""
        return Offset(self.screen_x, self.screen_y)

    @property
    def delta(self) -> Offset:
        """Mouse coordinate delta (change since last event)."""
        return Offset(self.delta_x, self.delta_y)

    @property
    def style(self) -> Style:
        """The (Rich) Style under the cursor."""
        return self._style or Style()

    @style.setter
    def style(self, style: Style) -> None:
        self._style = style

    def get_content_offset(self, widget: Widget) -> Offset | None:
        """Get offset within a widget's content area, or None if offset is not in content (i.e. padding or border).

        Args:
            widget: Widget receiving the event.

        Returns:
            An offset where the origin is at the top left of the content area.
        """
        if self.screen_offset not in widget.content_region:
            return None
        return self.get_content_offset_capture(widget)

    def get_content_offset_capture(self, widget: Widget) -> Offset:
        """Get offset from a widget's content area.

        This method works even if the offset is outside the widget content region.

        Args:
            widget: Widget receiving the event.

        Returns:
            An offset where the origin is at the top left of the content area.
        """
        return self.offset - widget.gutter.top_left

    def _apply_offset(self, x: int, y: int) -> MouseEvent:
        return self.__class__(
            self.widget,
            x=self._x + x,
            y=self._y + y,
            delta_x=self._delta_x,
            delta_y=self._delta_y,
            button=self.button,
            shift=self.shift,
            meta=self.meta,
            ctrl=self.ctrl,
            screen_x=self._screen_x,
            screen_y=self._screen_y,
            style=self.style,
        )


@rich.repr.auto
class MouseMove(MouseEvent, bubble=True, verbose=True):
    """Sent when the mouse cursor moves.

    - [X] Bubbles
    - [X] Verbose
    """


@rich.repr.auto
class MouseDown(MouseEvent, bubble=True, verbose=True):
    """Sent when a mouse button is pressed.

    - [X] Bubbles
    - [X] Verbose
    """


@rich.repr.auto
class MouseUp(MouseEvent, bubble=True, verbose=True):
    """Sent when a mouse button is released.

    - [X] Bubbles
    - [X] Verbose
    """


@rich.repr.auto
class MouseScrollDown(MouseEvent, bubble=True, verbose=True):
    """Sent when the mouse wheel is scrolled *down*.

    - [X] Bubbles
    - [X] Verbose
    """


@rich.repr.auto
class MouseScrollUp(MouseEvent, bubble=True, verbose=True):
    """Sent when the mouse wheel is scrolled *up*.

    - [X] Bubbles
    - [X] Verbose
    """


class Click(MouseEvent, bubble=True):
    """Sent when a widget is clicked.

    - [X] Bubbles
    - [ ] Verbose

    Args:
        chain: The number of clicks in the chain. 2 is a double click, 3 is a triple click, etc.
    """

    def __init__(
        self,
        widget: Widget | None,
        x: int,
        y: int,
        delta_x: int,
        delta_y: int,
        button: int,
        shift: bool,
        meta: bool,
        ctrl: bool,
        screen_x: int | None = None,
        screen_y: int | None = None,
        style: Style | None = None,
        chain: int = 1,
    ) -> None:
        super().__init__(
            widget,
            x,
            y,
            delta_x,
            delta_y,
            button,
            shift,
            meta,
            ctrl,
            screen_x,
            screen_y,
            style,
        )
        self.chain = chain

    @classmethod
    def from_event(
        cls: Type[Self],
        widget: Widget,
        event: MouseEvent,
        chain: int = 1,
    ) -> Self:
        new_event = cls(
            widget,
            event.x,
            event.y,
            event.delta_x,
            event.delta_y,
            event.button,
            event.shift,
            event.meta,
            event.ctrl,
            event.screen_x,
            event.screen_y,
            event._style,
            chain=chain,
        )
        return new_event

    def _apply_offset(self, x: int, y: int) -> Self:
        return self.__class__(
            self.widget,
            x=self.x + x,
            y=self.y + y,
            delta_x=self.delta_x,
            delta_y=self.delta_y,
            button=self.button,
            shift=self.shift,
            meta=self.meta,
            ctrl=self.ctrl,
            screen_x=self.screen_x,
            screen_y=self.screen_y,
            style=self.style,
            chain=self.chain,
        )

    def __rich_repr__(self) -> rich.repr.Result:
        yield from super().__rich_repr__()
        yield "chain", self.chain


@rich.repr.auto
class Timer(Event, bubble=False, verbose=True):
    """Sent in response to a timer.

    - [ ] Bubbles
    - [X] Verbose
    """

    __slots__ = ["timer", "time", "count", "callback"]

    def __init__(
        self,
        timer: "TimerClass",
        time: float,
        count: int = 0,
        callback: TimerCallback | None = None,
    ) -> None:
        super().__init__()
        self.timer = timer
        self.time = time
        self.count = count
        self.callback = callback

    def __rich_repr__(self) -> rich.repr.Result:
        yield self.timer.name
        yield "count", self.count


class Enter(Event, bubble=True, verbose=True):
    """Sent when the mouse is moved over a widget.

    Note that this event bubbles, so a widget may receive this event when the mouse
    moves over a child widget. Check the `node` attribute for the widget directly under
    the mouse.

    - [X] Bubbles
    - [X] Verbose
    """

    __slots__ = ["node"]

    def __init__(self, node: DOMNode) -> None:
        self.node = node
        """The node directly under the mouse."""
        super().__init__()

    @property
    def control(self) -> DOMNode:
        """Alias for the `node` under the mouse."""
        return self.node


class Leave(Event, bubble=True, verbose=True):
    """Sent when the mouse is moved away from a widget, or if a widget is
    programmatically disabled while hovered.

    Note that this widget bubbles, so a widget may receive Leave events for any child widgets.
    Check the `node` parameter for the original widget that was previously under the mouse.


    - [X] Bubbles
    - [X] Verbose
    """

    __slots__ = ["node"]

    def __init__(self, node: DOMNode) -> None:
        self.node = node
        """The node that was previously directly under the mouse."""
        super().__init__()

    @property
    def control(self) -> DOMNode:
        """Alias for the `node` that was previously under the mouse."""
        return self.node


class Focus(Event, bubble=False):
    """Sent when a widget is focussed.

    - [ ] Bubbles
    - [ ] Verbose

    Args:
        from_app_focus: True if this focus event has been sent because the app itself has
            regained focus (via an AppFocus event). False if the focus came from within
            the Textual app (e.g. via the user pressing tab or a programmatic setting
            of the focused widget).
    """

    def __init__(self, from_app_focus: bool = False) -> None:
        self.from_app_focus = from_app_focus
        super().__init__()

    def __rich_repr__(self) -> rich.repr.Result:
        yield from super().__rich_repr__()
        yield "from_app_focus", self.from_app_focus


class Blur(Event, bubble=False):
    """Sent when a widget is blurred (un-focussed).

    - [ ] Bubbles
    - [ ] Verbose
    """


class AppFocus(Event, bubble=False):
    """Sent when the app has focus.

    - [ ] Bubbles
    - [ ] Verbose

    Note:
        Only available when running within a terminal that supports
        `FocusIn`, or when running via textual-web.
    """


class AppBlur(Event, bubble=False):
    """Sent when the app loses focus.

    - [ ] Bubbles
    - [ ] Verbose

    Note:
        Only available when running within a terminal that supports
        `FocusOut`, or when running via textual-web.
    """


@dataclass
class DescendantFocus(Event, bubble=True, verbose=True):
    """Sent when a child widget is focussed.

    - [X] Bubbles
    - [X] Verbose
    """

    widget: Widget
    """The widget that was focused."""

    @property
    def control(self) -> Widget:
        """The widget that was focused (alias of `widget`)."""
        return self.widget


@dataclass
class DescendantBlur(Event, bubble=True, verbose=True):
    """Sent when a child widget is blurred.

    - [X] Bubbles
    - [X] Verbose
    """

    widget: Widget
    """The widget that was blurred."""

    @property
    def control(self) -> Widget:
        """The widget that was blurred (alias of `widget`)."""
        return self.widget


@rich.repr.auto
class Paste(Event, bubble=True):
    """Event containing text that was pasted into the Textual application.
    This event will only appear when running in a terminal emulator that supports
    bracketed paste mode. Textual will enable bracketed pastes when an app starts,
    and disable it when the app shuts down.

    - [X] Bubbles
    - [ ] Verbose


    Args:
        text: The text that has been pasted.
    """

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text
        """The text that was pasted."""

    def __rich_repr__(self) -> rich.repr.Result:
        yield "text", self.text


class ScreenResume(Event, bubble=False):
    """Sent to screen that has been made active.

    - [ ] Bubbles
    - [ ] Verbose
    """


class ScreenSuspend(Event, bubble=False):
    """Sent to screen when it is no longer active.

    - [ ] Bubbles
    - [ ] Verbose
    """


@rich.repr.auto
class Print(Event, bubble=False):
    """Sent to a widget that is capturing [`print`][print].

    - [ ] Bubbles
    - [ ] Verbose

    Args:
        text: Text that was printed.
        stderr: `True` if the print was to stderr, or `False` for stdout.

    Note:
        Python's [`print`][print] output can be captured with
        [`App.begin_capture_print`][textual.app.App.begin_capture_print].
    """

    def __init__(self, text: str, stderr: bool = False) -> None:
        super().__init__()
        self.text = text
        """The text that was printed."""
        self.stderr = stderr
        """`True` if the print was to stderr, or `False` for stdout."""

    def __rich_repr__(self) -> rich.repr.Result:
        yield self.text
        yield self.stderr


@dataclass
class DeliveryComplete(Event, bubble=False):
    """Sent to App when a file has been delivered."""

    key: str
    """The delivery key associated with the delivery.
    
    This is the same key that was returned by `App.deliver_text`/`App.deliver_binary`.
    """

    path: Path | None = None
    """The path where the file was saved, or `None` if the path is not available, for
    example if the file was delivered via web browser.
    """

    name: str | None = None
    """Optional name returned to the app to identify the download."""


@dataclass
class DeliveryFailed(Event, bubble=False):
    """Sent to App when a file delivery fails."""

    key: str
    """The delivery key associated with the delivery."""

    exception: BaseException
    """The exception that was raised during the delivery."""

    name: str | None = None
    """Optional name returned to the app to identify the download."""
