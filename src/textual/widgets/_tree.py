"""Provides a tree widget."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Generic, Iterable, NewType, TypeVar, cast

import rich.repr
from rich.style import NULL_STYLE, Style
from rich.text import Text, TextType

from textual import events, on
from textual._immutable_sequence_view import ImmutableSequenceView
from textual._loop import loop_last
from textual._segment_tools import line_pad
from textual.binding import Binding, BindingType
from textual.cache import LRUCache
from textual.geometry import Region, Size, clamp
from textual.message import Message
from textual.reactive import reactive, var
from textual.scroll_view import ScrollView
from textual.strip import Strip

if TYPE_CHECKING:
    from typing_extensions import Self, TypeAlias

NodeID = NewType("NodeID", int)
"""The type of an ID applied to a [TreeNode][textual.widgets._tree.TreeNode]."""

TreeDataType = TypeVar("TreeDataType")
"""The type of the data for a given instance of a [Tree][textual.widgets.Tree]."""

EventTreeDataType = TypeVar("EventTreeDataType")
"""The type of the data for a given instance of a [Tree][textual.widgets.Tree].

Similar to [TreeDataType][textual.widgets._tree.TreeDataType] but used for
``Tree`` messages.
"""

LineCacheKey: TypeAlias = "tuple[int | tuple, ...]"

TOGGLE_STYLE = Style.from_meta({"toggle": True})


class RemoveRootError(Exception):
    """Exception raised when trying to remove the root of a [`TreeNode`][textual.widgets.tree.TreeNode]."""


class UnknownNodeID(Exception):
    """Exception raised when referring to an unknown [`TreeNode`][textual.widgets.tree.TreeNode] ID."""


class AddNodeError(Exception):
    """Exception raised when there is an error with a request to add a node."""


@dataclass
class _TreeLine(Generic[TreeDataType]):
    path: list[TreeNode[TreeDataType]]
    last: bool

    @property
    def node(self) -> TreeNode[TreeDataType]:
        """The node associated with this line."""
        return self.path[-1]

    def _get_guide_width(self, guide_depth: int, show_root: bool) -> int:
        """Get the cell width of the line as rendered.

        Args:
            guide_depth: The guide depth (cells in the indentation).

        Returns:
            Width in cells.
        """
        if show_root:
            width = (max(0, len(self.path) - 1)) * guide_depth
        else:
            width = 0
            if len(self.path) > 1:
                width += (len(self.path) - 1) * guide_depth

        return width


class TreeNodes(ImmutableSequenceView["TreeNode[TreeDataType]"]):
    """An immutable collection of `TreeNode`."""


@rich.repr.auto
class TreeNode(Generic[TreeDataType]):
    """An object that represents a "node" in a tree control."""

    def __init__(
        self,
        tree: Tree[TreeDataType],
        parent: TreeNode[TreeDataType] | None,
        id: NodeID,
        label: Text,
        data: TreeDataType | None = None,
        *,
        expanded: bool = True,
        allow_expand: bool = True,
    ) -> None:
        """Initialise the node.

        Args:
            tree: The tree that the node is being attached to.
            parent: The parent node that this node is being attached to.
            id: The ID of the node.
            label: The label for the node.
            data: Optional data to associate with the node.
            expanded: Should the node be attached in an expanded state?
            allow_expand: Should the node allow being expanded by the user?
        """
        self._tree = tree
        self._parent = parent
        self._id = id
        self._label = tree.process_label(label)
        self.data = data
        """Optional data associated with the tree node."""
        self._expanded = expanded
        self._children: list[TreeNode[TreeDataType]] = []

        self._hover_ = False
        self._selected_ = False
        self._allow_expand = allow_expand
        self._updates: int = 0
        self._line: int = -1

    def __rich_repr__(self) -> rich.repr.Result:
        yield self._label.plain
        yield self.data

    def _reset(self) -> None:
        self._hover_ = False
        self._selected_ = False
        self._updates += 1

    @property
    def tree(self) -> Tree[TreeDataType]:
        """The tree that this node is attached to."""
        return self._tree

    @property
    def children(self) -> TreeNodes[TreeDataType]:
        """The child nodes of a TreeNode."""
        return TreeNodes(self._children)

    @property
    def siblings(self) -> TreeNodes[TreeDataType]:
        """The siblings of this node (includes self)."""
        if self.parent is None:
            return TreeNodes([self])
        else:
            return self.parent.children

    @property
    def line(self) -> int:
        """The line number for this node, or -1 if it is not displayed."""
        return self._line

    @property
    def _hover(self) -> bool:
        """Check if the mouse is over the node."""
        return self._hover_

    @_hover.setter
    def _hover(self, hover: bool) -> None:
        self._updates += 1
        self._hover_ = hover

    @property
    def _selected(self) -> bool:
        """Check if the node is selected."""
        return self._selected_

    @_selected.setter
    def _selected(self, selected: bool) -> None:
        self._updates += 1
        self._selected_ = selected

    @property
    def id(self) -> NodeID:
        """The ID of the  node."""
        return self._id

    @property
    def parent(self) -> TreeNode[TreeDataType] | None:
        """The parent of the node."""
        return self._parent

    @property
    def next_sibling(self) -> TreeNode[TreeDataType] | None:
        """The next sibling below the node."""
        siblings = self.siblings
        index = siblings.index(self) + 1
        try:
            return siblings[index]
        except IndexError:
            return None

    @property
    def previous_sibling(self) -> TreeNode[TreeDataType] | None:
        """The previous sibling below the node."""
        siblings = self.siblings
        index = siblings.index(self) - 1
        if index < 0:
            return None
        try:
            return siblings[index]
        except IndexError:
            return None

    @property
    def is_expanded(self) -> bool:
        """Is the node expanded?"""
        return self._expanded

    @property
    def is_collapsed(self) -> bool:
        """Is the node collapsed?"""
        return not self._expanded

    @property
    def is_last(self) -> bool:
        """Is this the last child node of its parent?"""
        if self._parent is None:
            return True
        return bool(
            self._parent._children and self._parent._children[-1] == self,
        )

    @property
    def is_root(self) -> bool:
        """Is this node the root of the tree?"""
        return self == self._tree.root

    @property
    def allow_expand(self) -> bool:
        """Is this node allowed to expand?"""
        return self._allow_expand

    @allow_expand.setter
    def allow_expand(self, allow_expand: bool) -> None:
        self._allow_expand = allow_expand
        self._updates += 1

    def _expand(self, expand_all: bool) -> None:
        """Mark the node as expanded (its children are shown).

        Args:
            expand_all: If `True` expand all offspring at all depths.
        """
        self._expanded = True
        self._updates += 1
        self._tree.post_message(Tree.NodeExpanded(self).set_sender(self._tree))
        if expand_all:
            for child in self.children:
                child._expand(expand_all)

    def expand(self) -> Self:
        """Expand the node (show its children).

        Returns:
            The `TreeNode` instance.
        """
        self._expand(False)
        self._tree._invalidate()
        return self

    def expand_all(self) -> Self:
        """Expand the node (show its children) and all those below it.

        Returns:
            The `TreeNode` instance.
        """
        self._expand(True)
        self._tree._invalidate()
        return self

    def _collapse(self, collapse_all: bool) -> None:
        """Mark the node as collapsed (its children are hidden).

        Args:
            collapse_all: If `True` collapse all offspring at all depths.
        """
        self._expanded = False
        self._updates += 1
        self._tree.post_message(Tree.NodeCollapsed(self).set_sender(self._tree))
        if collapse_all:
            for child in self.children:
                child._collapse(collapse_all)

    def collapse(self) -> Self:
        """Collapse the node (hide its children).

        Returns:
            The `TreeNode` instance.
        """
        self._collapse(False)
        self._tree._invalidate()
        return self

    def collapse_all(self) -> Self:
        """Collapse the node (hide its children) and all those below it.

        Returns:
            The `TreeNode` instance.
        """
        self._collapse(True)
        self._tree._invalidate()
        return self

    def toggle(self) -> Self:
        """Toggle the node's expanded state.

        Returns:
            The `TreeNode` instance.
        """
        if self._expanded:
            self.collapse()
        else:
            self.expand()
        return self

    def toggle_all(self) -> Self:
        """Toggle the node's expanded state and make all those below it match.

        Returns:
            The `TreeNode` instance.
        """
        if self._expanded:
            self.collapse_all()
        else:
            self.expand_all()
        return self

    @property
    def label(self) -> TextType:
        """The label for the node."""
        return self._label

    @label.setter
    def label(self, new_label: TextType) -> None:
        self.set_label(new_label)

    def set_label(self, label: TextType) -> None:
        """Set a new label for the node.

        Args:
            label: A ``str`` or ``Text`` object with the new label.
        """
        self._updates += 1
        text_label = self._tree.process_label(label)
        self._label = text_label
        self._tree.call_later(self._tree._refresh_node, self)

    def add(
        self,
        label: TextType,
        data: TreeDataType | None = None,
        *,
        before: int | TreeNode[TreeDataType] | None = None,
        after: int | TreeNode[TreeDataType] | None = None,
        expand: bool = False,
        allow_expand: bool = True,
    ) -> TreeNode[TreeDataType]:
        """Add a node to the sub-tree.

        Args:
            label: The new node's label.
            data: Data associated with the new node.
            before: Optional index or `TreeNode` to add the node before.
            after: Optional index or `TreeNode` to add the node after.
            expand: Node should be expanded.
            allow_expand: Allow user to expand the node via keyboard or mouse.

        Returns:
            A new Tree node

        Raises:
            AddNodeError: If there is a problem with the addition request.

        Note:
            Only one of `before` or `after` can be provided. If both are
            provided a `AddNodeError` will be raised.
        """
        if before is not None and after is not None:
            raise AddNodeError("Unable to add a node both before and after a node")

        insert_index: int = len(self.children)

        if before is not None:
            if isinstance(before, int):
                insert_index = before
            elif isinstance(before, TreeNode):
                try:
                    insert_index = self.children.index(before)
                except ValueError:
                    raise AddNodeError(
                        "The node specified for `before` is not a child of this node"
                    )
            else:
                raise TypeError(
                    "`before` argument must be an index or a TreeNode object to add before"
                )

        if after is not None:
            if isinstance(after, int):
                insert_index = after + 1
                if after < 0:
                    insert_index += len(self.children)
            elif isinstance(after, TreeNode):
                try:
                    insert_index = self.children.index(after) + 1
                except ValueError:
                    raise AddNodeError(
                        "The node specified for `after` is not a child of this node"
                    )
            else:
                raise TypeError(
                    "`after` argument must be an index or a TreeNode object to add after"
                )

        text_label = self._tree.process_label(label)
        node = self._tree._add_node(self, text_label, data)
        node._expanded = expand
        node._allow_expand = allow_expand
        self._updates += 1
        self._children.insert(insert_index, node)
        self._tree._invalidate()

        return node

    def add_leaf(
        self,
        label: TextType,
        data: TreeDataType | None = None,
        *,
        before: int | TreeNode[TreeDataType] | None = None,
        after: int | TreeNode[TreeDataType] | None = None,
    ) -> TreeNode[TreeDataType]:
        """Add a 'leaf' node (a node that can not expand).

        Args:
            label: Label for the node.
            data: Optional data.
            before: Optional index or `TreeNode` to add the node before.
            after: Optional index or `TreeNode` to add the node after.

        Returns:
            New node.

        Raises:
            AddNodeError: If there is a problem with the addition request.

        Note:
            Only one of `before` or `after` can be provided. If both are
            provided a `AddNodeError` will be raised.
        """
        node = self.add(
            label,
            data,
            before=before,
            after=after,
            expand=False,
            allow_expand=False,
        )
        return node

    def _remove_children(self) -> None:
        """Remove child nodes of this node.

        Note:
            This is the internal support method for `remove_children`. Call
            `remove_children` to ensure the tree gets refreshed.
        """
        for child in reversed(self._children):
            child._remove()

    def _remove(self) -> None:
        """Remove the current node and all its children.

        Note:
            This is the internal support method for `remove`. Call `remove`
            to ensure the tree gets refreshed.
        """
        self._remove_children()
        assert self._parent is not None
        del self._parent._children[self._parent._children.index(self)]
        del self._tree._tree_nodes[self.id]

    def remove(self) -> None:
        """Remove this node from the tree.

        Raises:
            RemoveRootError: If there is an attempt to remove the root.
        """
        if self.is_root:
            raise RemoveRootError("Attempt to remove the root node of a Tree.")
        self._remove()
        self._tree._invalidate()

    def remove_children(self) -> None:
        """Remove any child nodes of this node."""
        self._remove_children()
        self._tree._invalidate()

    def refresh(self) -> None:
        """Initiate a refresh (repaint) of this node."""
        self._updates += 1
        self._tree._refresh_line(self._line)


class Tree(Generic[TreeDataType], ScrollView, can_focus=True):
    """A widget for displaying and navigating data in a tree."""

    ICON_NODE = "▶ "
    """Unicode 'icon' to use for an expandable node."""
    ICON_NODE_EXPANDED = "▼ "
    """Unicode 'icon' to use for an expanded node."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("shift+left", "cursor_parent", "Cursor to parent", show=False),
        Binding(
            "shift+right",
            "cursor_parent_next_sibling",
            "Cursor to next ancestor",
            show=False,
        ),
        Binding(
            "shift+up",
            "cursor_previous_sibling",
            "Cursor to previous sibling",
            show=False,
        ),
        Binding(
            "shift+down",
            "cursor_next_sibling",
            "Cursor to next sibling",
            show=False,
        ),
        Binding("enter", "select_cursor", "Select", show=False),
        Binding("space", "toggle_node", "Toggle", show=False),
        Binding(
            "shift+space", "toggle_expand_all", "Expand or collapse all", show=False
        ),
        Binding("up", "cursor_up", "Cursor Up", show=False),
        Binding("down", "cursor_down", "Cursor Down", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | enter | Select the current item. |
    | space | Toggle the expand/collapsed space of the current item. |
    | up | Move the cursor up. |
    | down | Move the cursor down. |
    """

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "tree--cursor",
        "tree--guides",
        "tree--guides-hover",
        "tree--guides-selected",
        "tree--highlight",
        "tree--highlight-line",
        "tree--label",
    }
    """
    | Class | Description |
    | :- | :- |
    | `tree--cursor` | Targets the cursor. |
    | `tree--guides` | Targets the indentation guides. |
    | `tree--guides-hover` | Targets the indentation guides under the cursor. |
    | `tree--guides-selected` | Targets the indentation guides that are selected. |
    | `tree--highlight` | Targets the highlighted items. |
    | `tree--highlight-line` | Targets the lines under the cursor. |
    | `tree--label` | Targets the (text) labels of the items. |
    """

    DEFAULT_CSS = """
    Tree {
        background: $surface;
        color: $foreground;

        & > .tree--label {}
        & > .tree--guides {
            color: $surface-lighten-2;
        }
        & > .tree--guides-hover {
            color: $surface-lighten-2;
        }
        & > .tree--guides-selected {
            color: $block-cursor-blurred-background;
        }
        & > .tree--cursor {
            text-style: $block-cursor-blurred-text-style;
            background: $block-cursor-blurred-background;
        }
        & > .tree--highlight {}
        & > .tree--highlight-line {
            background: $block-hover-background;
        }

        &:focus {
            background-tint: $foreground 5%;
            & > .tree--cursor {
                color: $block-cursor-foreground;
                background: $block-cursor-background;
                text-style: $block-cursor-text-style;
            }
            & > .tree--guides {
                color: $surface-lighten-3;
            }
            & > .tree--guides-hover {
                color: $surface-lighten-3;
            }
            & > .tree--guides-selected {
                color: $block-cursor-background;
            }
        }

        &:light {
            /* In light mode the guides are darker*/
            & > .tree--guides {
                color: $surface-darken-1;
            }
            & > .tree--guides-hover {
                color: $block-cursor-background;
            }
            & > .tree--guides-selected {
                color: $block-cursor-background;
            }
        }

        &:ansi {
            color: ansi_default;
            & > .tree--guides {
                color: ansi_green;
            }
            &:nocolor > .tree--cursor{
                text-style: reverse;
            }
        }
    }

    """

    show_root = reactive(True)
    """Show the root of the tree."""
    hover_line = var(-1)
    """The line number under the mouse pointer, or -1 if not under the mouse pointer."""
    cursor_line = var(-1, always_update=True)
    """The line with the cursor, or -1 if no cursor."""
    show_guides = reactive(True)
    """Enable display of tree guide lines."""
    guide_depth = reactive(4, init=False)
    """The indent depth of tree nodes."""
    auto_expand = var(True)
    """Auto expand tree nodes when they are selected."""
    center_scroll = var(False)
    """Keep selected node in the center of the control, where possible."""

    LINES: dict[str, tuple[str, str, str, str]] = {
        "default": (
            "  ",
            "│ ",
            "└─",
            "├─",
        ),
        "bold": (
            "  ",
            "┃ ",
            "┗━",
            "┣━",
        ),
        "double": (
            "  ",
            "║ ",
            "╚═",
            "╠═",
        ),
    }

    class NodeCollapsed(Generic[EventTreeDataType], Message):
        """Event sent when a node is collapsed.

        Can be handled using `on_tree_node_collapsed` in a subclass of `Tree` or in a
        parent node in the DOM.
        """

        def __init__(self, node: TreeNode[EventTreeDataType]) -> None:
            self.node: TreeNode[EventTreeDataType] = node
            """The node that was collapsed."""
            super().__init__()

        @property
        def control(self) -> Tree[EventTreeDataType]:
            """The tree that sent the message."""
            return self.node.tree

    class NodeExpanded(Generic[EventTreeDataType], Message):
        """Event sent when a node is expanded.

        Can be handled using `on_tree_node_expanded` in a subclass of `Tree` or in a
        parent node in the DOM.
        """

        def __init__(self, node: TreeNode[EventTreeDataType]) -> None:
            self.node: TreeNode[EventTreeDataType] = node
            """The node that was expanded."""
            super().__init__()

        @property
        def control(self) -> Tree[EventTreeDataType]:
            """The tree that sent the message."""
            return self.node.tree

    class NodeHighlighted(Generic[EventTreeDataType], Message):
        """Event sent when a node is highlighted.

        Can be handled using `on_tree_node_highlighted` in a subclass of `Tree` or in a
        parent node in the DOM.
        """

        def __init__(self, node: TreeNode[EventTreeDataType]) -> None:
            self.node: TreeNode[EventTreeDataType] = node
            """The node that was highlighted."""
            super().__init__()

        @property
        def control(self) -> Tree[EventTreeDataType]:
            """The tree that sent the message."""
            return self.node.tree

    class NodeSelected(Generic[EventTreeDataType], Message):
        """Event sent when a node is selected.

        Can be handled using `on_tree_node_selected` in a subclass of `Tree` or in a
        parent node in the DOM.
        """

        def __init__(self, node: TreeNode[EventTreeDataType]) -> None:
            self.node: TreeNode[EventTreeDataType] = node
            """The node that was selected."""
            super().__init__()

        @property
        def control(self) -> Tree[EventTreeDataType]:
            """The tree that sent the message."""
            return self.node.tree

    def __init__(
        self,
        label: TextType,
        data: TreeDataType | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialise a Tree.

        Args:
            label: The label of the root node of the tree.
            data: The optional data to associate with the root node of the tree.
            name: The name of the Tree.
            id: The ID of the tree in the DOM.
            classes: The CSS classes of the tree.
            disabled: Whether the tree is disabled or not.
        """

        text_label = self.process_label(label)

        self._updates = 0
        self._tree_nodes: dict[NodeID, TreeNode[TreeDataType]] = {}
        self._current_id = 0
        self.root = self._add_node(None, text_label, data)
        """The root node of the tree."""
        self._line_cache: LRUCache[LineCacheKey, Strip] = LRUCache(1024)
        self._tree_lines_cached: list[_TreeLine[TreeDataType]] | None = None
        self._cursor_node: TreeNode[TreeDataType] | None = None

        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

    def add_json(self, json_data: object, node: TreeNode | None = None) -> None:
        """Adds JSON data to a node.

        Args:
            json_data: An object decoded from JSON.
            node: Node to add data to.

        """

        if node is None:
            node = self.root

        from rich.highlighter import ReprHighlighter

        highlighter = ReprHighlighter()

        def add_node(name: str, node: TreeNode, data: object) -> None:
            """Adds a node to the tree.

            Args:
                name: Name of the node.
                node: Parent node.
                data: Data associated with the node.
            """
            if isinstance(data, dict):
                node.set_label(Text(f"{{}} {name}"))
                for key, value in data.items():
                    new_node = node.add("")
                    add_node(key, new_node, value)
            elif isinstance(data, list):
                node.set_label(Text(f"[] {name}"))
                for index, value in enumerate(data):
                    new_node = node.add("")
                    add_node(str(index), new_node, value)
            else:
                node.allow_expand = False
                if name:
                    label = Text.assemble(
                        Text.from_markup(f"[b]{name}[/b]="), highlighter(repr(data))
                    )
                else:
                    label = Text(repr(data))
                node.set_label(label)

        add_node("", node, json_data)

    @property
    def cursor_node(self) -> TreeNode[TreeDataType] | None:
        """The currently selected node, or ``None`` if no selection."""
        return self._cursor_node

    @property
    def last_line(self) -> int:
        """The index of the last line."""
        return len(self._tree_lines) - 1

    def process_label(self, label: TextType) -> Text:
        """Process a `str` or `Text` value into a label.

        May be overridden in a subclass to change how labels are rendered.

        Args:
            label: Label.

        Returns:
            A Rich Text object.
        """
        if isinstance(label, str):
            text_label = Text.from_markup(label)
        else:
            text_label = label
        first_line = text_label.split()[0]
        return first_line

    def _add_node(
        self,
        parent: TreeNode[TreeDataType] | None,
        label: Text,
        data: TreeDataType | None,
        expand: bool = False,
    ) -> TreeNode[TreeDataType]:
        node = TreeNode(self, parent, self._new_id(), label, data, expanded=expand)
        self._tree_nodes[node._id] = node
        self._updates += 1
        return node

    def render_label(
        self, node: TreeNode[TreeDataType], base_style: Style, style: Style
    ) -> Text:
        """Render a label for the given node. Override this to modify how labels are rendered.

        Args:
            node: A tree node.
            base_style: The base style of the widget.
            style: The additional style for the label.

        Returns:
            A Rich Text object containing the label.
        """
        node_label = node._label.copy()
        node_label.stylize(style)

        if node._allow_expand:
            prefix = (
                self.ICON_NODE_EXPANDED if node.is_expanded else self.ICON_NODE,
                base_style + TOGGLE_STYLE,
            )
        else:
            prefix = ("", base_style)

        text = Text.assemble(prefix, node_label)
        return text

    def get_label_width(self, node: TreeNode[TreeDataType]) -> int:
        """Get the width of the nodes label.

        The default behavior is to call `render_label` and return the cell length. This method may be
        overridden in a sub-class if it can be done more efficiently.

        Args:
            node: A node.

        Returns:
            Width in cells.
        """
        label = self.render_label(node, NULL_STYLE, NULL_STYLE)
        return label.cell_len

    def _clear_line_cache(self) -> None:
        """Clear line cache."""
        self._line_cache.clear()
        self._tree_lines_cached = None

    def clear(self) -> Self:
        """Clear all nodes under root.

        Returns:
            The `Tree` instance.
        """
        self._clear_line_cache()
        self._current_id = 0
        root_label = self.root._label
        root_data = self.root.data
        root_expanded = self.root.is_expanded
        self.root = TreeNode(
            self,
            None,
            self._new_id(),
            root_label,
            root_data,
            expanded=root_expanded,
        )
        self._updates += 1
        self.refresh()
        return self

    def reset(self, label: TextType, data: TreeDataType | None = None) -> Self:
        """Clear the tree and reset the root node.

        Args:
            label: The label for the root node.
            data: Optional data for the root node.

        Returns:
            The `Tree` instance.
        """
        self.clear()
        self.root.label = label
        self.root.data = data
        return self

    def move_cursor(
        self, node: TreeNode[TreeDataType] | None, animate: bool = False
    ) -> None:
        """Move the cursor to the given node, or reset cursor.

        Args:
            node: A tree node, or None to reset cursor.
            animate: Enable animation
        """
        previous_cursor_line = self.cursor_line
        self.cursor_line = -1 if node is None else node._line
        if node is not None and self.cursor_node is not None:
            self.scroll_to_node(
                self.cursor_node,
                animate=animate and abs(self.cursor_line - previous_cursor_line) > 1,
            )

    def move_cursor_to_line(self, line: int, animate=False) -> None:
        """Move the cursor to the given line.

        Args:
            line: The line number (negative indexes are offsets from the last line).
            animate: Enable scrolling animation.

        Raises:
            IndexError: If the line doesn't exist.
        """
        if self.cursor_line == line:
            return
        try:
            node = self._tree_lines[line].node
        except IndexError:
            raise IndexError(f"No line no. {line} in the tree")
        self.move_cursor(node, animate=animate)

    def select_node(self, node: TreeNode[TreeDataType] | None) -> None:
        """Move the cursor to the given node and select it, or reset cursor.

        Args:
            node: A tree node to move the cursor to and select, or None to reset cursor.
        """
        self.move_cursor(node)
        if node is not None:
            self.post_message(Tree.NodeSelected(node))

    def unselect(self) -> None:
        """Hide and reset the cursor."""
        self.set_reactive(Tree.cursor_line, -1)
        self._invalidate()

    @on(NodeSelected)
    def _expand_node_on_select(self, event: NodeSelected[TreeDataType]) -> None:
        """When the node is selected, expand the node if `auto_expand` is True."""
        node = event.node
        if self.auto_expand:
            self._toggle_node(node)

    def get_node_at_line(self, line_no: int) -> TreeNode[TreeDataType] | None:
        """Get the node for a given line.

        Args:
            line_no: A line number.

        Returns:
            A tree node, or ``None`` if there is no node at that line.
        """
        try:
            line = self._tree_lines[line_no]
        except IndexError:
            return None
        else:
            return line.node

    def get_node_by_id(self, node_id: NodeID) -> TreeNode[TreeDataType]:
        """Get a tree node by its ID.

        Args:
            node_id: The ID of the node to get.

        Returns:
            The node associated with that ID.

        Raises:
            UnknownNodeID: Raised if the `TreeNode` ID is unknown.
        """
        try:
            return self._tree_nodes[node_id]
        except KeyError:
            raise UnknownNodeID(f"Unknown NodeID ({node_id}) in tree") from None

    def get_node_with_data(self, value: str | int, *keys) -> TreeNode[TreeDataType] | None:
        """Returns the first node that got a matching value in the json data field
        under the chain of *keys given.

        usage example: Tree.get_node_with_data(42, 'database', 'id')
        Args:
            value: str|int of the desired data in the data json
            *keys: chain of keys to the nested value

        Returns:
            The first Node with the desired value or None
        """
        for treeline in self._tree_lines:
            if treeline.node.data:
                data = treeline.node.data
                try:
                    for key in keys:
                        data = data[key]
                    if data == value:
                        return treeline.node
                except(KeyError, TypeError):
                    continue
        return None # if nothing was found

    def validate_cursor_line(self, value: int) -> int:
        """Prevent cursor line from going outside of range.

        Args:
            value: The value to test.

        Return:
            A valid version of the given value.
        """
        return clamp(value, 0, len(self._tree_lines) - 1)

    def validate_guide_depth(self, value: int) -> int:
        """Restrict guide depth to reasonable range.

        Args:
            value: The value to test.

        Return:
            A valid version of the given value.
        """
        return clamp(value, 2, 10)

    def _invalidate(self) -> None:
        """Invalidate caches."""
        self._clear_line_cache()
        self._updates += 1
        self.root._reset()
        self.refresh(layout=True)

    def _on_mouse_move(self, event: events.MouseMove) -> None:
        meta = event.style.meta
        if meta and "line" in meta:
            self.hover_line = meta["line"]
        else:
            self.hover_line = -1

    def _on_leave(self, _: events.Leave) -> None:
        # Ensure the hover effect doesn't linger after the mouse leaves.
        self.hover_line = -1

    def _new_id(self) -> NodeID:
        """Create a new node ID.

        Returns:
            A unique node ID.
        """
        id = self._current_id
        self._current_id += 1
        return NodeID(id)

    def _get_node(self, line: int) -> TreeNode[TreeDataType] | None:
        if line == -1:
            return None
        try:
            tree_line = self._tree_lines[line]
        except IndexError:
            return None
        else:
            return tree_line.node

    def _get_label_region(self, line: int) -> Region | None:
        """Returns the region occupied by the label of the node at line `line`.

        This can be used, e.g., when scrolling to that line such that the label
        is visible after the scroll.

        Args:
            line: A line number.

        Returns:
            The region occupied by the label, or `None` if the
            line is not in the tree.
        """
        try:
            tree_line = self._tree_lines[line]
        except IndexError:
            return None
        region_x = tree_line._get_guide_width(self.guide_depth, self.show_root)
        region_width = self.get_label_width(tree_line.node)
        return Region(region_x, line, region_width, 1)

    def watch_hover_line(self, previous_hover_line: int, hover_line: int) -> None:
        previous_node = self._get_node(previous_hover_line)
        if previous_node is not None:
            self._refresh_node(previous_node)
            previous_node._hover = False

        node = self._get_node(hover_line)
        if node is not None:
            self._refresh_node(node)
            node._hover = True

    def watch_cursor_line(self, previous_line: int, line: int) -> None:
        previous_node = self._get_node(previous_line)
        node = self._get_node(line)

        if self.cursor_node is not None:
            self.cursor_node._selected = False

        if previous_node is not None:
            previous_node._selected = False

        if node is not None:
            node._selected = True
            self._cursor_node = node
        else:
            self._cursor_node = None

        if previous_line == line:
            # No change, so no need for refresh
            return

        # Refresh previous cursor node
        if previous_node is not None:
            self._refresh_node(previous_node)

        # Refresh new node
        if node is not None:
            self._refresh_node(node)
            if previous_node != node:
                self.post_message(self.NodeHighlighted(node))

    def watch_guide_depth(self, guide_depth: int) -> None:
        self._invalidate()

    def watch_show_root(self, show_root: bool) -> None:
        self.cursor_line = -1
        self._invalidate()

    def scroll_to_line(self, line: int, animate: bool = True) -> None:
        """Scroll to the given line.

        Args:
            line: A line number.
            animate: Enable animation.
        """
        region = self._get_label_region(line)
        if region is not None:
            self.scroll_to_region(
                region,
                animate=animate,
                force=True,
                center=self.center_scroll,
                origin_visible=False,
                x_axis=False,  # Scrolling the X axis is quite jarring, and rarely necessary
            )

    def scroll_to_node(
        self, node: TreeNode[TreeDataType], animate: bool = True
    ) -> None:
        """Scroll to the given node.

        Args:
            node: Node to scroll into view.
            animate: Animate scrolling.
        """
        line = node._line
        if line != -1:
            self.scroll_to_line(line, animate=animate)

    def _refresh_line(self, line: int) -> None:
        """Refresh (repaint) a given line in the tree.

        Args:
            line: Line number.
        """
        region = Region(0, line - self.scroll_offset.y, self.size.width, 1)
        self.refresh(region)

    def _refresh_node_line(self, line: int) -> None:
        node = self._get_node(line)
        if node is not None:
            self._refresh_node(node)

    def _refresh_node(self, node: TreeNode[TreeDataType]) -> None:
        """Refresh a node and all its children.

        Args:
            node: A tree node.
        """
        scroll_y = self.scroll_offset.y
        height = self.size.height
        visible_lines = self._tree_lines[scroll_y : scroll_y + height]
        for line_no, line in enumerate(visible_lines, scroll_y):
            if node in line.path:
                self._refresh_line(line_no)

    @property
    def _tree_lines(self) -> list[_TreeLine[TreeDataType]]:
        if self._tree_lines_cached is None:
            self._build()
        assert self._tree_lines_cached is not None
        return self._tree_lines_cached

    async def _on_idle(self, event: events.Idle) -> None:
        """Check tree needs a rebuild on idle."""
        # Property calls build if required
        async with self.lock:
            self._tree_lines

    def _build(self) -> None:
        """Builds the tree by traversing nodes, and creating tree lines."""

        TreeLine = _TreeLine
        lines: list[_TreeLine[TreeDataType]] = []
        add_line = lines.append

        root = self.root

        def add_node(
            path: list[TreeNode[TreeDataType]], node: TreeNode[TreeDataType], last: bool
        ) -> None:
            child_path = [*path, node]
            node._line = len(lines)
            add_line(TreeLine(child_path, last))
            if node._expanded:
                for last, child in loop_last(node._children):
                    add_node(child_path, child, last)

        if self.show_root:
            add_node([], root, True)
        else:
            for node in self.root._children:
                add_node([], node, True)
        self._tree_lines_cached = lines

        guide_depth = self.guide_depth
        show_root = self.show_root
        get_label_width = self.get_label_width

        def get_line_width(line: _TreeLine[TreeDataType]) -> int:
            return get_label_width(line.node) + line._get_guide_width(
                guide_depth, show_root
            )

        if lines:
            width = max([get_line_width(line) for line in lines])
        else:
            width = self.size.width

        self.virtual_size = Size(width, len(lines))
        if self.cursor_line != -1:
            if self.cursor_node is not None:
                self.cursor_line = self.cursor_node._line
            if self.cursor_line >= len(lines):
                self.cursor_line = -1

    def render_lines(self, crop: Region) -> list[Strip]:
        self._pseudo_class_state = self.get_pseudo_class_state()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        scroll_x, scroll_y = self.scroll_offset
        style = self.rich_style
        return self._render_line(
            y + scroll_y,
            scroll_x,
            scroll_x + width,
            style,
        )

    def _render_line(self, y: int, x1: int, x2: int, base_style: Style) -> Strip:
        tree_lines = self._tree_lines
        width = self.size.width

        if y >= len(tree_lines):
            return Strip.blank(width, base_style)

        line = tree_lines[y]

        is_hover = self.hover_line >= 0 and any(node._hover for node in line.path)

        cache_key = (
            y,
            is_hover,
            width,
            self._updates,
            self._pseudo_class_state,
            tuple(node._updates for node in line.path),
        )
        if cache_key in self._line_cache:
            strip = self._line_cache[cache_key]
        else:
            # Allow tree guides to be explicitly disabled by setting color to transparent
            base_hidden = self.get_component_styles("tree--guides").color.a == 0
            hover_hidden = self.get_component_styles("tree--guides-hover").color.a == 0
            selected_hidden = (
                self.get_component_styles("tree--guides-selected").color.a == 0
            )

            base_guide_style = self.get_component_rich_style(
                "tree--guides", partial=True
            )
            guide_hover_style = base_guide_style + self.get_component_rich_style(
                "tree--guides-hover", partial=True
            )
            guide_selected_style = base_guide_style + self.get_component_rich_style(
                "tree--guides-selected", partial=True
            )

            hover = line.path[0]._hover
            selected = line.path[0]._selected and self.has_focus

            def get_guides(style: Style, hidden: bool) -> tuple[str, str, str, str]:
                """Get the guide strings for a given style.

                Args:
                    style: A Style object.
                    hidden: Switch to hide guides (make them invisible).

                Returns:
                    Strings for space, vertical, terminator and cross.
                """
                lines: tuple[Iterable[str], Iterable[str], Iterable[str], Iterable[str]]
                if self.show_guides and not hidden:
                    lines = self.LINES["default"]
                    if style.bold:
                        lines = self.LINES["bold"]
                    elif style.underline2:
                        lines = self.LINES["double"]
                else:
                    lines = ("  ", "  ", "  ", "  ")

                guide_depth = max(0, self.guide_depth - 2)
                guide_lines = tuple(
                    f"{characters[0]}{characters[1] * guide_depth} "
                    for characters in lines
                )
                return cast("tuple[str, str, str, str]", guide_lines)

            if is_hover:
                line_style = self.get_component_rich_style("tree--highlight-line")
            else:
                line_style = base_style

            line_style += Style(meta={"line": y})

            guides = Text(style=line_style)
            guides_append = guides.append

            guide_style = base_guide_style

            hidden = True
            for node in line.path[1:]:
                hidden = base_hidden
                if hover:
                    guide_style = guide_hover_style
                    hidden = hover_hidden
                if selected:
                    guide_style = guide_selected_style
                    hidden = selected_hidden

                space, vertical, _, _ = get_guides(guide_style, hidden)
                guide = space if node.is_last else vertical
                if node != line.path[-1]:
                    guides_append(guide, style=guide_style)
                hover = hover or node._hover
                selected = (selected or node._selected) and self.has_focus

            if len(line.path) > 1:
                _, _, terminator, cross = get_guides(guide_style, hidden)
                if line.last:
                    guides.append(terminator, style=guide_style)
                else:
                    guides.append(cross, style=guide_style)

            label_style = self.get_component_rich_style("tree--label", partial=True)
            if self.hover_line == y:
                label_style += self.get_component_rich_style(
                    "tree--highlight", partial=True
                )
            if self.cursor_line == y:
                label_style += self.get_component_rich_style(
                    "tree--cursor", partial=False
                )

            label = self.render_label(line.path[-1], line_style, label_style).copy()
            label.stylize(Style(meta={"node": line.node._id}))
            guides.append(label)

            segments = list(guides.render(self.app.console))
            pad_width = max(self.virtual_size.width, width)
            segments = line_pad(segments, 0, pad_width - guides.cell_len, line_style)
            strip = self._line_cache[cache_key] = Strip(segments)

        strip = strip.crop(x1, x2)
        return strip

    def _on_resize(self, event: events.Resize) -> None:
        self._line_cache.grow(event.size.height)
        self._invalidate()

    def _toggle_node(self, node: TreeNode[TreeDataType]) -> None:
        if not node.allow_expand:
            return
        if node.is_expanded:
            node.collapse()
        else:
            node.expand()

    async def _on_click(self, event: events.Click) -> None:
        async with self.lock:
            meta = event.style.meta
            if "line" in meta:
                cursor_line = meta["line"]
                if meta.get("toggle", False):
                    node = self.get_node_at_line(cursor_line)
                    if node is not None:
                        self._toggle_node(node)

                else:
                    self.cursor_line = cursor_line
                    await self.run_action("select_cursor")

    def notify_style_update(self) -> None:
        super().notify_style_update()
        self._invalidate()

    def action_cursor_up(self) -> None:
        """Move the cursor up one node."""
        if self.cursor_line == -1:
            self.cursor_line = self.last_line
        else:
            self.cursor_line -= 1
        self.scroll_to_line(self.cursor_line, animate=False)

    def action_cursor_down(self) -> None:
        """Move the cursor down one node."""
        if self.cursor_line == -1:
            self.cursor_line = 0
        else:
            self.cursor_line += 1
        self.scroll_to_line(self.cursor_line, animate=False)

    def action_page_down(self) -> None:
        """Move the cursor down a page's-worth of nodes."""
        if self.cursor_line == -1:
            self.cursor_line = 0
        self.cursor_line += self.scrollable_content_region.height - 1
        self.scroll_to_line(self.cursor_line)

    def action_page_up(self) -> None:
        """Move the cursor up a page's-worth of nodes."""
        if self.cursor_line == -1:
            self.cursor_line = self.last_line
        self.cursor_line -= self.scrollable_content_region.height - 1
        self.scroll_to_line(self.cursor_line)

    def action_scroll_home(self) -> None:
        """Move the cursor to the top of the tree."""
        self.cursor_line = 0
        self.scroll_to_line(self.cursor_line)

    def action_scroll_end(self) -> None:
        """Move the cursor to the bottom of the tree.

        Note:
            Here bottom means vertically, not branch depth.
        """
        self.cursor_line = self.last_line
        self.scroll_to_line(self.cursor_line)

    def action_toggle_node(self) -> None:
        """Toggle the expanded state of the target node."""
        try:
            line = self._tree_lines[self.cursor_line]
        except IndexError:
            pass
        else:
            self._toggle_node(line.path[-1])

    def action_select_cursor(self) -> None:
        """Cause a select event for the target node.

        Note:
            If `auto_expand` is `True` use of this action on a non-leaf node
            will cause both an expand/collapse event to occur, as well as a
            selected event.
        """
        if self.cursor_line < 0:
            return
        try:
            line = self._tree_lines[self.cursor_line]
        except IndexError:
            pass
        else:
            node = line.path[-1]
            self.post_message(Tree.NodeSelected(node))

    def action_cursor_parent(self) -> None:
        """Move the cursor to the parent node."""
        cursor_node = self.cursor_node
        if cursor_node is not None and cursor_node.parent is not None:
            self.move_cursor(cursor_node.parent, animate=True)

    def action_cursor_parent_next_sibling(self) -> None:
        """Move the cursor to the parent's next sibling."""
        cursor_node = self.cursor_node
        if cursor_node is not None and cursor_node.parent is not None:
            self.move_cursor(cursor_node.parent.next_sibling, animate=True)

    def action_cursor_previous_sibling(self) -> None:
        """Move the cursor to previous sibling, or to the parent if there are no more siblings."""
        cursor_node = self.cursor_node
        if cursor_node is not None:
            previous_sibling = cursor_node.previous_sibling
            if previous_sibling is None:
                self.move_cursor(cursor_node.parent, animate=True)
            else:
                self.move_cursor(previous_sibling, animate=True)

    def action_cursor_next_sibling(self) -> None:
        """Move the cursor to the next sibling, or to the paren't sibling if there are no more siblings."""
        cursor_node = self.cursor_node
        if cursor_node is not None:
            next_sibling = cursor_node.next_sibling
            if next_sibling is None:
                if cursor_node.parent is not None:
                    parent_sibling = cursor_node.parent.next_sibling
                    self.move_cursor(parent_sibling, animate=True)
            else:
                self.move_cursor(next_sibling, animate=True)

    def action_toggle_expand_all(self) -> None:
        """Expand or collapse all siblings.

        If all the siblings are collapsed then they will be expanded.
        Otherwise they will all be collapsed.

        """

        if self.cursor_node is None or self.cursor_node.parent is None:
            return

        siblings = self.cursor_node.siblings
        cursor_node = self.cursor_node

        # If all siblings are collapsed we want to expand them all
        if all(child.is_collapsed for child in siblings):
            for child in siblings:
                if child.allow_expand:
                    child.expand()
        # Otherwise we want to collapse them all
        else:
            for child in siblings:
                if child.allow_expand:
                    child.collapse()

        self.call_after_refresh(self.move_cursor, cursor_node, animate=False)
