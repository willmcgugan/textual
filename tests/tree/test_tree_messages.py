from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import Tree
from textual.message import Message


class TreeApp(App[None]):
    """Test tree app."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.messages: list[str] = []

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        yield Tree[None]("Root")

    def on_mount(self) -> None:
        """"""
        self.query_one(Tree[None]).root.add("Child")
        self.query_one(Tree[None]).focus()

    def record(self, event: Message) -> None:
        self.messages.append(event.__class__.__name__)

    def on_tree_node_selected(self, event: Tree.NodeSelected[None]) -> None:
        self.record(event)

    def on_tree_node_expanded(self, event: Tree.NodeExpanded[None]) -> None:
        self.record(event)

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed[None]) -> None:
        self.record(event)


async def test_tree_node_selected_message() -> None:
    """Selecting a node should result in a selected message being emitted."""
    async with TreeApp().run_test() as pilot:
        await pilot.press("enter")
        assert pilot.app.messages[-1] == "NodeSelected"


async def test_tree_node_expanded_message() -> None:
    """Expanding a node should result in an expanded message being emitted."""
    async with TreeApp().run_test() as pilot:
        await pilot.press("enter")
        assert pilot.app.messages[0] == "NodeExpanded"


async def test_tree_node_collapsed_message() -> None:
    """Collapsing a node should result in a collapsed message being emitted."""
    async with TreeApp().run_test() as pilot:
        await pilot.press("enter", "enter")
        assert pilot.app.messages[-2] == "NodeCollapsed"
