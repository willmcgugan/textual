from __future__ import annotations

from typing import ClassVar, Generic, Iterable, Optional, TypeVar

from typing_extensions import TypeGuard

from textual._loop import loop_from_index
from textual.await_complete import AwaitComplete
from textual.await_remove import AwaitRemove
from textual.binding import Binding, BindingType
from textual.containers import VerticalScroll
from textual.events import Mount
from textual.message import Message
from textual.reactive import reactive
from textual.widget import AwaitMount
from textual.widgets._list_item import ListItem

ListItemType = TypeVar("ListItemType", bound=ListItem)
"""The type of the ListItem for a given instance of a [ListView][textual.widgets.ListView]."""

EventListItemType = TypeVar("EventListItemType", bound=ListItem)
"""The type of the ListItem for a given instance of a [ListView][textual.widgets.ListView].

Similar to [ListItemType][textual.widgets._list_view.ListItemType] but used for
``ListView`` messages."""


class ListView(
    Generic[ListItemType], VerticalScroll, can_focus=True, can_focus_children=False
):
    """A vertical list view widget.

    Displays a vertical list of `ListItem`s which can be highlighted and
    selected using the mouse or keyboard.

    Attributes:
        index: The index in the list that's currently highlighted.
    """

    ALLOW_MAXIMIZE = True

    DEFAULT_CSS = """
    ListView {
        background: $surface;
        & > ListItem {
            color: $foreground;
            height: auto;
            overflow: hidden hidden;
            width: 1fr;

            &.-hovered {
                background: $block-hover-background;
            }
            
            &.-highlight {
                color: $block-cursor-blurred-foreground;
                background: $block-cursor-blurred-background;
                text-style: $block-cursor-blurred-text-style;
            }
        }

        &:focus {
            background-tint: $foreground 5%;
            & > ListItem.-highlight {
                color: $block-cursor-foreground;
                background: $block-cursor-background;
                text-style: $block-cursor-text-style;
            }
        }

    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "select_cursor", "Select", show=False),
        Binding("up", "cursor_up", "Cursor up", show=False),
        Binding("down", "cursor_down", "Cursor down", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | enter | Select the current item. |
    | up | Move the cursor up. |
    | down | Move the cursor down. |
    """

    index = reactive[Optional[int]](None, init=False)
    """The index of the currently highlighted item."""

    class Highlighted(Generic[EventListItemType], Message):
        """Posted when the highlighted item changes.

        Highlighted item is controlled using up/down keys.
        Can be handled using `on_list_view_highlighted` in a subclass of `ListView`
        or in a parent widget in the DOM.
        """

        ALLOW_SELECTOR_MATCH = {"item"}
        """Additional message attributes that can be used with the [`on` decorator][textual.on]."""

        def __init__(self, list_view: ListView, item: EventListItemType | None) -> None:
            super().__init__()
            self.list_view: ListView = list_view
            """The view that contains the item highlighted."""
            self.item: EventListItemType | None = item
            """The highlighted item, if there is one highlighted."""

        @property
        def control(self) -> ListView[EventListItemType]:
            """The view that contains the item highlighted.

            This is an alias for [`Highlighted.list_view`][textual.widgets.ListView.Highlighted.list_view]
            and is used by the [`on`][textual.on] decorator.
            """
            return self.list_view

    class Selected(Generic[EventListItemType], Message):
        """Posted when a list item is selected, e.g. when you press the enter key on it.

        Can be handled using `on_list_view_selected` in a subclass of `ListView` or in
        a parent widget in the DOM.
        """

        ALLOW_SELECTOR_MATCH = {"item"}
        """Additional message attributes that can be used with the [`on` decorator][textual.on]."""

        def __init__(self, list_view: ListView, item: EventListItemType) -> None:
            super().__init__()
            self.list_view: ListView = list_view
            """The view that contains the item selected."""
            self.item: EventListItemType = item
            """The selected item."""

        @property
        def control(self) -> ListView[EventListItemType]:
            """The view that contains the item selected.

            This is an alias for [`Selected.list_view`][textual.widgets.ListView.Selected.list_view]
            and is used by the [`on`][textual.on] decorator.
            """
            return self.list_view

    def __init__(
        self,
        *children: ListItemType,
        initial_index: int | None = 0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """
        Initialize a ListView.

        Args:
            *children: The ListItems to display in the list.
            initial_index: The index that should be highlighted when the list is first mounted.
            name: The name of the widget.
            id: The unique ID of the widget used in CSS/query selection.
            classes: The CSS classes of the widget.
            disabled: Whether the ListView is disabled or not.
        """
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )
        self._initial_index = initial_index

    def _on_mount(self, _: Mount) -> None:
        """Ensure the ListView is fully-settled after mounting."""

        if self._initial_index is not None and self.children:
            index = self._initial_index
            if index >= len(self.children):
                index = 0
            if self._nodes[index].disabled:
                for index, node in loop_from_index(self._nodes, index, wrap=True):
                    if not node.disabled:
                        break
            self.index = index

    @property
    def highlighted_child(self) -> ListItemType | None:
        """The currently highlighted ListItem, or None if nothing is highlighted."""
        if self.index is not None and 0 <= self.index < len(self._nodes):
            list_item = self._nodes[self.index]
            assert isinstance(list_item, ListItem)
            return list_item
        else:
            return None

    def validate_index(self, index: int | None) -> int | None:
        """Clamp the index to the valid range, or set to None if there's nothing to highlight.

        Args:
            index: The index to clamp.

        Returns:
            The clamped index.
        """
        if index is None or not self._nodes:
            return None
        elif index < 0:
            return 0
        elif index >= len(self._nodes):
            return len(self._nodes) - 1

        return index

    def _is_valid_index(self, index: int | None) -> TypeGuard[int]:
        """Determine whether the current index is valid into the list of children."""
        if index is None:
            return False
        return 0 <= index < len(self._nodes)

    def watch_index(self, old_index: int | None, new_index: int | None) -> None:
        """Updates the highlighting when the index changes."""

        if new_index is not None:
            selected_widget = self._nodes[new_index]
            if selected_widget.region:
                self.scroll_to_widget(self._nodes[new_index], animate=False)
            else:
                # Call after refresh to permit a refresh operation
                self.call_after_refresh(
                    self.scroll_to_widget, selected_widget, animate=False
                )

        if self._is_valid_index(old_index):
            old_child = self._nodes[old_index]
            assert isinstance(old_child, ListItem)
            old_child.highlighted = False

        if (
            new_index is not None
            and self._is_valid_index(new_index)
            and not self._nodes[new_index].disabled
        ):
            new_child = self._nodes[new_index]
            assert isinstance(new_child, ListItem)
            new_child.highlighted = True
            self.post_message(self.Highlighted(self, new_child))
        else:
            self.post_message(self.Highlighted(self, None))

    def extend(self, items: Iterable[ListItemType]) -> AwaitMount:
        """Append multiple new ListItems to the end of the ListView.

        Args:
            items: The ListItems to append.

        Returns:
            An awaitable that yields control to the event loop
                until the DOM has been updated with the new child items.
        """
        await_mount = self.mount(*items)
        return await_mount

    def append(self, item: ListItemType) -> AwaitMount:
        """Append a new ListItem to the end of the ListView.

        Args:
            item: The ListItem to append.

        Returns:
            An awaitable that yields control to the event loop
                until the DOM has been updated with the new child item.
        """
        return self.extend([item])

    def clear(self) -> AwaitRemove:
        """Clear all items from the ListView.

        Returns:
            An awaitable that yields control to the event loop until
                the DOM has been updated to reflect all children being removed.
        """
        await_remove = self.query("ListView > ListItem").remove()
        self.index = None
        return await_remove

    def insert(self, index: int, items: Iterable[ListItem]) -> AwaitMount:
        """Insert new ListItem(s) to specified index.

        Args:
            index: index to insert new ListItem.
            items: The ListItems to insert.

        Returns:
            An awaitable that yields control to the event loop
                until the DOM has been updated with the new child item.
        """
        await_mount = self.mount(*items, before=index)
        return await_mount

    def pop(self, index: Optional[int] = None) -> AwaitComplete:
        """Remove last ListItem from ListView or
           Remove ListItem from ListView by index

        Args:
            index: index of ListItem to remove from ListView

        Returns:
            An awaitable that yields control to the event loop until
                the DOM has been updated to reflect item being removed.
        """
        if len(self) == 0:
            raise IndexError("pop from empty list")

        index = index if index is not None else -1
        item_to_remove = self.query("ListItem")[index]
        normalized_index = index if index >= 0 else index + len(self)

        async def do_pop() -> None:
            """Remove the item and update the highlighted index."""
            await item_to_remove.remove()
            if self.index is not None:
                if normalized_index < self.index:
                    self.index -= 1
                elif normalized_index == self.index:
                    old_index = self.index
                    # Force a re-validation of the index
                    self.index = self.index
                    # If the index hasn't changed, the watcher won't be called
                    # but we need to update the highlighted item
                    if old_index == self.index:
                        self.watch_index(old_index, self.index)

        return AwaitComplete(do_pop())

    def remove_items(self, indices: Iterable[int]) -> AwaitComplete:
        """Remove ListItems from ListView by indices

        Args:
            indices: index(s) of ListItems to remove from ListView

        Returns:
            An awaitable object that waits for the direct children to be removed.
        """
        items = self.query("ListItem")
        items_to_remove = [items[index] for index in indices]
        normalized_indices = set(
            index if index >= 0 else index + len(self) for index in indices
        )

        async def do_remove_items() -> None:
            """Remove the items and update the highlighted index."""
            await self.remove_children(items_to_remove)
            if self.index is not None:
                removed_before_highlighted = sum(
                    1 for index in normalized_indices if index < self.index
                )
                if removed_before_highlighted:
                    self.index -= removed_before_highlighted
                elif self.index in normalized_indices:
                    old_index = self.index
                    # Force a re-validation of the index
                    self.index = self.index
                    # If the index hasn't changed, the watcher won't be called
                    # but we need to update the highlighted item
                    if old_index == self.index:
                        self.watch_index(old_index, self.index)

        return AwaitComplete(do_remove_items())

    def action_select_cursor(self) -> None:
        """Select the current item in the list."""
        selected_child = self.highlighted_child
        if selected_child is None:
            return
        self.post_message(self.Selected(self, selected_child))

    def action_cursor_down(self) -> None:
        """Highlight the next item in the list."""
        if self.index is None:
            if self._nodes:
                self.index = 0
        else:
            index = self.index
            for index, item in loop_from_index(self._nodes, self.index, wrap=False):
                if not item.disabled:
                    self.index = index
                    break

    def action_cursor_up(self) -> None:
        """Highlight the previous item in the list."""
        if self.index is None:
            if self._nodes:
                self.index = len(self._nodes) - 1
        else:
            for index, item in loop_from_index(
                self._nodes, self.index, direction=-1, wrap=False
            ):
                if not item.disabled:
                    self.index = index
                    break

    def _on_list_item__child_clicked(self, event: ListItem._ChildClicked) -> None:
        event.stop()
        self.focus()
        self.index = self._nodes.index(event.item)
        self.post_message(self.Selected(self, event.item))

    def __len__(self) -> int:
        """Compute the length (in number of items) of the list view."""
        return len(self._nodes)
