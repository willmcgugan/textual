"""
The module contains `DOMNode`, the base class for any object within the Textual Document Object Model,
which includes all Widgets, Screens, and Apps.

"""

from __future__ import annotations

import re
import threading
from functools import lru_cache, partial
from inspect import getfile
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Iterable,
    Sequence,
    Type,
    TypeVar,
    cast,
    overload,
)

import rich.repr
from rich.highlighter import ReprHighlighter
from rich.style import Style
from rich.text import Text
from rich.tree import Tree

from ._context import NoActiveAppError, active_message_pump
from ._node_list import NodeList
from ._types import WatchCallbackType
from .binding import Binding, BindingType, _Bindings
from .color import BLACK, WHITE, Color
from .css._error_tools import friendly_list
from .css.constants import VALID_DISPLAY, VALID_VISIBILITY
from .css.errors import DeclarationError, StyleValueError
from .css.parse import parse_declarations
from .css.styles import RenderStyles, Styles
from .css.tokenize import IDENTIFIER
from .message_pump import MessagePump
from .reactive import Reactive, ReactiveError, _watch
from .timer import Timer
from .walk import walk_breadth_first, walk_depth_first
from .worker_manager import WorkerManager

if TYPE_CHECKING:
    from typing_extensions import Self, TypeAlias
    from _typeshed import SupportsRichComparison

    from rich.console import RenderableType
    from .app import App
    from .css.query import DOMQuery, QueryType
    from .css.types import CSSLocation
    from .message import Message
    from .screen import Screen
    from .widget import Widget
    from .worker import Worker, WorkType, ResultType

    # Unused & ignored imports are needed for the docs to link to these objects:
    from .css.query import NoMatches, TooManyMatches, WrongType  # type: ignore  # noqa: F401

from typing_extensions import Literal

_re_identifier = re.compile(IDENTIFIER)


WalkMethod: TypeAlias = Literal["depth", "breadth"]
"""Valid walking methods for the [`DOMNode.walk_children` method][textual.dom.DOMNode.walk_children]."""


ReactiveType = TypeVar("ReactiveType")


class BadIdentifier(Exception):
    """Exception raised if you supply a `id` attribute or class name in the wrong format."""


def check_identifiers(description: str, *names: str) -> None:
    """Validate identifier and raise an error if it fails.

    Args:
        description: Description of where identifier is used for error message.
        *names: Identifiers to check.
    """
    match = _re_identifier.fullmatch
    for name in names:
        if match(name) is None:
            raise BadIdentifier(
                f"{name!r} is an invalid {description}; "
                "identifiers must contain only letters, numbers, underscores, or hyphens, and must not begin with a number."
            )


class DOMError(Exception):
    """Base exception class for errors relating to the DOM."""


class NoScreen(DOMError):
    """Raised when the node has no associated screen."""


class _ClassesDescriptor:
    """A descriptor to manage the `classes` property."""

    def __get__(
        self, obj: DOMNode, objtype: type[DOMNode] | None = None
    ) -> frozenset[str]:
        """A frozenset of the current classes on the widget."""
        return frozenset(obj._classes)

    def __set__(self, obj: DOMNode, classes: str | Iterable[str]) -> None:
        """Replaces classes entirely."""
        if isinstance(classes, str):
            class_names = set(classes.split())
        else:
            class_names = set(classes)
        check_identifiers("class name", *class_names)
        obj._classes = class_names
        obj._update_styles()


