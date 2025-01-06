"""

This module contains the `Screen` class and related objects.

The `Screen` class is a special widget which represents the content in the terminal. See [Screens](/guide/screens/) for details.

"""

from __future__ import annotations

import asyncio
from functools import partial
from operator import attrgetter
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    ClassVar,
    Generic,
    Iterable,
    Iterator,
    Optional,
    TypeVar,
    Union,
)

import rich.repr
from rich.console import RenderableType
from rich.style import Style

from textual import constants, errors, events, messages
from textual._arrange import arrange
from textual._callback import invoke
from textual._compositor import Compositor, MapGeometry
from textual._context import active_message_pump, visible_screen_stack
from textual._path import (
    CSSPathType,
    _css_path_type_as_list,
    _make_path_object_relative,
)
from textual._types import CallbackType
from textual.await_complete import AwaitComplete
from textual.binding import ActiveBinding, Binding, BindingsMap
from textual.css.match import match
from textual.css.parse import parse_selectors
from textual.css.query import NoMatches, QueryType
from textual.dom import DOMNode
from textual.errors import NoWidget
from textual.geometry import Offset, Region, Size
from textual.keys import key_to_character
from textual.layout import DockArrangeResult
from textual.reactive import Reactive
from textual.renderables.background_screen import BackgroundScreen
from textual.renderables.blank import Blank
from textual.signal import Signal
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Tooltip
from textual.widgets._toast import ToastRack

if TYPE_CHECKING:
    from typing_extensions import Final

    from textual.command import Provider

    # Unused & ignored imports are needed for the docs to link to these objects:
    from textual.message_pump import MessagePump

# Screen updates will be batched so that they don't happen more often than 60 times per second:
UPDATE_PERIOD: Final[float] = 1 / constants.MAX_FPS

ScreenResultType = TypeVar("ScreenResultType")
"""The result type of a screen."""

ScreenResultCallbackType = Union[
    Callable[[Optional[ScreenResultType]], None],
    Callable[[Optional[ScreenResultType]], Awaitable[None]],
]
"""Type of a screen result callback function."""


@rich.repr.auto
class ResultCallback(Generic[ScreenResultType]):
    """Holds the details of a callback."""

    def __init__(
        self,
        requester: MessagePump,
        callback: ScreenResultCallbackType[ScreenResultType] | None,
        future: asyncio.Future[ScreenResultType] | None = None,
    ) -> None:
        """Initialise the result callback object.

        Args:
            requester: The object making a request for the callback.
            callback: The callback function.
            future: A Future to hold the result.
        """
        self.requester = requester
        """The object in the DOM that requested the callback."""
        self.callback: ScreenResultCallbackType | None = callback
        """The callback function."""
        self.future = future
        """A future for the result"""

    def __call__(self, result: ScreenResultType) -> None:
        """Call the callback, passing the given result.

        Args:
            result: The result to pass to the callback.

        Note:
            If the requested or the callback are `None` this will be a no-op.
        """
        if self.future is not None:
            self.future.set_result(result)
        if self.requester is not None and self.callback is not None:
            self.requester.call_next(self.callback, result)
        self.callback = None


