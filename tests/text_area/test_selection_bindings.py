import pytest

from textual.app import App, ComposeResult
from textual.geometry import Offset
from textual.widgets import TextArea
from textual.widgets.text_area import Selection

TEXT = """I must not fear.
Fear is the mind-killer.
Fear is the little-death that brings total obliteration.
I will face my fear.
"""


class TextAreaApp(App):
    def __init__(self, read_only: bool = False):
        super().__init__()
        self.read_only = read_only

    def compose(self) -> ComposeResult:
        yield TextArea(TEXT, show_line_numbers=True, read_only=self.read_only)


@pytest.fixture(params=[True, False])
async def app(request):
    """Each test that receives an `app` will execute twice.
    Once with read_only=True, and once with read_only=False.
    """
    return TextAreaApp(read_only=request.param)


async def test_mouse_click(app: TextAreaApp):
    """When you click the TextArea, the cursor moves to the expected location."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        await pilot.click(TextArea, Offset(x=5, y=2))
        assert text_area.selection == Selection.cursor((1, 0))


async def test_mouse_click_clamp_from_right(app: TextAreaApp):
    """When you click to the right of the document bounds, the cursor is clamped
    to within the document bounds."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        await pilot.click(TextArea, Offset(x=8, y=20))
        assert text_area.selection == Selection.cursor((4, 0))


async def test_mouse_click_gutter_clamp(app: TextAreaApp):
    """When you click the gutter, it selects the start of the line."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        await pilot.click(TextArea, Offset(x=0, y=3))
        assert text_area.selection == Selection.cursor((2, 0))


async def test_cursor_movement_basic():
    app = TextAreaApp()
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("01234567\n012345\n0123456789")

        await pilot.press("right")
        assert text_area.selection == Selection.cursor((0, 1))

        await pilot.press("down")
        assert text_area.selection == Selection.cursor((1, 1))

        await pilot.press("left")
        assert text_area.selection == Selection.cursor((1, 0))

        await pilot.press("up")
        assert text_area.selection == Selection.cursor((0, 0))


async def test_cursor_selection_right(app: TextAreaApp):
    """When you press shift+right the selection is updated correctly."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        await pilot.press(*["shift+right"] * 3)
        assert text_area.selection == Selection((0, 0), (0, 3))


async def test_cursor_selection_right_to_previous_line(app: TextAreaApp):
    """When you press shift+right resulting in the cursor moving to the next line,
    the selection is updated correctly."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.selection = Selection.cursor((0, 15))
        await pilot.press(*["shift+right"] * 4)
        assert text_area.selection == Selection((0, 15), (1, 2))


async def test_cursor_selection_left(app: TextAreaApp):
    """When you press shift+left the selection is updated correctly."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.selection = Selection.cursor((2, 5))
        await pilot.press(*["shift+left"] * 3)
        assert text_area.selection == Selection((2, 5), (2, 2))


async def test_cursor_selection_left_to_previous_line(app: TextAreaApp):
    """When you press shift+left resulting in the cursor moving back to the previous line,
    the selection is updated correctly."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.selection = Selection.cursor((2, 2))
        await pilot.press(*["shift+left"] * 3)

        # The cursor jumps up to the end of the line above.
        end_of_previous_line = len(TEXT.splitlines()[1])
        assert text_area.selection == Selection((2, 2), (1, end_of_previous_line))


async def test_cursor_selection_up(app: TextAreaApp):
    """When you press shift+up the selection is updated correctly."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.move_cursor((2, 3))

        await pilot.press("shift+up")
        assert text_area.selection == Selection((2, 3), (1, 3))