@rich.repr.auto
class DOMNode(MessagePump):
    """The base class for object that can be in the Textual DOM (App and Widget)"""

    # CSS defaults
    DEFAULT_CSS: ClassVar[str] = ""

    # Default classes argument if not supplied
    DEFAULT_CLASSES: str = ""

    # Virtual DOM nodes
    COMPONENT_CLASSES: ClassVar[set[str]] = set()

    # Mapping of key bindings
    BINDINGS: ClassVar[list[BindingType]] = []

    # Indicates if the CSS should be automatically scoped
    SCOPED_CSS: ClassVar[bool] = True
    """Should default css be limited to the widget type?"""

    # True if this node inherits the CSS from the base class.
    _inherit_css: ClassVar[bool] = True

    # True if this node inherits the component classes from the base class.
    _inherit_component_classes: ClassVar[bool] = True

    # True to inherit bindings from base class
    _inherit_bindings: ClassVar[bool] = True

    # List of names of base classes that inherit CSS
    _css_type_names: ClassVar[frozenset[str]] = frozenset()

    # Name of the widget in CSS
    _css_type_name: str = ""

    # Generated list of bindings
    _merged_bindings: ClassVar[_Bindings | None] = None

    _reactives: ClassVar[dict[str, Reactive]]

    _decorated_handlers: dict[type[Message], list[tuple[Callable, str | None]]]

    # Names of potential computed reactives
    _computes: ClassVar[frozenset[str]]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        self._classes: set[str] = set()
        self._name = name
        self._id = None
        if id is not None:
            self.id = id

        _classes = classes.split() if classes else []
        check_identifiers("class name", *_classes)
        self._classes.update(_classes)

        self._nodes: NodeList = NodeList()
        self._css_styles: Styles = Styles(self)
        self._inline_styles: Styles = Styles(self)
        self.styles: RenderStyles = RenderStyles(
            self, self._css_styles, self._inline_styles
        )
        # A mapping of class names to Styles set in COMPONENT_CLASSES
        self._component_styles: dict[str, RenderStyles] = {}

        self._auto_refresh: float | None = None
        self._auto_refresh_timer: Timer | None = None
        self._css_types = {cls.__name__ for cls in self._css_bases(self.__class__)}
        self._bindings = (
            _Bindings()
            if self._merged_bindings is None
            else self._merged_bindings.copy()
        )
        self._has_hover_style: bool = False
        self._has_focus_within: bool = False
        self._reactive_connect: (
            dict[str, tuple[MessagePump, Reactive | object]] | None
        ) = None

        self._pruning = False

        super().__init__()

    def set_reactive(
        self, reactive: Reactive[ReactiveType], value: ReactiveType
    ) -> None:
        """Sets a reactive value *without* invoking validators or watchers.

        Example:
            ```python
            self.set_reactive(App.dark_mode, True)
            ```

        Args:
            reactive: A reactive property (use the class scope syntax, i.e. `MyClass.my_reactive`).
            value: New value of reactive.

        Raises:
            AttributeError: If the first argument is not a reactive.
        """
        if not isinstance(reactive, Reactive):
            raise TypeError(
                "A Reactive class is required; for example: MyApp.dark_mode"
            )
        if reactive.name not in self._reactives:
            raise AttributeError(
                "No reactive called {name!r}; Have you called super().__init__(...) in the {self.__class__.__name__} constructor?"
            )
        setattr(self, f"_reactive_{reactive.name}", value)

    def mutate_reactive(self, reactive: Reactive[ReactiveType]) -> None:
        """Force an update to a mutable reactive.

        Example:
            ```python
            self.reactive_name_list.append("Jessica")
            self.mutate_reactive(MyClass.reactive_name_list)
            ```

        Textual will automatically detect when a reactive is set to a new value, but it is unable
        to detect if a value is _mutated_ (such as updating a list, dict, or attribute of an object).
        If you do wish to use a collection or other mutable object in a reactive, then you can call
        this method after your reactive is updated. This will ensure that all the reactive _superpowers_
        work.

        Args:
            reactive: A reactive property (use the class scope syntax, i.e. `MyClass.my_reactive`).
        """

        internal_name = f"_reactive_{reactive.name}"
        value = getattr(self, internal_name)
        reactive._set(self, value, always=True)

    def data_bind(
        self,
        *reactives: Reactive[Any],
        **bind_vars: Reactive[Any] | object,
    ) -> Self:
        """Bind reactive data so that changes to a reactive automatically change the reactive on another widget.

        Reactives may be given as positional arguments or keyword arguments.
        See the [guide on data binding](/guide/reactivity#data-binding).

        Example:
            ```python
            def compose(self) -> ComposeResult:
                yield WorldClock("Europe/London").data_bind(WorldClockApp.time)
                yield WorldClock("Europe/Paris").data_bind(WorldClockApp.time)
                yield WorldClock("Asia/Tokyo").data_bind(WorldClockApp.time)
            ```

        Raises:
            ReactiveError: If the data wasn't bound.

        Returns:
            Self.
        """
        _rich_traceback_omit = True

        parent = active_message_pump.get()

        if self._reactive_connect is None:
            self._reactive_connect = {}
        bind_vars = {**{reactive.name: reactive for reactive in reactives}, **bind_vars}
        for name, reactive in bind_vars.items():
            if name not in self._reactives:
                raise ReactiveError(
                    f"Unable to bind non-reactive attribute {name!r} on {self}"
                )
            if isinstance(reactive, Reactive) and not isinstance(
                parent, reactive.owner
            ):
                raise ReactiveError(
                    f"Unable to bind data; {reactive.owner.__name__} is not defined on {parent.__class__.__name__}."
                )
            self._reactive_connect[name] = (parent, reactive)
        if self._is_mounted:
            self._initialize_data_bind()
        else:
            self.call_later(self._initialize_data_bind)
        return self

    def _initialize_data_bind(self) -> None:
        """initialize a data binding.

        Args:
            compose_parent: The node doing the binding.
        """
        if not self._reactive_connect:
            return
        for variable_name, (compose_parent, reactive) in self._reactive_connect.items():

            def make_setter(variable_name: str) -> Callable[[object], None]:
                """Make a setter for the given variable name.

                Args:
                    variable_name: Name of variable being set.

                Returns:
                    A callable which takes the value to set.
                """

                def setter(value: object) -> None:
                    """Set bound data."""
                    _rich_traceback_omit = True
                    Reactive._initialize_object(self)
                    setattr(self, variable_name, value)

                return setter

            assert isinstance(compose_parent, DOMNode)
            setter = make_setter(variable_name)
            if isinstance(reactive, Reactive):
                self.watch(
                    compose_parent,
                    reactive.name,
                    setter,
                    init=True,
                )
            else:
                self.call_later(partial(setter, reactive))
        self._reactive_connect = None

    def compose_add_child(self, widget: Widget) -> None:
        """Add a node to children.

        This is used by the compose process when it adds children.
        There is no need to use it directly, but you may want to override it in a subclass
        if you want children to be attached to a different node.

        Args:
            widget: A Widget to add.
        """
        self._nodes._append(widget)

    @property
    def children(self) -> Sequence["Widget"]:
        """A view on to the children.

        Returns:
            The node's children.
        """
        return self._nodes

    def sort_children(
        self,
        *,
        key: Callable[[Widget], SupportsRichComparison] | None = None,
        reverse: bool = False,
    ) -> None:
        """Sort child widgets with an optional key function.

        If `key` is not provided then widgets will be sorted in the order they are constructed.

        Example:
            ```python
            # Sort widgets by name
            screen.sort_children(key=lambda widget: widget.name or "")
            ```

        Args:
            key: A callable which accepts a widget and returns something that can be sorted,
                or `None` to sort without a key function.
            reverse: Sort in descending order.
        """
        self._nodes._sort(key=key, reverse=reverse)
        self.refresh(layout=True)

    @property
    def auto_refresh(self) -> float | None:
        """Number of seconds between automatic refresh, or `None` for no automatic refresh."""
        return self._auto_refresh

    @auto_refresh.setter
    def auto_refresh(self, interval: float | None) -> None:
        if self._auto_refresh_timer is not None:
            self._auto_refresh_timer.stop()
            self._auto_refresh_timer = None
        if interval is not None:
            self._auto_refresh_timer = self.set_interval(
                interval, self._automatic_refresh, name=f"auto refresh {self!r}"
            )
        self._auto_refresh = interval

    def run_worker(
        self,
        work: WorkType[ResultType],
        name: str | None = "",
        group: str = "default",
        description: str = "",
        exit_on_error: bool = True,
        start: bool = True,
        exclusive: bool = False,
        thread: bool = False,
    ) -> Worker[ResultType]:
        """Run work in a worker.

        A worker runs a function, coroutine, or awaitable, in the *background* as an async task or as a thread.

        Args:
            work: A function, async function, or an awaitable object to run in a worker.
            name: A short string to identify the worker (in logs and debugging).
            group: A short string to identify a group of workers.
            description: A longer string to store longer information on the worker.
            exit_on_error: Exit the app if the worker raises an error. Set to `False` to suppress exceptions.
            start: Start the worker immediately.
            exclusive: Cancel all workers in the same group.
            thread: Mark the worker as a thread worker.

        Returns:
            New Worker instance.
        """

        # If we're running a worker from inside a secondary thread,
        # do so in a thread-safe way.
        if self.app._thread_id != threading.get_ident():
            creator = partial(self.app.call_from_thread, self.app.workers._new_worker)
        else:
            creator = self.app.workers._new_worker
        worker: Worker[ResultType] = creator(
            work,
            self,
            name=name,
            group=group,
            description=description,
            exit_on_error=exit_on_error,
            start=start,
            exclusive=exclusive,
            thread=thread,
        )
        return worker

    @property
    def is_modal(self) -> bool:
        """Is the node a modal?"""
        return False

    def _automatic_refresh(self) -> None:
        """Perform an automatic refresh (set with auto_refresh property)."""
        self.refresh()

    def __init_subclass__(
        cls,
        inherit_css: bool = True,
        inherit_bindings: bool = True,
        inherit_component_classes: bool = True,
    ) -> None:
        super().__init_subclass__()

        reactives = cls._reactives = {}
        for base in reversed(cls.__mro__):
            reactives.update(
                {
                    name: reactive
                    for name, reactive in base.__dict__.items()
                    if isinstance(reactive, Reactive)
                }
            )

        cls._inherit_css = inherit_css
        cls._inherit_bindings = inherit_bindings
        cls._inherit_component_classes = inherit_component_classes
        css_type_names: set[str] = set()
        bases = cls._css_bases(cls)
        cls._css_type_name = bases[0].__name__
        for base in bases:
            css_type_names.add(base.__name__)
        cls._merged_bindings = cls._merge_bindings()
        cls._css_type_names = frozenset(css_type_names)
        cls._computes = frozenset(
            [
                name.lstrip("_")[8:]
                for name in dir(cls)
                if name.startswith(("_compute_", "compute_"))
            ]
        )

    def get_component_styles(self, *names: str) -> RenderStyles:
        """Get a "component" styles object (must be defined in COMPONENT_CLASSES classvar).

        Args:
            names: Names of the components.

        Raises:
            KeyError: If the component class doesn't exist.

        Returns:
            A Styles object.
        """
        styles = RenderStyles(self, Styles(), Styles())
        for name in names:
            if name not in self._component_styles:
                raise KeyError(f"No {name!r} key in COMPONENT_CLASSES")
            component_styles = self._component_styles[name]
            styles.node = component_styles.node
            styles.base.merge(component_styles.base)
            styles.inline.merge(component_styles.inline)
            styles._updates += 1

        return styles

    def _post_mount(self):
        """Called after the object has been mounted."""
        _rich_traceback_omit = True
        Reactive._initialize_object(self)

    def notify_style_update(self) -> None:
        """Called after styles are updated.

        Implement this in a subclass if you want to clear any cached data when the CSS is reloaded.
        """

    @property
    def _node_bases(self) -> Sequence[Type[DOMNode]]:
        """The DOMNode bases classes (including self.__class__)"""
        # Node bases are in reversed order so that the base class is lower priority
        return self._css_bases(self.__class__)

    @classmethod
    @lru_cache(maxsize=None)
    def _css_bases(cls, base: Type[DOMNode]) -> Sequence[Type[DOMNode]]:
        """Get the DOMNode base classes, which inherit CSS.

        Args:
            base: A DOMNode class

        Returns:
            An iterable of DOMNode classes.
        """
        classes: list[type[DOMNode]] = []
        _class = base
        while True:
            classes.append(_class)
            if not _class._inherit_css:
                break
            for _base in _class.__bases__:
                if issubclass(_base, DOMNode):
                    _class = _base
                    break
            else:
                break
        return classes

    @classmethod
    def _merge_bindings(cls) -> _Bindings:
        """Merge bindings from base classes.

        Returns:
            Merged bindings.
        """
        bindings: list[_Bindings] = []

        for base in reversed(cls.__mro__):
            if issubclass(base, DOMNode):
                if not base._inherit_bindings:
                    bindings.clear()
                bindings.append(
                    _Bindings(
                        base.__dict__.get("BINDINGS", []),
                    )
                )
        keys: dict[str, Binding] = {}
        for bindings_ in bindings:
            keys.update(bindings_.keys)
        return _Bindings(keys.values())

    def _post_register(self, app: App) -> None:
        """Called when the widget is registered

        Args:
            app: Parent application.
        """

    def __rich_repr__(self) -> rich.repr.Result:
        # Being a bit defensive here to guard against errors when calling repr before initialization
        if hasattr(self, "_name"):
            yield "name", self._name, None
        if hasattr(self, "_id"):
            yield "id", self._id, None
        if hasattr(self, "_classes") and self._classes:
            yield "classes", " ".join(self._classes)

    def _get_default_css(self) -> list[tuple[CSSLocation, str, int, str]]:
        """Gets the CSS for this class and inherited from bases.

        Default CSS is inherited from base classes, unless `inherit_css` is set to
        `False` when subclassing.

        Returns:
            A list of tuples containing (LOCATION, SOURCE, SPECIFICITY, SCOPE) for this
                class and inherited from base classes.
        """

        css_stack: list[tuple[CSSLocation, str, int, str]] = []

        def get_location(base: Type[DOMNode]) -> CSSLocation:
            """Get the original location of this DEFAULT_CSS.

            Args:
                base: The class from which the default css was extracted.

            Returns:
                The filename where the class was defined (if possible) and the class
                    variable the CSS was extracted from.
            """
            try:
                return (getfile(base), f"{base.__name__}.DEFAULT_CSS")
            except (TypeError, OSError):
                return ("", f"{base.__name__}.DEFAULT_CSS")

        for tie_breaker, base in enumerate(self._node_bases):
            css: str = base.__dict__.get("DEFAULT_CSS", "")
            if css:
                scoped: bool = base.__dict__.get("SCOPED_CSS", True)
                css_stack.append(
                    (
                        get_location(base),
                        css,
                        -tie_breaker,
                        base._css_type_name if scoped else "",
                    )
                )
        return css_stack

    @classmethod
    @lru_cache(maxsize=None)
    def _get_component_classes(cls) -> frozenset[str]:
        """Gets the component classes for this class and inherited from bases.

        Component classes are inherited from base classes, unless
        `inherit_component_classes` is set to `False` when subclassing.

        Returns:
            A set with all the component classes available.
        """

        component_classes: set[str] = set()
        for base in cls._css_bases(cls):
            component_classes.update(base.__dict__.get("COMPONENT_CLASSES", set()))
            if not base.__dict__.get("_inherit_component_classes", True):
                break

        return frozenset(component_classes)

    @property
    def parent(self) -> DOMNode | None:
        """The parent node.

        All nodes have parent once added to the DOM, with the exception of the App which is the *root* node.
        """
        return cast("DOMNode | None", self._parent)

    @property
    def screen(self) -> "Screen[object]":
        """The screen containing this node.

        Returns:
            A screen object.

        Raises:
            NoScreen: If this node isn't mounted (and has no screen).
        """
        # Get the node by looking up a chain of parents
        # Note that self.screen may not be the same as self.app.screen
        from .screen import Screen

        node: MessagePump | None = self
        while node is not None and not isinstance(node, Screen):
            node = node._parent
        if not isinstance(node, Screen):
            raise NoScreen("node has no screen")
        return node

    @property
    def id(self) -> str | None:
        """The ID of this node, or None if the node has no ID."""
        return self._id

    @id.setter
    def id(self, new_id: str) -> str:
        """Sets the ID (may only be done once).

        Args:
            new_id: ID for this node.

        Raises:
            ValueError: If the ID has already been set.
        """
        check_identifiers("id", new_id)

        if self._id is not None:
            raise ValueError(
                f"Node 'id' attribute may not be changed once set (current id={self._id!r})"
            )
        self._id = new_id
        return new_id

    @property
    def name(self) -> str | None:
        """The name of the node."""
        return self._name

    @property
    def css_identifier(self) -> str:
        """A CSS selector that identifies this DOM node."""
        tokens = [self.__class__.__name__]
        if self.id is not None:
            tokens.append(f"#{self.id}")
        return "".join(tokens)

    @property
    def css_identifier_styled(self) -> Text:
        """A syntax highlighted CSS identifier.

        Returns:
            A Rich Text object.
        """
        tokens = Text.styled(self.__class__.__name__)
        if self.id is not None:
            tokens.append(f"#{self.id}", style="bold")
        if self.classes:
            tokens.append(".")
            tokens.append(".".join(class_name for class_name in self.classes), "italic")
        if self.name:
            tokens.append(f"[name={self.name}]", style="underline")
        return tokens

    classes = _ClassesDescriptor()
    """CSS class names for this node."""

    @property
    def pseudo_classes(self) -> frozenset[str]:
        """A (frozen) set of all pseudo classes."""
        return frozenset(self.get_pseudo_classes())

    @property
    def css_path_nodes(self) -> list[DOMNode]:
        """A list of nodes from the App to this node, forming a "path".

        Returns:
            A list of nodes, where the first item is the App, and the last is this node.
        """
        result: list[DOMNode] = [self]
        append = result.append

        node: DOMNode = self
        while isinstance((node := node._parent), DOMNode):
            append(node)
        return result[::-1]

    @property
    def _selector_names(self) -> set[str]:
        """Get a set of selectors applicable to this widget.

        Returns:
            Set of selector names.
        """
        selectors: set[str] = {
            "*",
            *(f".{class_name}" for class_name in self._classes),
            *self._css_types,
        }
        if self._id is not None:
            selectors.add(f"#{self._id}")
        return selectors

    @property
    def display(self) -> bool:
        """Should the DOM node be displayed?

        May be set to a boolean to show or hide the node, or to any valid value for the `display` rule.

        Example:
            ```python
            my_widget.display = False  # Hide my_widget
            ```
        """
        return self.styles.display != "none" and not (
            self._closing or self._closed or self._pruning
        )

    @display.setter
    def display(self, new_val: bool | str) -> None:
        """
        Args:
            new_val: Shortcut to set the ``display`` CSS property.
                ``False`` will set ``display: none``. ``True`` will set ``display: block``.
                A ``False`` value will prevent the DOMNode from consuming space in the layout.
        """
        # TODO: This will forget what the original "display" value was, so if a user
        #  toggles to False then True, we'll reset to the default "block", rather than
        #  what the user initially specified.
        if isinstance(new_val, bool):
            self.styles.display = "block" if new_val else "none"
        elif new_val in VALID_DISPLAY:
            self.styles.display = new_val
        else:
            raise StyleValueError(
                f"invalid value for display (received {new_val!r}, "
                f"expected {friendly_list(VALID_DISPLAY)})",
            )

    @property
    def visible(self) -> bool:
        """Is this widget visible in the DOM?

        If a widget hasn't had its visibility set explicitly, then it inherits it from its
        DOM ancestors.

        This may be set explicitly to override inherited values.
        The valid values include the valid values for the `visibility` rule and the booleans
        `True` or `False`, to set the widget to be visible or invisible, respectively.

        When a node is invisible, Textual will reserve space for it, but won't display anything.
        """
        own_value = self.styles.get_rule("visibility")
        if own_value is not None:
            return own_value != "hidden"
        return self.parent.visible if self.parent else True

    @visible.setter
    def visible(self, new_value: bool | str) -> None:
        if isinstance(new_value, bool):
            self.styles.visibility = "visible" if new_value else "hidden"
        elif new_value in VALID_VISIBILITY:
            self.styles.visibility = new_value
        else:
            raise StyleValueError(
                f"invalid value for visibility (received {new_value!r}, "
                f"expected {friendly_list(VALID_VISIBILITY)})"
            )

    @property
    def tree(self) -> Tree:
        """A Rich tree to display the DOM.

        Log this to visualize your app in the textual console.

        Example:
            ```python
            self.log(self.tree)
            ```

        Returns:
            A Tree renderable.
        """
        from rich.pretty import Pretty

        def render_info(node: DOMNode) -> Pretty:
            """Render a node for the tree."""
            return Pretty(node)

        tree = Tree(render_info(self))

        def add_children(tree, node):
            for child in node.children:
                info = render_info(child)
                branch = tree.add(info)
                if tree.children:
                    add_children(branch, child)

        add_children(tree, self)
        return tree

    @property
    def css_tree(self) -> Tree:
        """A Rich tree to display the DOM, annotated with the node's CSS.

        Log this to visualize your app in the textual console.

        Example:
            ```python
            self.log(self.css_tree)
            ```

        Returns:
            A Tree renderable.
        """
        from rich.columns import Columns
        from rich.console import Group
        from rich.panel import Panel
        from rich.pretty import Pretty

        from .widget import Widget

        def render_info(node: DOMNode) -> Columns:
            """Render a node for the tree."""
            if isinstance(node, Widget):
                info = Columns(
                    [
                        Pretty(node),
                        highlighter(f"region={node.region!r}"),
                        highlighter(
                            f"virtual_size={node.virtual_size!r}",
                        ),
                    ]
                )
            else:
                info = Columns([Pretty(node)])
            return info

        highlighter = ReprHighlighter()
        tree = Tree(render_info(self))

        def add_children(tree: Tree, node: DOMNode) -> None:
            """Add children to the tree."""
            for child in node.children:
                info: RenderableType = render_info(child)
                css = child.styles.css
                if css:
                    info = Group(
                        info,
                        Panel.fit(
                            Text(child.styles.css),
                            border_style="dim",
                            title="css",
                            title_align="left",
                        ),
                    )
                branch = tree.add(info)
                if tree.children:
                    add_children(branch, child)

        add_children(tree, self)
        return tree

    @property
    def text_style(self) -> Style:
        """Get the text style object.

        A widget's style is influenced by its parent. for instance if a parent is bold, then
        the child will also be bold.

        Returns:
            A Rich Style.
        """
        return Style.combine(
            node.styles.text_style for node in reversed(self.ancestors_with_self)
        )

    @property
    def rich_style(self) -> Style:
        """Get a Rich Style object for this DOMNode.

        Returns:
            A Rich style.
        """
        background = Color(0, 0, 0, 0)
        color = Color(255, 255, 255, 0)

        style = Style()
        opacity = 1.0

        for node in reversed(self.ancestors_with_self):
            styles = node.styles
            opacity *= styles.opacity
            if styles.has_rule("background"):
                text_background = background + styles.background
                background += styles.background.multiply_alpha(opacity)
            else:
                text_background = background
            if styles.has_rule("color"):
                color = styles.color
            style += styles.text_style
            if styles.has_rule("auto_color") and styles.auto_color:
                color = text_background.get_contrast_text(color.a)

        style += Style.from_color(
            (background + color).rich_color if (background.a or color.a) else None,
            background.rich_color if background.a else None,
        )
        return style

    def _get_title_style_information(
        self, background: Color
    ) -> tuple[Color, Color, Style]:
        """Get a Rich Style object for for titles.

        Args:
            background: The background color.

        Returns:
            A Rich style.
        """
        styles = self.styles
        if styles.auto_border_title_color:
            color = background.get_contrast_text(styles.border_title_color.a)
        else:
            color = styles.border_title_color
        return (
            color,
            styles.border_title_background,
            styles.border_title_style,
        )

    def _get_subtitle_style_information(
        self, background: Color
    ) -> tuple[Color, Color, Style]:
        """Get a Rich Style object for for titles.

        Args:
            background: The background color.

        Returns:
            A Rich style.
        """
        styles = self.styles
        if styles.auto_border_subtitle_color:
            color = background.get_contrast_text(styles.border_subtitle_color.a)
        else:
            color = styles.border_subtitle_color
        return (
            color,
            styles.border_subtitle_background,
            styles.border_subtitle_style,
        )

    @property
    def background_colors(self) -> tuple[Color, Color]:
        """The background color and the color of the parent's background.

        Returns:
            `(<background color>, <color>)`
        """
        base_background = background = BLACK
        for node in reversed(self.ancestors_with_self):
            styles = node.styles
            base_background = background
            background += styles.background
        return (base_background, background)

    @property
    def _opacity_background_colors(self) -> tuple[Color, Color]:
        """Background colors adjusted for opacity.

        Returns:
            `(<background color>, <color>)`
        """
        base_background = background = BLACK
        opacity = 1.0
        for node in reversed(self.ancestors_with_self):
            styles = node.styles
            base_background = background
            opacity *= styles.opacity
            background += styles.background.multiply_alpha(opacity)
        return (base_background, background)

    @property
    def colors(self) -> tuple[Color, Color, Color, Color]:
        """The widget's background and foreground colors, and the parent's background and foreground colors.

        Returns:
            `(<parent background>, <parent color>, <background>, <color>)`
        """
        base_background = background = WHITE
        base_color = color = BLACK
        for node in reversed(self.ancestors_with_self):
            styles = node.styles
            base_background = background
            background += styles.background
            if styles.has_rule("color"):
                base_color = color
                if styles.auto_color:
                    color = background.get_contrast_text(color.a)
                else:
                    color = styles.color

        return (base_background, base_color, background, color)

    @property
    def ancestors_with_self(self) -> list[DOMNode]:
        """A list of ancestor nodes found by tracing a path all the way back to App.

        Note:
            This is inclusive of ``self``.

        Returns:
            A list of nodes.
        """
        nodes: list[MessagePump | None] = [self]
        add_node = nodes.append
        node: MessagePump | None = self
        while (node := node._parent) is not None:
            add_node(node)
        return cast("list[DOMNode]", nodes)

    @property
    def ancestors(self) -> list[DOMNode]:
        """A list of ancestor nodes found by tracing a path all the way back to App.

        Returns:
            A list of nodes.
        """
        nodes: list[MessagePump | None] = []
        add_node = nodes.append
        node: MessagePump | None = self
        while (node := node._parent) is not None:
            add_node(node)
        return cast("list[DOMNode]", nodes)

    @property
    def displayed_children(self) -> list[Widget]:
        """The child nodes which will be displayed.

        Returns:
            A list of nodes.
        """
        return [child for child in self._nodes if child.display]

    def watch(
        self,
        obj: DOMNode,
        attribute_name: str,
        callback: WatchCallbackType,
        init: bool = True,
    ) -> None:
        """Watches for modifications to reactive attributes on another object.

        Example:

            Here's how you could detect when the app changes from dark to light mode (and vice versa).

            ```python
            def on_dark_change(old_value:bool, new_value:bool):
                # Called when app.dark changes.
                print("App.dark when from {old_value} to {new_value}")

            self.watch(self.app, "dark", self.on_dark_change, init=False)
            ```

        Args:
            obj: Object containing attribute to watch.
            attribute_name: Attribute to watch.
            callback: A callback to run when attribute changes.
            init: Check watchers on first call.
        """
        _watch(self, obj, attribute_name, callback, init=init)

    def get_pseudo_classes(self) -> Iterable[str]:
        """Get any pseudo classes applicable to this Node, e.g. hover, focus.

        Returns:
            Iterable of strings, such as a generator.
        """
        return ()

    def reset_styles(self) -> None:
        """Reset styles back to their initial state."""
        from .widget import Widget

        for node in self.walk_children(with_self=True):
            node._css_styles.reset()
            if isinstance(node, Widget):
                node._set_dirty()
                node._layout_required = True

    def _add_child(self, node: Widget) -> None:
        """Add a new child node.

        !!! note
            For tests only.

        Args:
            node: A DOM node.
        """
        self._nodes._append(node)
        node._attach(self)

    def _add_children(self, *nodes: Widget) -> None:
        """Add multiple children to this node.

        !!! note
            For tests only.

        Args:
            *nodes: Positional args should be new DOM nodes.
        """
        _append = self._nodes._append
        for node in nodes:
            node._attach(self)
            _append(node)
            node._add_children(*node._pending_children)

    WalkType = TypeVar("WalkType", bound="DOMNode")

    if TYPE_CHECKING:

        @overload
        def walk_children(
            self,
            filter_type: type[WalkType],
            *,
            with_self: bool = False,
            method: WalkMethod = "depth",
            reverse: bool = False,
        ) -> list[WalkType]: ...

        @overload
        def walk_children(
            self,
            *,
            with_self: bool = False,
            method: WalkMethod = "depth",
            reverse: bool = False,
        ) -> list[DOMNode]: ...

    def walk_children(
        self,
        filter_type: type[WalkType] | None = None,
        *,
        with_self: bool = False,
        method: WalkMethod = "depth",
        reverse: bool = False,
    ) -> list[DOMNode] | list[WalkType]:
        """Walk the subtree rooted at this node, and return every descendant encountered in a list.

        Args:
            filter_type: Filter only this type, or None for no filter.
            with_self: Also yield self in addition to descendants.
            method: One of "depth" or "breadth".
            reverse: Reverse the order (bottom up).

        Returns:
            A list of nodes.
        """
        check_type = filter_type or DOMNode

        node_generator = (
            walk_depth_first(self, check_type, with_root=with_self)
            if method == "depth"
            else walk_breadth_first(self, check_type, with_root=with_self)
        )

        # We want a snapshot of the DOM at this point So that it doesn't
        # change mid-walk
        nodes = list(node_generator)
        if reverse:
            nodes.reverse()
        return cast("list[DOMNode]", nodes)

    if TYPE_CHECKING:

        @overload
        def query(self, selector: str | None = None) -> DOMQuery[Widget]: ...

        @overload
        def query(self, selector: type[QueryType]) -> DOMQuery[QueryType]: ...

    def query(
        self, selector: str | type[QueryType] | None = None
    ) -> DOMQuery[Widget] | DOMQuery[QueryType]:
        """Query the DOM for children that match a selector or widget type.

        Args:
            selector: A CSS selector, widget type, or `None` for all nodes.

        Returns:
            A query object.
        """
        from .css.query import DOMQuery, QueryType
        from .widget import Widget

        if isinstance(selector, str) or selector is None:
            return DOMQuery[Widget](self, filter=selector)
        else:
            return DOMQuery[QueryType](self, filter=selector.__name__)

    if TYPE_CHECKING:

        @overload
        def query_children(self, selector: str | None = None) -> DOMQuery[Widget]: ...

        @overload
        def query_children(self, selector: type[QueryType]) -> DOMQuery[QueryType]: ...

    def query_children(
        self, selector: str | type[QueryType] | None = None
    ) -> DOMQuery[Widget] | DOMQuery[QueryType]:
        """Query the DOM for the immediate children that match a selector or widget type.

        Note that this will not return child widgets more than a single level deep.
        If you want to a query to potentially match all children in the widget tree,
        see [query][textual.dom.DOMNode.query].

        Args:
            selector: A CSS selector, widget type, or `None` for all nodes.

        Returns:
            A query object.
        """
        from .css.query import DOMQuery, QueryType
        from .widget import Widget

        if isinstance(selector, str) or selector is None:
            return DOMQuery[Widget](self, deep=False, filter=selector)
        else:
            return DOMQuery[QueryType](self, deep=False, filter=selector.__name__)

    if TYPE_CHECKING:

        @overload
        def query_one(self, selector: str) -> Widget: ...

        @overload
        def query_one(self, selector: type[QueryType]) -> QueryType: ...

        @overload
        def query_one(
            self, selector: str, expect_type: type[QueryType]
        ) -> QueryType: ...

    def query_one(
        self,
        selector: str | type[QueryType],
        expect_type: type[QueryType] | None = None,
    ) -> QueryType | Widget:
        """Get a widget from this widget's children that matches a selector or widget type.

        Args:
            selector: A selector or widget type.
            expect_type: Require the object be of the supplied type, or None for any type.

        Raises:
            WrongType: If the wrong type was found.
            NoMatches: If no node matches the query.
            TooManyMatches: If there is more than one matching node in the query.

        Returns:
            A widget matching the selector.
        """
        _rich_traceback_omit = True
        from .css.query import DOMQuery

        if isinstance(selector, str):
            query_selector = selector
        else:
            query_selector = selector.__name__
        query: DOMQuery[Widget] = DOMQuery(self, filter=query_selector)

        return query.only_one() if expect_type is None else query.only_one(expect_type)

    def set_styles(self, css: str | None = None, **update_styles: Any) -> Self:
        """Set custom styles on this object.

        Args:
            css: Styles in CSS format.
            update_styles: Keyword arguments map style names onto style values.

        Returns:
            Self.
        """

        if css is not None:
            try:
                new_styles = parse_declarations(css, read_from=("set_styles", ""))
            except DeclarationError as error:
                raise DeclarationError(error.name, error.token, error.message) from None
            self._inline_styles.merge(new_styles)
            self.refresh(layout=True)

        styles = self.styles
        for key, value in update_styles.items():
            setattr(styles, key, value)
        return self

    def has_class(self, *class_names: str) -> bool:
        """Check if the Node has all the given class names.

        Args:
            *class_names: CSS class names to check.

        Returns:
            ``True`` if the node has all the given class names, otherwise ``False``.
        """
        return self._classes.issuperset(class_names)

    def set_class(self, add: bool, *class_names: str, update: bool = True) -> Self:
        """Add or remove class(es) based on a condition.

        Args:
            add: Add the classes if True, otherwise remove them.
            update: Also update styles.

        Returns:
            Self.
        """
        if add:
            self.add_class(*class_names, update=update)
        else:
            self.remove_class(*class_names, update=update)
        return self

    def set_classes(self, classes: str | Iterable[str]) -> Self:
        """Replace all classes.

        Args:
            classes: A string containing space separated classes, or an
                iterable of class names.

        Returns:
            Self.
        """
        self.classes = classes
        return self

    def _update_styles(self) -> None:
        """Request an update of this node's styles.

        Should be called whenever CSS classes / pseudo classes change.
        """
        try:
            self.app.update_styles(self)
        except NoActiveAppError:
            pass

    def add_class(self, *class_names: str, update: bool = True) -> Self:
        """Add class names to this Node.

        Args:
            *class_names: CSS class names to add.
            update: Also update styles.

        Returns:
            Self.
        """
        check_identifiers("class name", *class_names)
        old_classes = self._classes.copy()
        self._classes.update(class_names)
        if old_classes == self._classes:
            return self
        if update:
            self._update_styles()
        return self

    def remove_class(self, *class_names: str, update: bool = True) -> Self:
        """Remove class names from this Node.

        Args:
            *class_names: CSS class names to remove.
            update: Also update styles.

        Returns:
            Self.
        """
        check_identifiers("class name", *class_names)
        old_classes = self._classes.copy()
        self._classes.difference_update(class_names)
        if old_classes == self._classes:
            return self
        if update:
            self._update_styles()
        return self

    def toggle_class(self, *class_names: str) -> Self:
        """Toggle class names on this Node.

        Args:
            *class_names: CSS class names to toggle.

        Returns:
            Self.
        """
        check_identifiers("class name", *class_names)
        old_classes = self._classes.copy()
        self._classes.symmetric_difference_update(class_names)
        if old_classes == self._classes:
            return self
        self._update_styles()
        return self

    def has_pseudo_class(self, class_name: str) -> bool:
        """Check the node has the given pseudo class.

        Args:
            class_name: The pseudo class to check for.

        Returns:
            `True` if the DOM node has the pseudo class, `False` if not.
        """
        return class_name in self.get_pseudo_classes()

    def has_pseudo_classes(self, class_names: set[str]) -> bool:
        """Check the node has all the given pseudo classes.

        Args:
            class_names: Set of class names to check for.

        Returns:
            `True` if all pseudo class names are present.
        """
        return class_names.issubset(self.get_pseudo_classes())

    def refresh(
        self, *, repaint: bool = True, layout: bool = False, recompose: bool = False
    ) -> Self:
        return self

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Check whether an action is enabled.

        Implement this method to add logic for [dynamic actions](/guide/actions#dynamic-actions) / bindings.

        Args:
            action: The name of an action.
            parameters: A tuple of any action parameters.

        Returns:
            `True` if the action is enabled+visible,
                `False` if the action is disabled+hidden,
                `None` if the action is disabled+visible (grayed out in footer)
        """
        return True

    def refresh_bindings(self) -> None:
        """Call to prompt widgets such as the [Footer][textual.widgets.Footer] to update
        the display of key bindings.

        See [actions](/guide/actions#dynamic-actions) for how to use this method.

        """
        self.screen.refresh_bindings()

    async def action_toggle(self, attribute_name: str) -> None:
        """Toggle an attribute on the node.

        Assumes the attribute is a bool.

        Args:
            attribute_name: Name of the attribute.
        """
        value = getattr(self, attribute_name)
        setattr(self, attribute_name, not value)