@rich.repr.auto
class Screen(Generic[ScreenResultType], Widget):
    """The base class for screens."""

    AUTO_FOCUS: ClassVar[str | None] = None
    """A selector to determine what to focus automatically when the screen is activated.

    The widget focused is the first that matches the given [CSS selector](/guide/queries/#query-selectors).
    Set to `None` to inherit the value from the screen's app.
    Set to `""` to disable auto focus.
    """

    CSS: ClassVar[str] = ""
    """Inline CSS, useful for quick scripts. Rules here take priority over CSS_PATH.

    Note:
        This CSS applies to the whole app.
    """
    CSS_PATH: ClassVar[CSSPathType | None] = None
    """File paths to load CSS from.

    Note:
        This CSS applies to the whole app.
    """

    DEFAULT_CSS = """
    Screen {
        layout: vertical;
        overflow-y: auto;
        background: $background;        
        
        &:inline {
            height: auto;
            min-height: 1;
            border-top: tall $background;
            border-bottom: tall $background;
        }

        &:ansi {
            background: ansi_default;
            color: ansi_default;

            &.-screen-suspended {                                            
                text-style: dim;
                ScrollBar {
                    text-style: not dim;
                }
            }
        }
    }
    """

    TITLE: ClassVar[str | None] = None
    """A class variable to set the *default* title for the screen.

    This overrides the app title.
    To update the title while the screen is running,
    you can set the [title][textual.screen.Screen.title] attribute.
    """

    SUB_TITLE: ClassVar[str | None] = None
    """A class variable to set the *default* sub-title for the screen.

    This overrides the app sub-title.
    To update the sub-title while the screen is running,
    you can set the [sub_title][textual.screen.Screen.sub_title] attribute.
    """

    focused: Reactive[Widget | None] = Reactive(None)
    """The focused [widget][textual.widget.Widget] or `None` for no focus.
    To set focus, do not update this value directly. Use [set_focus][textual.screen.Screen.set_focus] instead."""
    stack_updates: Reactive[int] = Reactive(0, repaint=False)
    """An integer that updates when the screen is resumed."""
    sub_title: Reactive[str | None] = Reactive(None, compute=False)
    """Screen sub-title to override [the app sub-title][textual.app.App.sub_title]."""
    title: Reactive[str | None] = Reactive(None, compute=False)
    """Screen title to override [the app title][textual.app.App.title]."""

    COMMANDS: ClassVar[set[type[Provider] | Callable[[], type[Provider]]]] = set()
    """Command providers used by the [command palette](/guide/command_palette), associated with the screen.

    Should be a set of [`command.Provider`][textual.command.Provider] classes.
    """
    ALLOW_IN_MAXIMIZED_VIEW: ClassVar[str | None] = None
    """A selector for the widgets (direct children of Screen) that are allowed in the maximized view (in addition to maximized widget). Or
    `None` to default to [App.ALLOW_IN_MAXIMIZED_VIEW][textual.app.App.ALLOW_IN_MAXIMIZED_VIEW]"""

    ESCAPE_TO_MINIMIZE: ClassVar[bool | None] = None
    """Use escape key to minimize (potentially overriding bindings) or `None` to defer to [`App.ESCAPE_TO_MINIMIZE`][textual.app.App.ESCAPE_TO_MINIMIZE]."""

    maximized: Reactive[Widget | None] = Reactive(None, layout=True)
    """The currently maximized widget, or `None` for no maximized widget."""

    BINDINGS = [
        Binding("tab", "app.focus_next", "Focus Next", show=False),
        Binding("shift+tab", "app.focus_previous", "Focus Previous", show=False),
    ]

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Initialize the screen.

        Args:
            name: The name of the screen.
            id: The ID of the screen in the DOM.
            classes: The CSS classes for the screen.
        """
        self._modal = False
        super().__init__(name=name, id=id, classes=classes)
        self._compositor = Compositor()
        self._dirty_widgets: set[Widget] = set()
        self.__update_timer: Timer | None = None
        self._callbacks: list[tuple[CallbackType, MessagePump]] = []
        self._result_callbacks: list[ResultCallback[ScreenResultType | None]] = []

        self._tooltip_widget: Widget | None = None
        self._tooltip_timer: Timer | None = None

        css_paths = [
            _make_path_object_relative(css_path, self)
            for css_path in (
                _css_path_type_as_list(self.CSS_PATH)
                if self.CSS_PATH is not None
                else []
            )
        ]
        self.css_path = css_paths

        self.title = self.TITLE
        self.sub_title = self.SUB_TITLE

        self.screen_layout_refresh_signal: Signal[Screen] = Signal(
            self, "layout-refresh"
        )
        """The signal that is published when the screen's layout is refreshed."""

        self.bindings_updated_signal: Signal[Screen] = Signal(self, "bindings_updated")
        """A signal published when the bindings have been updated"""

        self._css_update_count = -1
        """Track updates to CSS."""

    @property
    def is_modal(self) -> bool:
        """Is the screen modal?"""
        return self._modal

    @property
    def is_current(self) -> bool:
        """Is the screen current (i.e. visible to user)?"""
        from textual.app import ScreenStackError

        try:
            return self.app.screen is self or self in self.app._background_screens
        except ScreenStackError:
            return False

    @property
    def _update_timer(self) -> Timer:
        """Timer used to perform updates."""
        if self.__update_timer is None:
            self.__update_timer = self.set_interval(
                UPDATE_PERIOD, self._on_timer_update, name="screen_update", pause=True
            )
        return self.__update_timer

    @property
    def layers(self) -> tuple[str, ...]:
        """Layers from parent.

        Returns:
            Tuple of layer names.
        """
        extras = ["_loading"]
        if not self.app._disable_notifications:
            extras.append("_toastrack")
        if not self.app._disable_tooltips:
            extras.append("_tooltips")
        return (*super().layers, *extras)

    def _watch_focused(self):
        self.refresh_bindings()

    def _watch_stack_updates(self):
        self.refresh_bindings()

    def refresh_bindings(self) -> None:
        """Call to request a refresh of bindings."""
        self.bindings_updated_signal.publish(self)

    def _watch_maximized(
        self, previously_maximized: Widget | None, maximized: Widget | None
    ) -> None:
        # The screen gets a `-maximized-view` class if there is a maximized widget
        # The widget gets a `-maximized` class if it is maximized
        self.set_class(maximized is not None, "-maximized-view")
        if previously_maximized is not None:
            previously_maximized.remove_class("-maximized")
        if maximized is not None:
            maximized.add_class("-maximized")

    @property
    def _binding_chain(self) -> list[tuple[DOMNode, BindingsMap]]:
        """Binding chain from this screen."""

        focused = self.focused
        if focused is not None and focused.loading:
            focused = None

        namespace_bindings: list[tuple[DOMNode, BindingsMap]]
        if focused is None:
            namespace_bindings = [
                (self, self._bindings.copy()),
                (self.app, self.app._bindings.copy()),
            ]
        else:
            namespace_bindings = [
                (node, node._bindings.copy()) for node in focused.ancestors_with_self
            ]

        # Filter out bindings that could be captures by widgets (such as Input, TextArea)
        filter_namespaces: list[DOMNode] = []
        for namespace, bindings_map in namespace_bindings:
            for filter_namespace in filter_namespaces:
                check_consume_key = filter_namespace.check_consume_key
                for key in list(bindings_map.key_to_bindings):
                    if check_consume_key(key, key_to_character(key)):
                        # If the widget consumes the key (e.g. like an Input widget),
                        # then remove the key from the bindings map.
                        del bindings_map.key_to_bindings[key]

            filter_namespaces.append(namespace)

        keymap = self.app._keymap
        for namespace, bindings_map in namespace_bindings:
            if keymap:
                result = bindings_map.apply_keymap(keymap)
                if result.clashed_bindings:
                    self.app.handle_bindings_clash(result.clashed_bindings, namespace)

        return namespace_bindings

    @property
    def _modal_binding_chain(self) -> list[tuple[DOMNode, BindingsMap]]:
        """The binding chain, ignoring everything before the last modal."""
        binding_chain = self._binding_chain
        for index, (node, _bindings) in enumerate(binding_chain, 1):
            if node.is_modal:
                return binding_chain[:index]
        return binding_chain

    @property
    def active_bindings(self) -> dict[str, ActiveBinding]:
        """Get currently active bindings for this screen.

        If no widget is focused, then app-level bindings are returned.
        If a widget is focused, then any bindings present in the screen and app are merged and returned.

        This property may be used to inspect current bindings.

        Returns:
            A map of keys to a tuple containing (NAMESPACE, BINDING, ENABLED).
        """
        bindings_map: dict[str, ActiveBinding] = {}
        app = self.app
        for namespace, bindings in self._modal_binding_chain:
            for key, binding in bindings:
                # This will call the nodes `check_action` method.
                action_state = app._check_action_state(binding.action, namespace)
                if action_state is False:
                    # An action_state of False indicates the action is disabled and not shown
                    # Note that None has a different meaning, which is why there is an `is False`
                    # rather than a truthy check.
                    continue

                enabled = bool(action_state)
                if existing_key_and_binding := bindings_map.get(key):
                    # This key has already been bound
                    # Replace priority bindings
                    if (
                        binding.priority
                        and not existing_key_and_binding.binding.priority
                    ):
                        bindings_map[key] = ActiveBinding(
                            namespace, binding, enabled, binding.tooltip
                        )
                else:
                    # New binding
                    bindings_map[key] = ActiveBinding(
                        namespace, binding, enabled, binding.tooltip
                    )

        return bindings_map

    def _arrange(self, size: Size) -> DockArrangeResult:
        """Arrange children.

        Args:
            size: Size of container.

        Returns:
            Widget locations.
        """
        # This is customized over the base class to allow for a widget to be maximized
        cache_key = (size, self._nodes._updates, self.maximized)
        cached_result = self._arrangement_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        allow_in_maximized_view = (
            self.app.ALLOW_IN_MAXIMIZED_VIEW
            if self.ALLOW_IN_MAXIMIZED_VIEW is None
            else self.ALLOW_IN_MAXIMIZED_VIEW
        )

        def get_maximize_widgets(maximized: Widget) -> list[Widget]:
            """Get widgets to display in maximized view.

            Returns:
                A list of widgets.

            """
            # De-duplicate with a set
            widgets = {
                maximized,
                *self.query_children(allow_in_maximized_view),
                *self.query_children(".-textual-system"),
            }
            # Restore order of widgets.
            maximize_widgets = [widget for widget in self.children if widget in widgets]
            # Add the maximized widget, if its not already included
            if maximized not in maximize_widgets:
                maximize_widgets.insert(0, maximized)
            return maximize_widgets

        arrangement = self._arrangement_cache[cache_key] = arrange(
            self,
            (
                get_maximize_widgets(self.maximized)
                if self.maximized is not None
                else self._nodes
            ),
            size,
            self.screen.size,
        )

        return arrangement

    @property
    def is_active(self) -> bool:
        """Is the screen active (i.e. visible and top of the stack)?"""
        try:
            return self.app.screen is self
        except Exception:
            return False

    def render(self) -> RenderableType:
        """Render method inherited from widget, used to render the screen's background.

        Returns:
            Background renderable.
        """
        background = self.styles.background
        try:
            base_screen = visible_screen_stack.get().pop()
        except LookupError:
            base_screen = None

        if base_screen is not None and background.a < 1:
            # If background is translucent, render a background screen
            return BackgroundScreen(base_screen, background)

        if background.is_transparent:
            # If the background is transparent, defer to App.render
            return self.app.render()
        # Render a screen of a solid color.
        return Blank(background)

    def get_offset(self, widget: Widget) -> Offset:
        """Get the absolute offset of a given Widget.

        Args:
            widget: A widget

        Returns:
            The widget's offset relative to the top left of the terminal.
        """
        return self._compositor.get_offset(widget)

    def get_widget_at(self, x: int, y: int) -> tuple[Widget, Region]:
        """Get the widget at a given coordinate.

        Args:
            x: X Coordinate.
            y: Y Coordinate.

        Returns:
            Widget and screen region.

        Raises:
            NoWidget: If there is no widget under the screen coordinate.
        """
        return self._compositor.get_widget_at(x, y)

    def get_widgets_at(self, x: int, y: int) -> Iterable[tuple[Widget, Region]]:
        """Get all widgets under a given coordinate.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            Sequence of (WIDGET, REGION) tuples.
        """
        return self._compositor.get_widgets_at(x, y)

    def get_focusable_widget_at(self, x: int, y: int) -> Widget | None:
        """Get the focusable widget under a given coordinate.

        If the widget directly under the given coordinate is not focusable, then this method will check
        if any of the ancestors are focusable. If no ancestors are focusable, then `None` will be returned.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            A `Widget`, or `None` if there is no focusable widget underneath the coordinate.
        """
        try:
            widget, _region = self.get_widget_at(x, y)
        except NoWidget:
            return None

        if widget.has_class("-textual-system") or widget.loading:
            # Clicking Textual system widgets should not focus anything
            return None

        for node in widget.ancestors_with_self:
            if isinstance(node, Widget) and node.focusable:
                return node
        return None

    def get_style_at(self, x: int, y: int) -> Style:
        """Get the style under a given coordinate.

        Args:
            x: X Coordinate.
            y: Y Coordinate.

        Returns:
            Rich Style object.
        """
        return self._compositor.get_style_at(x, y)

    def find_widget(self, widget: Widget) -> MapGeometry:
        """Get the screen region of a Widget.

        Args:
            widget: A Widget within the composition.

        Returns:
            Region relative to screen.

        Raises:
            NoWidget: If the widget could not be found in this screen.
        """
        return self._compositor.find_widget(widget)

    @property
    def focus_chain(self) -> list[Widget]:
        """A list of widgets that may receive focus, in focus order."""
        # TODO: Calculating a focus chain is moderately expensive.
        # Suspect we can move focus without calculating the entire thing again.

        widgets: list[Widget] = []
        add_widget = widgets.append
        focus_sorter = attrgetter("_focus_sort_key")
        # We traverse the DOM and keep track of where we are at with a node stack.
        # Additionally, we manually keep track of the visibility of the DOM
        # instead of relying on the property `.visible` to save on DOM traversals.
        # node_stack: list[tuple[iterator over node children, node visibility]]
        node_stack: list[tuple[Iterator[Widget], bool]] = [
            (
                iter(sorted(self.displayed_children, key=focus_sorter)),
                self.visible,
            )
        ]
        pop = node_stack.pop
        push = node_stack.append

        while node_stack:
            children_iterator, parent_visibility = node_stack[-1]
            node = next(children_iterator, None)
            if node is None:
                pop()
            else:
                if node._check_disabled():
                    continue
                node_styles_visibility = node.styles.get_rule("visibility")
                node_is_visible = (
                    node_styles_visibility != "hidden"
                    if node_styles_visibility
                    else parent_visibility  # Inherit visibility if the style is unset.
                )
                if node.is_container and node.allow_focus_children():
                    sorted_displayed_children = sorted(
                        node.displayed_children, key=focus_sorter
                    )
                    push((iter(sorted_displayed_children), node_is_visible))
                # Same check as `if node.focusable`, but we cached inherited visibility
                # and we also skipped disabled nodes altogether.
                if node_is_visible and node.allow_focus():
                    add_widget(node)

        return widgets

    def _move_focus(
        self, direction: int = 0, selector: str | type[QueryType] = "*"
    ) -> Widget | None:
        """Move the focus in the given direction.

        If no widget is currently focused, this will focus the first focusable widget.
        If no focusable widget matches the given CSS selector, focus is set to `None`.

        Args:
            direction: 1 to move forward, -1 to move backward, or
                0 to keep the current focus.
            selector: CSS selector to filter
                what nodes can be focused.

        Returns:
            Newly focused widget, or None for no focus. If the return
                is not `None`, then it is guaranteed that the widget returned matches
                the CSS selectors given in the argument.
        """

        if not isinstance(selector, str):
            selector = selector.__name__
        selector_set = parse_selectors(selector)
        focus_chain = self.focus_chain

        # If a widget is maximized we want to limit the focus chain to the visible widgets
        if self.maximized is not None:
            focusable = set(self.maximized.walk_children(with_self=True))
            focus_chain = [widget for widget in focus_chain if widget in focusable]

        filtered_focus_chain = (
            node for node in focus_chain if match(selector_set, node)
        )

        if not focus_chain:
            # Nothing focusable, so nothing to do
            return self.focused
        if self.focused is None:
            # Nothing currently focused, so focus the first one.
            to_focus = next(filtered_focus_chain, None)
            self.set_focus(to_focus)
            return self.focused

        # Ensure focus will be in a node that matches the selectors.
        if not direction and not match(selector_set, self.focused):
            direction = 1

        try:
            # Find the index of the currently focused widget
            current_index = focus_chain.index(self.focused)
        except ValueError:
            # Focused widget was removed in the interim, start again
            self.set_focus(next(filtered_focus_chain, None))
        else:
            # Only move the focus if we are currently showing the focus
            if direction:
                to_focus = None
                chain_length = len(focus_chain)
                for step in range(1, len(focus_chain) + 1):
                    node = focus_chain[
                        (current_index + direction * step) % chain_length
                    ]
                    if match(selector_set, node):
                        to_focus = node
                        break
                self.set_focus(to_focus)

        return self.focused

    def focus_next(self, selector: str | type[QueryType] = "*") -> Widget | None:
        """Focus the next widget, optionally filtered by a CSS selector.

        If no widget is currently focused, this will focus the first focusable widget.
        If no focusable widget matches the given CSS selector, focus is set to `None`.

        Args:
            selector: CSS selector to filter
                what nodes can be focused.

        Returns:
            Newly focused widget, or None for no focus. If the return
                is not `None`, then it is guaranteed that the widget returned matches
                the CSS selectors given in the argument.
        """
        return self._move_focus(1, selector)

    def focus_previous(self, selector: str | type[QueryType] = "*") -> Widget | None:
        """Focus the previous widget, optionally filtered by a CSS selector.

        If no widget is currently focused, this will focus the first focusable widget.
        If no focusable widget matches the given CSS selector, focus is set to `None`.

        Args:
            selector: CSS selector to filter
                what nodes can be focused.

        Returns:
            Newly focused widget, or None for no focus. If the return
                is not `None`, then it is guaranteed that the widget returned matches
                the CSS selectors given in the argument.
        """
        return self._move_focus(-1, selector)

    def maximize(self, widget: Widget, container: bool = True) -> bool:
        """Maximize a widget, so it fills the screen.

        Args:
            widget: Widget to maximize.
            container: If one of the widgets ancestors is a maximizeable widget, maximize that instead.

        Returns:
            `True` if the widget was maximized, otherwise `False`.
        """
        if widget.allow_maximize:
            if container:
                # If we want to maximize the container, look up the dom to find a suitable widget
                for maximize_widget in widget.ancestors:
                    if not isinstance(maximize_widget, Widget):
                        break
                    if maximize_widget.allow_maximize:
                        self.maximized = maximize_widget
                        return True

            self.maximized = widget
            return True
        return False

    def minimize(self) -> None:
        """Restore any maximized widget to normal state."""
        self.maximized = None
        if self.focused is not None:
            self.call_after_refresh(
                self.scroll_to_widget, self.focused, animate=False, center=True
            )

    def action_maximize(self) -> None:
        """Action to maximize the currently focused widget."""
        if self.focused is not None:
            self.maximize(self.focused)

    def action_minimize(self) -> None:
        """Action to minimize the currently maximized widget."""
        self.minimize()

    def action_blur(self) -> None:
        """Action to remove focus (if set)."""
        self.set_focus(None)

    def _reset_focus(
        self, widget: Widget, avoiding: list[Widget] | None = None
    ) -> None:
        """Reset the focus when a widget is removed

        Args:
            widget: A widget that is removed.
            avoiding: Optional list of nodes to avoid.
        """

        avoiding = avoiding or []

        # Make this a NOP if we're being asked to deal with a widget that
        # isn't actually the currently-focused widget.
        if self.focused is not widget:
            return

        # Grab the list of widgets that we can set focus to.
        focusable_widgets = self.focus_chain
        if not focusable_widgets:
            # If there's nothing to focus... give up now.
            self.set_focus(None)
            return

        try:
            # Find the location of the widget we're taking focus from, in
            # the focus chain.
            widget_index = focusable_widgets.index(widget)
        except ValueError:
            # widget is not in focusable widgets
            # It may have been made invisible
            # Move to a sibling if possible
            for sibling in widget.visible_siblings:
                if sibling not in avoiding and sibling.focusable:
                    self.set_focus(sibling)
                    break
            else:
                self.set_focus(None)
            return

        # Now go looking for something before it, that isn't about to be
        # removed, and which can receive focus, and go focus that.
        chosen: Widget | None = None
        for candidate in reversed(
            focusable_widgets[widget_index + 1 :] + focusable_widgets[:widget_index]
        ):
            if candidate not in avoiding:
                chosen = candidate
                break

        # Go with what was found.
        self.set_focus(chosen)

    def _update_focus_styles(
        self, focused: Widget | None = None, blurred: Widget | None = None
    ) -> None:
        """Update CSS for focus changes.

        Args:
            focused: The widget that was focused.
            blurred: The widget that was blurred.
        """
        widgets: set[DOMNode] = set()

        if focused is not None:
            for widget in reversed(focused.ancestors_with_self):
                if widget._has_focus_within:
                    widgets.update(widget.walk_children(with_self=True))
                    break
        if blurred is not None:
            for widget in reversed(blurred.ancestors_with_self):
                if widget._has_focus_within:
                    widgets.update(widget.walk_children(with_self=True))
                    break
        if widgets:
            self.app.stylesheet.update_nodes(
                [widget for widget in widgets if widget._has_focus_within], animate=True
            )

    def set_focus(
        self,
        widget: Widget | None,
        scroll_visible: bool = True,
        from_app_focus: bool = False,
    ) -> None:
        """Focus (or un-focus) a widget. A focused widget will receive key events first.

        Args:
            widget: Widget to focus, or None to un-focus.
            scroll_visible: Scroll widget in to view.
            from_app_focus: True if this focus is due to the app itself having regained
                focus. False if the focus is being set because a widget within the app
                regained focus.
        """
        if widget is self.focused:
            # Widget is already focused
            return

        focused: Widget | None = None
        blurred: Widget | None = None

        if widget is None:
            # No focus, so blur currently focused widget if it exists
            if self.focused is not None:
                self.focused.post_message(events.Blur())
                blurred = self.focused
                self.focused = None
            self.log.debug("focus was removed")
        elif widget.focusable:
            if self.focused != widget:
                if self.focused is not None:
                    # Blur currently focused widget
                    self.focused.post_message(events.Blur())
                    blurred = self.focused
                # Change focus
                self.focused = widget
                # Send focus event
                widget.post_message(events.Focus(from_app_focus=from_app_focus))
                focused = widget

                if scroll_visible:

                    def scroll_to_center(widget: Widget) -> None:
                        """Scroll to center (after a refresh)."""
                        if self.focused is widget and not self.can_view_entire(widget):
                            self.scroll_to_center(widget, origin_visible=True)

                    self.call_later(scroll_to_center, widget)

                self.log.debug(widget, "was focused")

        self._update_focus_styles(focused, blurred)
        self.call_after_refresh(self.refresh_bindings)

    def _extend_compose(self, widgets: list[Widget]) -> None:
        """Insert Textual's own internal widgets.

        Args:
            widgets: The list of widgets to be composed.

        This method adds the tooltip, if required, and also adds the
        container for `Toast`s.
        """
        if not self.app._disable_tooltips:
            widgets.insert(0, Tooltip(id="textual-tooltip"))
        if not self.app._disable_notifications:
            widgets.insert(0, ToastRack(id="textual-toastrack"))

    def _on_mount(self, event: events.Mount) -> None:
        """Set up the tooltip-clearing signal when we mount."""
        self.screen_layout_refresh_signal.subscribe(
            self, self._maybe_clear_tooltip, immediate=True
        )

    async def _on_idle(self, event: events.Idle) -> None:
        # Check for any widgets marked as 'dirty' (needs a repaint)
        event.prevent_default()
        if not self.app._batch_count and self.is_current:
            if (
                self._layout_required
                or self._scroll_required
                or self._repaint_required
                or self._recompose_required
                or self._dirty_widgets
            ):
                self._update_timer.resume()
                return

        await self._invoke_and_clear_callbacks()

    def _compositor_refresh(self) -> None:
        """Perform a compositor refresh."""

        app = self.app

        if app.is_inline:
            if self is app.screen:
                inline_height = app._get_inline_height()
                clear = (
                    app._previous_inline_height is not None
                    and inline_height < app._previous_inline_height
                )
                app._display(
                    self,
                    self._compositor.render_inline(
                        app.size.with_height(inline_height),
                        screen_stack=app._background_screens,
                        clear=clear,
                    ),
                )
                app._previous_inline_height = inline_height
                self._dirty_widgets.clear()
                self._compositor._dirty_regions.clear()
            elif (
                self in self.app._background_screens and self._compositor._dirty_regions
            ):
                app.screen.refresh(*self._compositor._dirty_regions)
                self._compositor._dirty_regions.clear()
                self._dirty_widgets.clear()

        else:
            if self is app.screen:
                # Top screen
                update = self._compositor.render_update(
                    screen_stack=app._background_screens
                )
                app._display(self, update)
                self._dirty_widgets.clear()
            elif (
                self in self.app._background_screens and self._compositor._dirty_regions
            ):
                self._set_dirty(*self._compositor._dirty_regions)
                app.screen.refresh(*self._compositor._dirty_regions)
                self._repaint_required = True
                self._compositor._dirty_regions.clear()
                self._dirty_widgets.clear()
        app._update_mouse_over(self)

    def _on_timer_update(self) -> None:
        """Called by the _update_timer."""
        self._update_timer.pause()
        if self.is_current and not self.app._batch_count:
            if self._layout_required:
                self._refresh_layout(scroll=self._scroll_required)
                self._layout_required = False
                self._dirty_widgets.clear()
            elif self._scroll_required:
                self._refresh_layout(scroll=True)
            self._scroll_required = False

            if self._repaint_required:
                self._dirty_widgets.clear()
                self._dirty_widgets.add(self)
                self._repaint_required = False

            if self._dirty_widgets:
                self._compositor.update_widgets(self._dirty_widgets)
                self._compositor_refresh()

            if self._recompose_required:
                self._recompose_required = False
                self.call_next(self.recompose)

        if self._callbacks:
            self.call_next(self._invoke_and_clear_callbacks)

    async def _invoke_and_clear_callbacks(self) -> None:
        """If there are scheduled callbacks to run, call them and clear
        the callback queue."""
        if self._callbacks:
            callbacks = self._callbacks[:]
            self._callbacks.clear()
            for callback, message_pump in callbacks:
                with message_pump._context():
                    await invoke(callback)

    def _invoke_later(self, callback: CallbackType, sender: MessagePump) -> None:
        """Enqueue a callback to be invoked after the screen is repainted.

        Args:
            callback: A callback.
            sender: The sender (active message pump) of the callback.
        """

        self._callbacks.append((callback, sender))
        self.check_idle()

    def _push_result_callback(
        self,
        requester: MessagePump,
        callback: ScreenResultCallbackType[ScreenResultType] | None,
        future: asyncio.Future[ScreenResultType | None] | None = None,
    ) -> None:
        """Add a result callback to the screen.

        Args:
            requester: The object requesting the callback.
            callback: The callback.
            future: A Future to hold the result.
        """
        self._result_callbacks.append(
            ResultCallback[Optional[ScreenResultType]](requester, callback, future)
        )

    async def _message_loop_exit(self) -> None:
        await super()._message_loop_exit()
        self._compositor.clear()
        self._dirty_widgets.clear()
        self._dirty_regions.clear()
        self._arrangement_cache.clear()
        self.screen_layout_refresh_signal.unsubscribe(self)
        self._nodes._clear()
        self._task = None

    def _pop_result_callback(self) -> None:
        """Remove the latest result callback from the stack."""
        self._result_callbacks.pop()

    def _refresh_layout(self, size: Size | None = None, scroll: bool = False) -> None:
        """Refresh the layout (can change size and positions of widgets)."""
        size = self.outer_size if size is None else size
        if self.app.is_inline:
            size = size.with_height(self.app._get_inline_height())
        if not size:
            return
        self._compositor.update_widgets(self._dirty_widgets)
        self._update_timer.pause()
        ResizeEvent = events.Resize

        try:
            if scroll:
                exposed_widgets = self._compositor.reflow_visible(self, size)
                if exposed_widgets:
                    layers = self._compositor.layers
                    for widget, (
                        region,
                        _order,
                        _clip,
                        virtual_size,
                        container_size,
                        _,
                        _,
                    ) in layers:
                        if widget in exposed_widgets:
                            if widget._size_updated(
                                region.size, virtual_size, container_size, layout=False
                            ):
                                widget.post_message(
                                    ResizeEvent(
                                        region.size, virtual_size, container_size
                                    )
                                )

            else:
                hidden, shown, resized = self._compositor.reflow(self, size)
                Hide = events.Hide
                Show = events.Show

                for widget in hidden:
                    widget.post_message(Hide())

                # We want to send a resize event to widgets that were just added or change since last layout
                send_resize = shown | resized

                layers = self._compositor.layers
                for widget, (
                    region,
                    _order,
                    _clip,
                    virtual_size,
                    container_size,
                    _,
                    _,
                ) in layers:
                    widget._size_updated(region.size, virtual_size, container_size)
                    if widget in send_resize:
                        widget.post_message(
                            ResizeEvent(region.size, virtual_size, container_size)
                        )

                for widget in shown:
                    widget.post_message(Show())

        except Exception as error:
            self.app._handle_exception(error)
            return
        if self.is_current:
            self._compositor_refresh()

        if self.app._dom_ready:
            self.screen_layout_refresh_signal.publish(self.screen)
        else:
            self.app.post_message(events.Ready())
            self.app._dom_ready = True

    async def _on_update(self, message: messages.Update) -> None:
        message.stop()
        message.prevent_default()
        widget = message.widget
        assert isinstance(widget, Widget)

        if self in self._compositor:
            self._dirty_widgets.add(widget)
            self.check_idle()

    async def _on_layout(self, message: messages.Layout) -> None:
        message.stop()
        message.prevent_default()
        self._layout_required = True
        self.check_idle()

    async def _on_update_scroll(self, message: messages.UpdateScroll) -> None:
        message.stop()
        message.prevent_default()
        self._scroll_required = True
        self.check_idle()

    def _get_inline_height(self, size: Size) -> int:
        """Get the inline height (number of lines to display when running inline mode).

        Args:
            size: Size of the terminal

        Returns:
            Height for inline mode.
        """
        height_scalar = self.styles.height
        if height_scalar is None or height_scalar.is_auto:
            inline_height = self.get_content_height(size, size, size.width)
        else:
            inline_height = int(height_scalar.resolve(size, size))
        inline_height += self.styles.gutter.height
        min_height = self.styles.min_height
        max_height = self.styles.max_height
        if min_height is not None:
            inline_height = max(inline_height, int(min_height.resolve(size, size)))
        if max_height is not None:
            inline_height = min(inline_height, int(max_height.resolve(size, size)))
        inline_height = min(self.app.size.height, inline_height)
        return inline_height

    def _screen_resized(self, size: Size):
        """Called by App when the screen is resized."""
        if self.stack_updates:
            self._refresh_layout(size)

    def _on_screen_resume(self) -> None:
        """Screen has resumed."""
        if self.app.SUSPENDED_SCREEN_CLASS:
            self.remove_class(self.app.SUSPENDED_SCREEN_CLASS)
        self.stack_updates += 1
        self.app._refresh_notifications()
        size = self.app.size

        self._refresh_layout(size)
        self.refresh()
        # Only auto-focus when the app has focus (textual-web only)
        if self.app.app_focus:
            auto_focus = (
                self.app.AUTO_FOCUS if self.AUTO_FOCUS is None else self.AUTO_FOCUS
            )
            if auto_focus and self.focused is None:
                for widget in self.query(auto_focus):
                    if widget.focusable:
                        self.set_focus(widget)
                        break

    def _on_screen_suspend(self) -> None:
        """Screen has suspended."""
        if self.app.SUSPENDED_SCREEN_CLASS:
            self.add_class(self.app.SUSPENDED_SCREEN_CLASS)
        self.app._set_mouse_over(None)
        self._clear_tooltip()
        self.stack_updates += 1

    async def _on_resize(self, event: events.Resize) -> None:
        event.stop()
        size = self.app.size
        if self.size == size:
            return

        self._screen_resized(size)
        for screen in self.app._background_screens:
            screen._screen_resized(size)

    def _update_tooltip(self, widget: Widget) -> None:
        """Update the content of the tooltip."""
        try:
            tooltip = self.get_child_by_type(Tooltip)
        except NoMatches:
            pass
        else:
            if tooltip.display and self._tooltip_widget is widget:
                self._handle_tooltip_timer(widget)

    def _clear_tooltip(self) -> None:
        """Unconditionally clear any existing tooltip."""
        try:
            tooltip = self.get_child_by_type(Tooltip)
        except NoMatches:
            return
        if tooltip.display:
            if self._tooltip_timer is not None:
                self._tooltip_timer.stop()
            tooltip.display = False

    def _maybe_clear_tooltip(self, _) -> None:
        """Check if the widget under the mouse cursor still pertains to the tooltip.

        If they differ, the tooltip will be removed.
        """
        # If there's a widget associated with the tooltip at all...
        if self._tooltip_widget is not None:
            # ...look at what's currently under the mouse.
            try:
                under_mouse, _ = self.get_widget_at(*self.app.mouse_position)
            except NoWidget:
                pass
            else:
                # If it's not the same widget...
                if under_mouse is not self._tooltip_widget:
                    # ...clear the tooltip.
                    self._clear_tooltip()

    def _handle_tooltip_timer(self, widget: Widget) -> None:
        """Called by a timer from _handle_mouse_move to update the tooltip.

        Args:
            widget: The widget under the mouse.
        """

        try:
            tooltip = self.get_child_by_type(Tooltip)
        except NoMatches:
            pass
        else:
            tooltip_content: RenderableType | None = None
            for node in widget.ancestors_with_self:
                if not isinstance(node, Widget):
                    break
                if node.tooltip is not None:
                    tooltip_content = node.tooltip
                    break

            if tooltip_content is None:
                tooltip.display = False
            else:
                tooltip.display = True
                tooltip.absolute_offset = self.app.mouse_position
                tooltip.update(tooltip_content)

    def _handle_mouse_move(self, event: events.MouseMove) -> None:
        try:
            if self.app.mouse_captured:
                widget = self.app.mouse_captured
                region = self.find_widget(widget).region
            else:
                widget, region = self.get_widget_at(event.x, event.y)
        except errors.NoWidget:
            self.app._set_mouse_over(None)
            if self._tooltip_timer is not None:
                self._tooltip_timer.stop()
            if not self.app._disable_tooltips:
                try:
                    self.get_child_by_type(Tooltip).display = False
                except NoMatches:
                    pass

        else:
            self.app._set_mouse_over(widget)
            widget.hover_style = event.style
            if widget is self:
                self.post_message(event)
            else:
                mouse_event = self._translate_mouse_move_event(event, widget, region)
                mouse_event._set_forwarded()
                widget._forward_event(mouse_event)

            if not self.app._disable_tooltips:
                try:
                    tooltip = self.get_child_by_type(Tooltip)
                except NoMatches:
                    pass
                else:
                    if self._tooltip_widget != widget or not tooltip.display:
                        self._tooltip_widget = widget
                        if self._tooltip_timer is not None:
                            self._tooltip_timer.stop()

                        self._tooltip_timer = self.set_timer(
                            self.app.TOOLTIP_DELAY,
                            partial(self._handle_tooltip_timer, widget),
                            name="tooltip-timer",
                        )
                    else:
                        tooltip.display = False

    @staticmethod
    def _translate_mouse_move_event(
        event: events.MouseMove, widget: Widget, region: Region
    ) -> events.MouseMove:
        """
        Returns a mouse move event whose relative coordinates are translated to
        the origin of the specified region.
        """
        return events.MouseMove(
            widget,
            event.x - region.x,
            event.y - region.y,
            event.delta_x,
            event.delta_y,
            event.button,
            event.shift,
            event.meta,
            event.ctrl,
            screen_x=event.screen_x,
            screen_y=event.screen_y,
            style=event.style,
        )

    def _forward_event(self, event: events.Event) -> None:
        if event.is_forwarded:
            return
        event._set_forwarded()

        if isinstance(event, (events.Enter, events.Leave)):
            self.post_message(event)

        elif isinstance(event, events.MouseMove):
            event.style = self.get_style_at(event.screen_x, event.screen_y)
            self._handle_mouse_move(event)

        elif isinstance(event, events.MouseEvent):
            try:
                if self.app.mouse_captured:
                    widget = self.app.mouse_captured
                    region = self.find_widget(widget).region
                else:
                    widget, region = self.get_widget_at(event.x, event.y)
            except errors.NoWidget:
                self.set_focus(None)
            else:
                if isinstance(event, events.MouseDown):
                    focusable_widget = self.get_focusable_widget_at(event.x, event.y)
                    if focusable_widget:
                        self.set_focus(focusable_widget, scroll_visible=False)
                event.style = self.get_style_at(event.screen_x, event.screen_y)
                if widget.loading:
                    return
                if widget is self:
                    event._set_forwarded()
                    self.post_message(event)
                else:
                    widget._forward_event(event._apply_offset(-region.x, -region.y))

        else:
            self.post_message(event)

    def dismiss(self, result: ScreenResultType | None = None) -> AwaitComplete:
        """Dismiss the screen, optionally with a result.

        Any callback provided in [push_screen][textual.app.App.push_screen] will be invoked with the supplied result.

        Only the active screen may be dismissed. This method will produce a warning in the logs if
        called on an inactive screen (but otherwise have no effect).

        !!! warning

            Textual will raise a [`ScreenError`][textual.app.ScreenError] if you await the return value from a
            message handler on the Screen being dismissed. If you want to dismiss the current screen, you can
            call `self.dismiss()` _without_ awaiting.

        Args:
            result: The optional result to be passed to the result callback.

        """
        _rich_traceback_omit = True
        if not self.is_active:
            self.log.warning("Can't dismiss inactive screen")
            return AwaitComplete()
        if self._result_callbacks:
            callback = self._result_callbacks[-1]
            callback(result)
        await_pop = self.app.pop_screen()

        def pre_await() -> None:
            """Called by the AwaitComplete object."""
            _rich_traceback_omit = True
            if active_message_pump.get() is self:
                from textual.app import ScreenError

                raise ScreenError(
                    "Can't await screen.dismiss() from the screen's message handler; try removing the await keyword."
                )

        await_pop.set_pre_await_callback(pre_await)

        return await_pop

    def pop_until_active(self) -> None:
        """Pop any screens on top of this one, until this screen is active.

        Raises:
            ScreenError: If this screen is not in the current mode.

        """
        from textual.app import ScreenError

        try:
            self.app._pop_to_screen(self)
        except ScreenError:
            # More specific error message
            raise ScreenError(
                f"Can't make {self} active as it is not in the current stack."
            ) from None

    async def action_dismiss(self, result: ScreenResultType | None = None) -> None:
        """A wrapper around [`dismiss`][textual.screen.Screen.dismiss] that can be called as an action.

        Args:
            result: The optional result to be passed to the result callback.
        """
        await self._flush_next_callbacks()
        self.dismiss(result)

    def can_view_entire(self, widget: Widget) -> bool:
        """Check if a given widget is fully within the current screen.

        Note: This doesn't necessarily equate to a widget being visible.
        There are other reasons why a widget may not be visible.

        Args:
            widget: A widget.

        Returns:
            `True` if the entire widget is in view, `False` if it is partially visible or not in view.
        """
        if widget not in self._compositor.visible_widgets:
            return False
        # If the widget is one that overlays the screen...
        if widget.styles.overlay == "screen":
            # ...simply check if it's within the screen's region.
            return widget.region in self.region
        # Failing that fall back to normal checking.
        return super().can_view_entire(widget)

    def can_view_partial(self, widget: Widget) -> bool:
        """Check if a given widget is at least partially within the current view.

        Args:
            widget: A widget.

        Returns:
            `True` if the any part of the widget is in view, `False` if it is completely outside of the screen.
        """
        if widget not in self._compositor.visible_widgets:
            return False
        # If the widget is one that overlays the screen...
        if widget.styles.overlay == "screen":
            # ...simply check if it's within the screen's region.
            return widget.region in self.region
        # Failing that fall back to normal checking.
        return super().can_view_partial(widget)

    def validate_title(self, title: Any) -> str | None:
        """Ensure the title is a string or `None`."""
        return None if title is None else str(title)

    def validate_sub_title(self, sub_title: Any) -> str | None:
        """Ensure the sub-title is a string or `None`."""
        return None if sub_title is None else str(sub_title)


@rich.repr.auto
class ModalScreen(Screen[ScreenResultType]):
    """A screen with bindings that take precedence over the App's key bindings.

    The default styling of a modal screen will dim the screen underneath.
    """

    DEFAULT_CSS = """
    ModalScreen {
        layout: vertical;
        overflow-y: auto;
        background: $background 60%;
        &:ansi {
            background: transparent;                   
        }
    }
    """

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._modal = True


class SystemModalScreen(ModalScreen[ScreenResultType], inherit_css=False):
    """A variant of `ModalScreen` for internal use.

    This version of `ModalScreen` allows us to build system-level screens;
    the type being used to indicate that the screen should be isolated from
    the main application.

    Note:
        This screen is set to *not* inherit CSS.
    """
