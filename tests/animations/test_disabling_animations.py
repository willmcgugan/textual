"""
Test that generic animations can be disabled.
"""

from textual.app import App, ComposeResult
from textual.color import Color
from textual.widgets import Label


class SingleLabelApp(App[None]):
    """Single label whose background colour we'll animate."""

    CSS = """
        Label {
            background: red;
        }
    """

    def compose(self) -> ComposeResult:
        yield Label()


async def test_style_animations_via_animate_work_on_full() -> None:
    app = SingleLabelApp()
    app.animation_level = "full"

    async with app.run_test() as pilot:
        label = app.query_one(Label)
        # Sanity check.
        assert label.styles.background == Color.parse("red")
        # Test.
        animator = app.animator
        # Freeze time at 0 before triggering the animation.
        animator._get_time = lambda *_: 0
        label.styles.animate("background", "blue", duration=1)
        await pilot.pause()
        # Freeze time after the animation start and before animation end.
        animator._get_time = lambda *_: 0.01
        # Move to the next frame.
        await animator()
        assert label.styles.background != Color.parse("blue")


async def test_style_animations_via_animate_are_disabled_on_basic() -> None:
    app = SingleLabelApp()
    app.animation_level = "basic"

    async with app.run_test() as pilot:
        label = app.query_one(Label)
        # Sanity check.
        assert label.styles.background == Color.parse("red")
        # Test.
        animator = app.animator
        # Freeze time at 0 before triggering the animation.
        animator._get_time = lambda *_: 0
        label.styles.animate("background", "blue", duration=1)
        await pilot.pause()
        # Freeze time after the animation start and before animation end.
        animator._get_time = lambda *_: 0.01
        # Move to the next frame.
        await animator()
        assert label.styles.background == Color.parse("blue")


async def test_style_animations_via_animate_are_disabled_on_none() -> None:
    app = SingleLabelApp()
    app.animation_level = "none"

    async with app.run_test() as pilot:
        label = app.query_one(Label)
        # Sanity check.
        assert label.styles.background == Color.parse("red")
        # Test.
        animator = app.animator
        # Freeze time at 0 before triggering the animation.
        animator._get_time = lambda *_: 0
        label.styles.animate("background", "blue", duration=1)
        await pilot.pause()
        # Freeze time after the animation start and before animation end.
        animator._get_time = lambda *_: 0.01
        # Move to the next frame.
        await animator()
        assert label.styles.background == Color.parse("blue")


class LabelWithTransitionsApp(App[None]):
    """Single label whose background is set to animate with TCSS."""

    CSS = """
        Label {
            background: red;
            transition: background 1s;
        }

        Label.blue-bg {
            background: blue;
        }
    """

    def compose(self) -> ComposeResult:
        yield Label()


async def test_style_animations_via_transition_work_on_full() -> None:
    app = LabelWithTransitionsApp()
    app.animation_level = "full"

    async with app.run_test() as pilot:
        label = app.query_one(Label)
        # Sanity check.
        assert label.styles.background == Color.parse("red")
        # Test.
        label.add_class("blue-bg")
        await pilot.pause()
        assert label.styles.background != Color.parse("blue")


async def test_style_animations_via_transition_are_disabled_on_basic() -> None:
    app = LabelWithTransitionsApp()
    app.animation_level = "basic"

    async with app.run_test() as pilot:
        label = app.query_one(Label)
        # Sanity check.
        assert label.styles.background == Color.parse("red")
        # Test.
        label.add_class("blue-bg")
        await pilot.pause()
        assert label.styles.background == Color.parse("blue")


async def test_style_animations_via_transition_are_disabled_on_none() -> None:
    app = LabelWithTransitionsApp()
    app.animation_level = "none"

    async with app.run_test() as pilot:
        label = app.query_one(Label)
        # Sanity check.
        assert label.styles.background == Color.parse("red")
        # Test.
        label.add_class("blue-bg")
        await pilot.pause()
        assert label.styles.background == Color.parse("blue")