async def test_cursor_selection_up_when_cursor_on_first_line(app: TextAreaApp):
    """When you press shift+up the on the first line, it selects to the start."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.move_cursor((0, 4))

        await pilot.press("shift+up")
        assert text_area.selection == Selection((0, 4), (0, 0))
        await pilot.press("shift+up")
        assert text_area.selection == Selection((0, 4), (0, 0))


async def test_cursor_selection_down(app: TextAreaApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.move_cursor((2, 5))

        await pilot.press("shift+down")
        assert text_area.selection == Selection((2, 5), (3, 5))


async def test_cursor_selection_down_when_cursor_on_last_line(app: TextAreaApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("ABCDEF\nGHIJK")
        text_area.move_cursor((1, 2))

        await pilot.press("shift+down")
        assert text_area.selection == Selection((1, 2), (1, 5))
        await pilot.press("shift+down")
        assert text_area.selection == Selection((1, 2), (1, 5))


async def test_cursor_word_right(app: TextAreaApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("ABC DEF\nGHIJK")

        await pilot.press("ctrl+right")

        assert text_area.selection == Selection.cursor((0, 3))


async def test_cursor_word_right_select(app: TextAreaApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("ABC DEF\nGHIJK")

        await pilot.press("ctrl+shift+right")

        assert text_area.selection == Selection((0, 0), (0, 3))


async def test_cursor_word_left(app: TextAreaApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("ABC DEF\nGHIJK")
        text_area.move_cursor((0, 7))

        await pilot.press("ctrl+left")

        assert text_area.selection == Selection.cursor((0, 4))


async def test_cursor_word_left_select(app: TextAreaApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("ABC DEF\nGHIJK")
        text_area.move_cursor((0, 7))

        await pilot.press("ctrl+shift+left")

        assert text_area.selection == Selection((0, 7), (0, 4))


@pytest.mark.parametrize("key", ["end", "ctrl+e"])
async def test_cursor_to_line_end(key, app: TextAreaApp):
    """You can use the keyboard to jump the cursor to the end of the current line."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.selection = Selection.cursor((2, 2))
        await pilot.press(key)
        eol_index = len(TEXT.splitlines()[2])
        assert text_area.cursor_location == (2, eol_index)
        assert text_area.selection.is_empty


@pytest.mark.parametrize("key", ["home", "ctrl+a"])
async def test_cursor_to_line_home_basic_behaviour(key, app: TextAreaApp):
    """You can use the keyboard to jump the cursor to the start of the current line."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.selection = Selection.cursor((2, 2))
        await pilot.press(key)
        assert text_area.cursor_location == (2, 0)
        assert text_area.selection.is_empty


@pytest.mark.parametrize(
    "cursor_start,cursor_destination",
    [
        ((0, 0), (0, 4)),
        ((0, 2), (0, 0)),
        ((0, 4), (0, 0)),
        ((0, 5), (0, 4)),
        ((0, 9), (0, 4)),
        ((0, 15), (0, 4)),
    ],
)
async def test_cursor_line_home_smart_home(
    cursor_start, cursor_destination, app: TextAreaApp
):
    """If the line begins with whitespace, pressing home firstly goes
    to the start of the (non-whitespace) content. Pressing it again takes you to column
    0. If you press it again, it goes back to the first non-whitespace column."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("    hello world")
        text_area.move_cursor(cursor_start)
        await pilot.press("home")
        assert text_area.selection == Selection.cursor(cursor_destination)


async def test_cursor_page_down(app: TextAreaApp):
    """Pagedown moves the cursor down 1 page, retaining column index."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("XXX\n" * 200)
        text_area.selection = Selection.cursor((0, 1))
        await pilot.press("pagedown")
        margin = 2
        assert text_area.selection == Selection.cursor(
            (app.size.height - margin, 1)
        )


async def test_cursor_page_up(app: TextAreaApp):
    """Pageup moves the cursor up 1 page, retaining column index."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.load_text("XXX\n" * 200)
        text_area.selection = Selection.cursor((100, 1))
        await pilot.press("pageup")
        margin = 2
        assert text_area.selection == Selection.cursor(
            (100 - app.size.height + margin, 1)
        )


async def test_cursor_vertical_movement_visual_alignment_snapping(app: TextAreaApp):
    """When you move the cursor vertically, it should stay vertically
    aligned even when double-width characters are used."""
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.text = "こんにちは\n012345"
        text_area.move_cursor((1, 3), record_width=True)

        # The '3' is aligned with ん at (0, 1)
        # こんにちは
        # 012345
        # Pressing `up` takes us from (1, 3) to (0, 1) because record_width=True.
        await pilot.press("up")
        assert text_area.selection == Selection.cursor((0, 1))

        # Pressing `down` takes us from (0, 1) to (1, 3)
        await pilot.press("down")
        assert text_area.selection == Selection.cursor((1, 3))


async def test_select_line_binding(app: TextAreaApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)
        text_area.move_cursor((2, 2))

        await pilot.press("f6")

        assert text_area.selection == Selection((2, 0), (2, 56))


async def test_select_all_binding(app: TextAreaApp):
    async with app.run_test() as pilot:
        text_area = app.query_one(TextArea)

        await pilot.press("f7")

        assert text_area.selection == Selection((0, 0), (4, 0))
