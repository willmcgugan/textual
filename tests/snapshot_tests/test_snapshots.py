from pathlib import Path

import pytest
from rich.panel import Panel
from rich.text import Text

from tests.snapshot_tests.language_snippets import SNIPPETS
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding, Keymap
from textual.containers import Center, Grid, Middle, Vertical
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.pilot import Pilot
from textual.renderables.gradient import LinearGradient
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Header,
    DataTable,
    Input,
    RichLog,
    TextArea,
    Footer,
    Log,
    OptionList,
    Placeholder,
    SelectionList,
)
from textual.widgets import ProgressBar, Label, Switch
from textual.widgets import Static
from textual.widgets.text_area import BUILTIN_LANGUAGES, Selection, TextAreaTheme

# These paths should be relative to THIS directory.
WIDGET_EXAMPLES_DIR = Path("../../docs/examples/widgets")
LAYOUT_EXAMPLES_DIR = Path("../../docs/examples/guide/layout")
STYLES_EXAMPLES_DIR = Path("../../docs/examples/styles")
EXAMPLES_DIR = Path("../../examples")
SNAPSHOT_APPS_DIR = Path("./snapshot_apps")


# --- Layout related stuff ---


def test_grid_layout_basic(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "grid_layout1.py")


def test_grid_layout_basic_overflow(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "grid_layout2.py")


def test_grid_layout_gutter(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "grid_layout7_gutter.py")


def test_layers(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "layers.py")


def test_horizontal_layout(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "horizontal_layout.py")


def test_horizontal_layout_width_auto_dock(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "horizontal_auto_width.py")


def test_vertical_layout(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "vertical_layout.py")


def test_dock_layout_sidebar(snap_compare):
    assert snap_compare(LAYOUT_EXAMPLES_DIR / "dock_layout2_sidebar.py")


def test_layout_containers(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "layout_containers.py")


def test_alignment_containers(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "alignment_containers.py")


# --- Widgets - rendering and basic interactions ---
# Each widget should have a canonical example that is display in the docs.
# When adding a new widget, ideally we should also create a snapshot test
# from these examples which test rendering and simple interactions with it.


def test_switches(snap_compare):
    """Tests switches but also acts a regression test for using
    width: auto in a Horizontal layout context."""
    press = [
        "shift+tab",
        "enter",  # toggle off
        "shift+tab",
        "wait:20",
        "enter",  # toggle on
        "wait:20",
    ]
    assert snap_compare(WIDGET_EXAMPLES_DIR / "switch.py", press=press)


def test_input_and_focus(snap_compare):
    press = [
        *"Darren",  # Write "Darren"
        "tab",
        *"Burns",  # Focus second input, write "Burns"
    ]
    assert snap_compare(WIDGET_EXAMPLES_DIR / "input.py", press=press)


def test_input_validation(snap_compare):
    """Checking that invalid styling is applied. The snapshot app itself
    also adds styling for -valid which gives a green border."""
    press = [
        *"-2",  # -2 is invalid, so -invalid should be applied
        "tab",
        "3",  # This is valid, so -valid should be applied
        "tab",
        *"-2",
        # -2 is invalid, so -invalid should be applied (and :focus, since we stop here)
    ]
    assert snap_compare(SNAPSHOT_APPS_DIR / "input_validation.py", press=press)


def test_input_suggestions(snap_compare):
    async def run_before(pilot):
        pilot.app.query(Input).first().cursor_blink = False

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "input_suggestions.py", press=["b"], run_before=run_before
    )


def test_masked_input(snap_compare):
    async def run_before(pilot):
        pilot.app.query(Input).first().cursor_blink = False

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "masked_input.py",
        press=["A", "B", "C", "0", "1", "-", "D", "E"],
        run_before=run_before,
    )


def test_buttons_render(snap_compare):
    # Testing button rendering. We press tab to focus the first button too.
    assert snap_compare(WIDGET_EXAMPLES_DIR / "button.py", press=["tab"])


def test_placeholder_render(snap_compare):
    # Testing the rendering of the multiple placeholder variants and labels.
    assert snap_compare(WIDGET_EXAMPLES_DIR / "placeholder.py")


def test_datatable_render(snap_compare):
    press = ["tab", "down", "down", "right", "up", "left"]
    assert snap_compare(WIDGET_EXAMPLES_DIR / "data_table.py", press=press)


def test_datatable_row_cursor_render(snap_compare):
    press = ["up", "left", "right", "down", "down"]
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_row_cursor.py", press=press)


def test_datatable_column_cursor_render(snap_compare):
    press = ["left", "up", "down", "right", "right"]
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_column_cursor.py", press=press)


def test_datatable_sort_multikey(snap_compare):
    press = ["down", "right", "s"]  # Also checks that sort doesn't move cursor.
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_sort.py", press=press)


def test_datatable_remove_row(snap_compare):
    press = ["r"]
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_remove_row.py", press=press)


def test_datatable_labels_and_fixed_data(snap_compare):
    # Ensure that we render correctly when there are fixed rows/cols and labels.
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_row_labels.py")


def test_datatable_style_ordering(snap_compare):
    # Regression test for https://github.com/Textualize/textual/issues/2061
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_style_order.py")


def test_datatable_add_column(snap_compare):
    # Checking adding columns after adding rows
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_add_column.py")


def test_datatable_add_row_auto_height(snap_compare):
    # Check that rows added with auto height computation look right.
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_add_row_auto_height.py")


def test_datatable_add_row_auto_height_sorted(snap_compare):
    # Check that rows added with auto height computation look right.
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "data_table_add_row_auto_height.py", press=["s"]
    )


def test_datatable_auto_height_future_updates(snap_compare):
    """https://github.com/Textualize/textual/issues/4928 meant that when height=None,
    in add_row, future updates to the table would be incorrect.

    In this test, every 2nd row is auto height and every other row is height 2.
    The table is cleared then fully repopulated with the same 4 rows. All 4 rows
    should be visible and rendered at heights 2, 1, 2, 1.
    """
    ROWS = [
        ("foo", "bar"),
        (1, "abc"),
        (2, "def"),
        (3, "ghi"),
        (4, "jkl"),
    ]

    class ExampleApp(App[None]):
        CSS = "DataTable { border: solid red; }"

        def compose(self) -> ComposeResult:
            yield DataTable()

        def on_mount(self) -> None:
            table = self.query_one(DataTable)
            table.add_columns(*ROWS[0])
            self.populate_table()

        def key_r(self) -> None:
            self.populate_table()

        def populate_table(self) -> None:
            table = self.query_one(DataTable)
            table.clear()
            for i, row in enumerate(ROWS[1:]):
                table.add_row(
                    *row,
                    height=None if i % 2 == 1 else 2,
                )

    assert snap_compare(ExampleApp(), press=["r"])


def test_datatable_cell_padding(snap_compare):
    # Check that horizontal cell padding is respected.
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_cell_padding.py")


def test_datatable_change_cell_padding(snap_compare):
    # Check that horizontal cell padding is respected.
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "data_table_cell_padding.py", press=["a", "b"]
    )


def test_footer_render(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "footer.py")


def test_header_render(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "header.py")


def test_list_view(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "list_view.py", press=["tab", "down", "down", "up"]
    )


def test_log_write_lines(snap_compare):
    assert snap_compare("snapshot_apps/log_write_lines.py")


def test_log_write(snap_compare):
    assert snap_compare("snapshot_apps/log_write.py")


def test_fr_units(snap_compare):
    assert snap_compare("snapshot_apps/fr_units.py")


def test_visibility(snap_compare):
    assert snap_compare("snapshot_apps/visibility.py")


def test_tree_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "tree.py")


def test_tree_with_detail_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "detail_tree.py")


def test_markdown_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "markdown.py")


def test_markdown_viewer_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "markdown_viewer.py")


def test_markdown_theme_switching(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "markdown_theme_switcher.py", press=["t"])


def test_markdown_dark_theme_override(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "markdown_theme_switcher.py", press=["d", "wait:100"]
    )


def test_markdown_light_theme_override(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "markdown_theme_switcher.py", press=["l", "t", "wait:100"]
    )


def test_checkbox_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "checkbox.py")


def test_radio_button_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "radio_button.py")


def test_radio_set_example(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "radio_set.py")


def test_content_switcher_example_initial(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "content_switcher.py")


def test_content_switcher_example_switch(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "content_switcher.py",
        press=["tab", "enter", "wait:500"],
        terminal_size=(50, 50),
    )


def test_tabbed_content(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "tabbed_content.py")


def test_tabbed_content_with_modified_tabs(snap_compare):
    # Tabs enabled and hidden.
    assert snap_compare(SNAPSHOT_APPS_DIR / "modified_tabs.py")


def test_tabbed_content_styling_not_leaking(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "tabbed_content_style_leak_test.py")


def test_option_list_strings(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "option_list_strings.py")


def test_option_list_options(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "option_list_options.py")


def test_option_list_tables(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "option_list_tables.py")


def test_option_list_build(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "option_list.py")


def test_option_list_replace_prompt_from_single_line_to_single_line(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "option_list_multiline_options.py", press=["1"]
    )


def test_option_list_replace_prompt_from_single_line_to_two_lines(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "option_list_multiline_options.py", press=["2"]
    )


def test_option_list_replace_prompt_from_two_lines_to_three_lines(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "option_list_multiline_options.py", press=["3"]
    )


def test_option_list_scrolling_in_long_list(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "option_list_long.py", press=["up"])


def test_progress_bar_indeterminate(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_isolated_.py", press=["f"])


def test_progress_bar_indeterminate_styled(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_styled_.py", press=["f"])


def test_progress_bar_halfway(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_isolated_.py", press=["t"])


def test_progress_bar_halfway_styled(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_styled_.py", press=["t"])


def test_progress_bar_completed(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_isolated_.py", press=["u"])


def test_progress_bar_completed_styled(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "progress_bar_styled_.py", press=["u"])


def test_rule_horizontal_rules(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "horizontal_rules.py")


def test_rule_vertical_rules(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "vertical_rules.py")


def test_select(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "select_widget.py")


def test_selection_list_selected(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "selection_list_selected.py")


def test_selection_list_selections(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "selection_list_selections.py")


def test_selection_list_tuples(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "selection_list_tuples.py")


def test_select_expanded(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "select_widget.py", press=["tab", "enter"]
    )


def test_select_from_values_expanded(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "select_from_values_widget.py", press=["tab", "enter"]
    )


def test_select_expanded_changed(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "select_widget.py",
        press=["tab", "enter", "down", "enter"],
    )


def test_select_no_blank_has_default_value(snap_compare):
    """Make sure that the first value is selected by default if allow_blank=False."""
    assert snap_compare(WIDGET_EXAMPLES_DIR / "select_widget_no_blank.py")


def test_select_set_options(snap_compare):
    assert snap_compare(
        WIDGET_EXAMPLES_DIR / "select_widget_no_blank.py",
        press=["s"],
    )


def test_sparkline_render(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "sparkline.py")


def test_sparkline_component_classes_colors(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "sparkline_colors.py")


def test_collapsible_render(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible.py")


def test_collapsible_collapsed(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible.py", press=["c"])


def test_collapsible_expanded(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible.py", press=["e"])


def test_collapsible_nested(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible_nested.py")


def test_collapsible_custom_symbol(snap_compare):
    assert snap_compare(WIDGET_EXAMPLES_DIR / "collapsible_custom_symbol.py")


def test_directory_tree_reloading(snap_compare, tmp_path):
    async def run_before(pilot):
        await pilot.app.setup(tmp_path)
        await pilot.press(
            "down", "e", "e", "down", "down", "down", "down", "e", "down", "d", "r"
        )

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "directory_tree_reload.py",
        run_before=run_before,
    )


# --- CSS properties ---
# We have a canonical example for each CSS property that is shown in their docs.
# If any of these change, something has likely broken, so snapshot each of them.

PATHS = [
    path.name
    for path in (Path(__file__).parent / STYLES_EXAMPLES_DIR).iterdir()
    if path.suffix == ".py"
]


@pytest.mark.parametrize("file_name", PATHS)
def test_css_property(file_name, snap_compare):
    path_to_app = STYLES_EXAMPLES_DIR / file_name
    assert snap_compare(path_to_app)


def test_viewport_height_and_width_properties(snap_compare):
    path_to_app = SNAPSHOT_APPS_DIR / "viewport_units.py"
    assert snap_compare(path_to_app)


def test_multiple_css(snap_compare):
    # Interaction between multiple CSS files and app-level/classvar CSS
    assert snap_compare("snapshot_apps/multiple_css/multiple_css.py")


def test_order_independence(snap_compare):
    assert snap_compare("snapshot_apps/layer_order_independence.py")


def test_order_independence_toggle(snap_compare):
    assert snap_compare("snapshot_apps/layer_order_independence.py", press="t")


def test_columns_height(snap_compare):
    # Interaction with height auto, and relative heights to make columns
    assert snap_compare("snapshot_apps/columns_height.py")


def test_offsets(snap_compare):
    """Test offsets of containers"""
    assert snap_compare("snapshot_apps/offsets.py")


def test_nested_auto_heights(snap_compare):
    """Test refreshing widget within a auto sized container"""
    assert snap_compare("snapshot_apps/nested_auto_heights.py", press=["1", "2"])


def test_programmatic_scrollbar_gutter_change(snap_compare):
    """Regression test for #1607 https://github.com/Textualize/textual/issues/1607

    See also tests/css/test_programmatic_style_changes.py for other related regression tests.
    """
    assert snap_compare(
        "snapshot_apps/programmatic_scrollbar_gutter_change.py", press=["s"]
    )


# --- Other ---


def test_key_display(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "key_display.py")


def test_demo(snap_compare):
    """Test the demo app (python -m textual)"""
    assert snap_compare(
        Path("../../src/textual/demo.py"),
        terminal_size=(100, 30),
    )


def test_label_widths(snap_compare):
    """Test renderable widths are calculate correctly."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "label_widths.py")


def test_border_alpha(snap_compare):
    """Test setting a border alpha."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "border_alpha.py")


def test_auto_width_input(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "auto_width_input.py", press=["tab", *"Hello"]
    )


def test_screen_switch(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "screen_switch.py", press=["a", "b"])


def test_disabled_widgets(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "disable_widgets.py")


def test_focus_component_class(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "focus_component_class.py", press=["tab"])


def test_line_api_scrollbars(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "line_api_scrollbars.py")


def test_remove_with_auto_height(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "remove_auto.py", press=["a", "a", "a", "d", "d"]
    )


def test_auto_table(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto-table.py", terminal_size=(120, 40))


def test_table_markup(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "table_markup.py")


def test_richlog_max_lines(snap_compare):
    assert snap_compare("snapshot_apps/richlog_max_lines.py", press=[*"abcde"])


def test_richlog_scroll(snap_compare):
    """Ensure `RichLog.auto_scroll` causes the log to scroll to the end when new content is written."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "richlog_scroll.py")


def test_richlog_width(snap_compare):
    """Check that the width of RichLog is respected, even when it's not visible."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "richlog_width.py", press=["p"])


def test_richlog_min_width(snap_compare):
    """The available space of this RichLog is less than the minimum width, so written
    content should be rendered at `min_width`. This snapshot should show the renderable
    clipping at the right edge, as there's not enough space to satisfy the minimum width."""

    class RichLogMinWidth20(App[None]):
        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=20)
            text = Text("0123456789", style="on red", justify="right")
            rich_log.write(text)
            yield rich_log

    assert snap_compare(RichLogMinWidth20(), terminal_size=(20, 6))


def test_richlog_deferred_render_no_expand(snap_compare):
    """Check we can write to a RichLog before its size is known i.e. in `compose`."""

    class RichLogNoExpand(App[None]):
        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=10)
            text = Text("0123456789", style="on red", justify="right")
            # Perform the write in compose - it'll be deferred until the size is known
            rich_log.write(text)
            yield rich_log

    assert snap_compare(RichLogNoExpand(), terminal_size=(20, 6))


def test_richlog_deferred_render_expand(snap_compare):
    """Check we can write to a RichLog before its size is known i.e. in `compose`.

    The renderable should expand to fill full the width of the RichLog.
    """

    class RichLogExpand(App[None]):
        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=10)
            text = Text("0123456789", style="on red", justify="right")
            # Perform the write in compose - it'll be deferred until the size is known
            rich_log.write(text, expand=True)
            yield rich_log

    assert snap_compare(RichLogExpand(), terminal_size=(20, 6))


def test_richlog_markup(snap_compare):
    """Check that Rich markup is rendered in RichLog when markup=True."""

    class RichLogWidth(App[None]):
        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=10, markup=True)
            rich_log.write("[black on red u]black text on red, underlined")
            rich_log.write("normal text, no markup")
            yield rich_log

    assert snap_compare(RichLogWidth(), terminal_size=(42, 6))


def test_richlog_shrink(snap_compare):
    """Ensure that when shrink=True, the renderable shrinks to fit the width of the RichLog."""

    class RichLogShrink(App[None]):
        CSS = "RichLog { width: 20; background: red;}"

        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=4)
            panel = Panel("lorem ipsum dolor sit amet lorem ipsum dolor sit amet")
            rich_log.write(panel)
            yield rich_log

    assert snap_compare(RichLogShrink(), terminal_size=(24, 6))


def test_richlog_write_at_specific_width(snap_compare):
    """Ensure we can write renderables at a specific width.
    `min_width` should be respected, but `width` should override.

    The green label at the bottom should be equal in width to the bottom
    renderable (equal to min_width).
    """

    class RichLogWriteAtSpecificWidth(App[None]):
        CSS = """
        RichLog { width: 1fr; height: auto; }
        #width-marker { background: green; width: 50; }
        """

        def compose(self) -> ComposeResult:
            rich_log = RichLog(min_width=50)
            rich_log.write(Panel("width=20", style="black on red"), width=20)
            rich_log.write(Panel("width=40", style="black on red"), width=40)
            rich_log.write(Panel("width=60", style="black on red"), width=60)
            rich_log.write(Panel("width=120", style="black on red"), width=120)
            rich_log.write(
                Panel("width=None (fallback to min_width)", style="black on red")
            )
            yield rich_log
            width_marker = Label(
                f"this label is width 50 (same as min_width)", id="width-marker"
            )
            yield width_marker

    assert snap_compare(RichLogWriteAtSpecificWidth())


def test_richlog_highlight(snap_compare):
    """Check that RichLog.highlight correctly highlights with the ReprHighlighter.

    Also ensures that interaction between CSS and highlighting is as expected -
    non-highlighted text should have the CSS styles applied, but highlighted text
    should ignore the CSS (and use the highlights returned from the highlighter).
    """

    class RichLogHighlight(App[None]):
        # Add some CSS to check interaction with highlighting.
        CSS = """
        RichLog { color: red; background: dodgerblue 40%; }
        """

        def compose(self) -> ComposeResult:
            rich_log = RichLog(highlight=True)
            rich_log.write("Foo('bar', x=1, y=[1, 2, 3])")
            yield rich_log

    assert snap_compare(RichLogHighlight(), terminal_size=(30, 3))


def test_tabs_invalidate(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "tabs_invalidate.py",
        press=["tab", "right"],
    )


def test_scrollbar_thumb_height(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "scrollbar_thumb_height.py",
    )


def test_pilot_resize_terminal(snap_compare):
    async def run_before(pilot):
        await pilot.resize_terminal(35, 20)
        await pilot.resize_terminal(20, 10)

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "pilot_resize_terminal.py",
        run_before=run_before,
        terminal_size=(80, 25),
    )


def test_css_hot_reloading(snap_compare, monkeypatch):
    """Regression test for https://github.com/Textualize/textual/issues/2063."""

    monkeypatch.setenv(
        "TEXTUAL", "debug"
    )  # This will make sure we create a file monitor.

    async def run_before(pilot):
        css_file = pilot.app.CSS_PATH
        with open(css_file, "w") as f:
            f.write("/* This file is purposefully empty. */\n")  # Clear all the CSS.
        await pilot.app._on_css_change()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "hot_reloading_app.py", run_before=run_before
    )


def test_css_hot_reloading_on_screen(snap_compare, monkeypatch):
    """Regression test for https://github.com/Textualize/textual/issues/3454."""

    monkeypatch.setenv(
        "TEXTUAL", "debug"
    )  # This will make sure we create a file monitor.

    async def run_before(pilot):
        css_file = pilot.app.screen.CSS_PATH
        with open(css_file, "w") as f:
            f.write("/* This file is purposefully empty. */\n")  # Clear all the CSS.
        await pilot.app._on_css_change()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "hot_reloading_app_with_screen_css.py",
        run_before=run_before,
    )


def test_datatable_hot_reloading(snap_compare, monkeypatch):
    """Regression test for https://github.com/Textualize/textual/issues/3312."""

    monkeypatch.setenv(
        "TEXTUAL", "debug"
    )  # This will make sure we create a file monitor.

    async def run_before(pilot):
        css_file = pilot.app.CSS_PATH
        with open(css_file, "w") as f:
            f.write("/* This file is purposefully empty. */\n")  # Clear all the CSS.
        await pilot.app._on_css_change()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "datatable_hot_reloading.py", run_before=run_before
    )


def test_markdown_component_classes_reloading(snap_compare, monkeypatch):
    """Tests all markdown component classes reload correctly.

    See https://github.com/Textualize/textual/issues/3464."""

    monkeypatch.setenv(
        "TEXTUAL", "debug"
    )  # This will make sure we create a file monitor.

    async def run_before(pilot):
        css_file = pilot.app.CSS_PATH
        with open(css_file, "w") as f:
            f.write("/* This file is purposefully empty. */\n")  # Clear all the CSS.
        await pilot.app._on_css_change()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "markdown_component_classes_reloading.py",
        run_before=run_before,
    )


def test_markdown_space_squashing(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "markdown_whitespace.py")


def test_layer_fix(snap_compare):
    # Check https://github.com/Textualize/textual/issues/1358
    assert snap_compare(SNAPSHOT_APPS_DIR / "layer_fix.py", press=["d"])


def test_modal_dialog_bindings_input(snap_compare):
    # Check https://github.com/Textualize/textual/issues/2194
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "modal_screen_bindings.py",
        press=["enter", "h", "!", "left", "i", "tab"],
    )


def test_modal_dialog_bindings(snap_compare):
    # Check https://github.com/Textualize/textual/issues/2194
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "modal_screen_bindings.py",
        press=["enter", "tab", "h", "i", "tab", "enter"],
    )


def test_dock_scroll(snap_compare):
    # https://github.com/Textualize/textual/issues/2188
    assert snap_compare(SNAPSHOT_APPS_DIR / "dock_scroll.py", terminal_size=(80, 25))


def test_dock_scroll2(snap_compare):
    # https://github.com/Textualize/textual/issues/2525
    assert snap_compare(SNAPSHOT_APPS_DIR / "dock_scroll2.py", terminal_size=(80, 25))


def test_dock_scroll_off_by_one(snap_compare):
    # https://github.com/Textualize/textual/issues/2525
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "dock_scroll_off_by_one.py",
        terminal_size=(80, 25),
        press=["_"],
    )


def test_dock_none(snap_compare):
    """Checking that `dock:none` works in CSS and Python.
    The label should appear at the top here, since we've undocked both
    the header and footer.
    """

    class DockNone(App[None]):
        CSS = "Header { dock: none; }"

        def compose(self) -> ComposeResult:
            yield Label("Hello")
            yield Header()
            footer = Footer()
            footer.styles.dock = "none"
            yield footer

    assert snap_compare(DockNone(), terminal_size=(30, 5))


def test_scroll_to(snap_compare):
    # https://github.com/Textualize/textual/issues/2525
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "scroll_to.py", terminal_size=(80, 25), press=["_"]
    )


def test_auto_fr(snap_compare):
    # https://github.com/Textualize/textual/issues/2220
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto_fr.py", terminal_size=(80, 25))


def test_fr_margins(snap_compare):
    # https://github.com/Textualize/textual/issues/2220
    assert snap_compare(SNAPSHOT_APPS_DIR / "fr_margins.py", terminal_size=(80, 25))


def test_scroll_visible(snap_compare):
    # https://github.com/Textualize/textual/issues/2181
    assert snap_compare(SNAPSHOT_APPS_DIR / "scroll_visible.py", press=["t"])


def test_scroll_to_center(snap_compare):
    # READ THIS IF THIS TEST FAILS:
    # While https://github.com/Textualize/textual/issues/2254 is open, the snapshot
    # this is being compared against is INCORRECT.
    # The correct output for this snapshot test would show a couple of containers
    # scrolled so that the red string >>bullseye<< is centered on the screen.
    # When this snapshot "breaks" because #2254 is fixed, this snapshot can be updated.
    assert snap_compare(SNAPSHOT_APPS_DIR / "scroll_to_center.py", press=["s"])


def test_quickly_change_tabs(snap_compare):
    # https://github.com/Textualize/textual/issues/2229
    assert snap_compare(SNAPSHOT_APPS_DIR / "quickly_change_tabs.py", press=["p"])


def test_fr_unit_with_min(snap_compare):
    # https://github.com/Textualize/textual/issues/2378
    assert snap_compare(SNAPSHOT_APPS_DIR / "fr_with_min.py")


def test_select_rebuild(snap_compare):
    # https://github.com/Textualize/textual/issues/2557
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "select_rebuild.py",
        press=["space", "escape", "tab", "enter", "tab", "space"],
    )


def test_blur_on_disabled(snap_compare):
    # https://github.com/Textualize/textual/issues/2641
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "blur_on_disabled.py",
        press=[*"foo", "f3", *"this should not appear"],
    )


def test_tooltips_in_compound_widgets(snap_compare):
    # https://github.com/Textualize/textual/issues/2641
    async def run_before(pilot) -> None:
        await pilot.pause()
        await pilot.hover("ProgressBar")
        await pilot.pause(0.4)
        await pilot.pause()

    assert snap_compare(SNAPSHOT_APPS_DIR / "tooltips.py", run_before=run_before)


def test_command_palette(snap_compare) -> None:
    async def run_before(pilot) -> None:
        # await pilot.press("ctrl+backslash")
        pilot.app.screen.query_one(Input).cursor_blink = False
        await pilot.press("A")
        await pilot.app.screen.workers.wait_for_complete()

    assert snap_compare(SNAPSHOT_APPS_DIR / "command_palette.py", run_before=run_before)


def test_command_palette_discovery(snap_compare) -> None:
    async def run_before(pilot) -> None:
        pilot.app.screen.query_one(Input).cursor_blink = False
        await pilot.app.screen.workers.wait_for_complete()

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "command_palette_discovery.py", run_before=run_before
    )


# --- textual-dev library preview tests ---


def test_textual_dev_border_preview(snap_compare):
    async def run_before(pilot):
        buttons = pilot.app.query(Button)
        for button in buttons:
            button.active_effect_duration = 0

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "dev_previews_border.py",
        press=["enter"],
        run_before=run_before,
    )


def test_textual_dev_colors_preview(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "dev_previews_color.py")


def test_textual_dev_easing_preview(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "dev_previews_easing.py")


def test_textual_dev_keys_preview(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "dev_previews_keys.py", press=["a", "b"])


def test_notifications_example(snap_compare) -> None:
    assert snap_compare(WIDGET_EXAMPLES_DIR / "toast.py")


def test_notifications_through_screens(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "notification_through_screens.py")


def test_notifications_through_modes(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "notification_through_modes.py")


def test_notification_with_inline_link(snap_compare) -> None:
    # https://github.com/Textualize/textual/issues/3530
    assert snap_compare(SNAPSHOT_APPS_DIR / "notification_with_inline_link.py")


def test_notification_with_inline_link_hover(snap_compare) -> None:
    # https://github.com/Textualize/textual/issues/3530
    async def run_before(pilot) -> None:
        await pilot.pause()
        await pilot.hover("Toast", offset=(8, 1))

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "notification_with_inline_link.py",
        run_before=run_before,
    )


def test_print_capture(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "capture_print.py")


def test_text_log_blank_write(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "text_log_blank_write.py")


def test_nested_fr(snap_compare) -> None:
    # https://github.com/Textualize/textual/pull/3059
    assert snap_compare(SNAPSHOT_APPS_DIR / "nested_fr.py")


@pytest.mark.syntax
@pytest.mark.parametrize("language", BUILTIN_LANGUAGES)
def test_text_area_language_rendering(language, snap_compare):
    # This test will fail if we're missing a snapshot test for a valid
    # language. We should have a snapshot test for each language we support
    # as the syntax highlighting will be completely different for each of them.

    snippet = SNIPPETS.get(language)

    def setup_language(pilot) -> None:
        text_area = pilot.app.query_one(TextArea)
        text_area.load_text(snippet)
        text_area.language = language

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area.py",
        run_before=setup_language,
        terminal_size=(80, snippet.count("\n") + 4),
    )


@pytest.mark.parametrize(
    "selection",
    [
        Selection((0, 0), (2, 8)),
        Selection((1, 0), (0, 0)),
        Selection((5, 2), (0, 0)),
        Selection((0, 0), (4, 20)),
        Selection.cursor((1, 0)),
        Selection.cursor((2, 6)),
    ],
)
def test_text_area_selection_rendering(snap_compare, selection):
    text = """I am a line.

I am another line.

I am the final line."""

    def setup_selection(pilot):
        text_area = pilot.app.query_one(TextArea)
        text_area.load_text(text)
        text_area.show_line_numbers = False
        text_area.selection = selection

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area.py",
        run_before=setup_selection,
        terminal_size=(30, text.count("\n") + 4),
    )


def test_text_area_read_only_cursor_rendering(snap_compare):
    def setup_selection(pilot):
        text_area = pilot.app.query_one(TextArea)
        text_area.theme = "css"
        text_area.text = "Hello, world!"
        text_area.read_only = True

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area.py",
        run_before=setup_selection,
        terminal_size=(30, 5),
    )


@pytest.mark.syntax
@pytest.mark.parametrize(
    "theme_name", [theme.name for theme in TextAreaTheme.builtin_themes()]
)
def test_text_area_themes(snap_compare, theme_name):
    """Each theme should have its own snapshot with at least some Python
    to check that the rendering is sensible. This also ensures that theme
    switching results in the display changing correctly."""
    text = """\
def hello(name):
    x = 123
    while not False:
        print("hello " + name)
        continue
"""

    def setup_theme(pilot):
        text_area = pilot.app.query_one(TextArea)
        text_area.load_text(text)
        text_area.language = "python"
        text_area.selection = Selection((0, 1), (1, 9))
        text_area.theme = theme_name

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area.py",
        run_before=setup_theme,
        terminal_size=(48, text.count("\n") + 4),
    )


def test_text_area_alternate_screen(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area_alternate_screen.py", terminal_size=(48, 10)
    )


@pytest.mark.syntax
def test_text_area_wrapping_and_folding(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area_wrapping.py", terminal_size=(20, 26)
    )


def test_text_area_line_number_start(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "text_area_line_number_start.py", terminal_size=(32, 8)
    )


def test_digits(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "digits.py")


def test_auto_grid(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto_grid.py")


def test_auto_grid_default_height(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto_grid_default_height.py", press=["g"])


def test_scoped_css(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "scoped_css.py")


def test_unscoped_css(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "unscoped_css.py")


def test_big_buttons(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "big_button.py")


def test_keyline(snap_compare) -> None:
    assert snap_compare(SNAPSHOT_APPS_DIR / "keyline.py")


def test_button_outline(snap_compare):
    """Outline style rendered incorrectly when applied to a `Button` widget.

    Regression test for https://github.com/Textualize/textual/issues/3628
    """
    assert snap_compare(SNAPSHOT_APPS_DIR / "button_outline.py")


def test_notifications_loading_overlap_order(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3677.

    This tests that notifications stay on top of loading indicators and it also
    tests that loading a widget will remove its scrollbars.
    """
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "notifications_above_loading.py", terminal_size=(80, 20)
    )


def test_missing_vertical_scroll(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3687"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "missing_vertical_scroll.py")


def test_vertical_min_height(snap_compare):
    """Test vertical min height takes border in to account."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "vertical_min_height.py")


def test_vertical_max_height(snap_compare):
    """Test vertical max height takes border in to account."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "vertical_max_height.py")


def test_max_height_100(snap_compare):
    """Test vertical max height takes border in to account."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "max_height_100.py")


def test_loading_indicator(snap_compare):
    """Test loading indicator."""
    # https://github.com/Textualize/textual/pull/3816
    assert snap_compare(SNAPSHOT_APPS_DIR / "loading.py", press=["space"])


def test_loading_indicator_disables_widget(snap_compare):
    """Test loading indicator disabled widget."""
    # https://github.com/Textualize/textual/pull/3816
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "loading.py", press=["space", "down", "down", "space"]
    )


def test_mount_style_fix(snap_compare):
    """Regression test for broken style update on mount."""
    # https://github.com/Textualize/textual/issues/3858
    assert snap_compare(SNAPSHOT_APPS_DIR / "mount_style_fix.py")


def test_zero_scrollbar_size(snap_compare):
    """Regression test for missing content with 0 sized scrollbars"""
    # https://github.com/Textualize/textual/issues/3886
    assert snap_compare(SNAPSHOT_APPS_DIR / "zero_scrollbar_size.py")


def test_tree_clearing_and_expansion(snap_compare):
    """Test the Tree.root.is_expanded state after a Tree.clear"""
    # https://github.com/Textualize/textual/issues/3557
    assert snap_compare(SNAPSHOT_APPS_DIR / "tree_clearing.py")


def test_nested_specificity(snap_compare):
    """Test specificity of nested rules is working."""
    # https://github.com/Textualize/textual/issues/3961
    assert snap_compare(SNAPSHOT_APPS_DIR / "nested_specificity.py")


def test_tab_rename(snap_compare):
    """Test setting a new label for a tab amongst a TabbedContent."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "tab_rename.py")


def test_input_percentage_width(snap_compare):
    """Check percentage widths work correctly."""
    # https://github.com/Textualize/textual/issues/3721
    assert snap_compare(SNAPSHOT_APPS_DIR / "input_percentage_width.py")


def test_recompose(snap_compare):
    """Check recompose works."""
    # https://github.com/Textualize/textual/pull/4206
    assert snap_compare(SNAPSHOT_APPS_DIR / "recompose.py")


@pytest.mark.parametrize("dark", [True, False])
def test_ansi_color_mapping(snap_compare, dark):
    """Test how ANSI colors in Rich renderables are mapped to hex colors."""

    def setup(pilot):
        pilot.app.dark = dark

    assert snap_compare(SNAPSHOT_APPS_DIR / "ansi_mapping.py", run_before=setup)


def test_pretty_grid_gutter_interaction(snap_compare):
    """Regression test for https://github.com/Textualize/textual/pull/4219."""
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "pretty_grid_gutter_interaction.py", terminal_size=(81, 7)
    )


def test_sort_children(snap_compare):
    """Test sort_children method."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "sort_children.py", terminal_size=(80, 25))


def test_app_blur(snap_compare):
    """Test Styling after receiving an AppBlur message."""

    async def run_before(pilot) -> None:
        await pilot.pause()  # Allow the AppBlur message to get processed.

    assert snap_compare(SNAPSHOT_APPS_DIR / "app_blur.py", run_before=run_before)


def test_placeholder_disabled(snap_compare):
    """Test placeholder with diabled set to True."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "placeholder_disabled.py")


def test_listview_index(snap_compare):
    """Tests that ListView scrolls correctly after updating its index."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "listview_index.py")


def test_button_widths(snap_compare):
    """Test that button widths expand auto containers as expected."""
    # https://github.com/Textualize/textual/issues/4024
    assert snap_compare(SNAPSHOT_APPS_DIR / "button_widths.py")


def test_welcome(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "welcome_widget.py")


# --- Example apps ---
# We skip the code browser because the length of the scrollbar in the tree depends on
# the number of files and folders we have locally and that typically differs from the
# pristine setting in which CI runs.


def test_example_calculator(snap_compare):
    """Test the calculator example."""
    assert snap_compare(EXAMPLES_DIR / "calculator.py")


def test_example_color_command(snap_compare):
    """Test the color_command example."""
    assert snap_compare(
        EXAMPLES_DIR / "color_command.py",
        press=[App.COMMAND_PALETTE_BINDING, "r", "e", "d", "down", "enter"],
    )


def test_example_dictionary(snap_compare):
    """Test the dictionary example (basic layout test)."""

    async def run_before(pilot):
        pilot.app.query(Input).first().cursor_blink = False

    assert snap_compare(EXAMPLES_DIR / "dictionary.py", run_before=run_before)


def test_example_five_by_five(snap_compare):
    """Test the five_by_five example."""
    assert snap_compare(EXAMPLES_DIR / "five_by_five.py")


def test_example_json_tree(snap_compare):
    """Test the json_tree example."""
    assert snap_compare(
        EXAMPLES_DIR / "json_tree.py",
        press=["a", "down", "enter", "down", "down", "enter"],
    )


def test_example_markdown(snap_compare):
    """Test the markdown example."""
    assert snap_compare(EXAMPLES_DIR / "markdown.py")


def test_example_merlin(snap_compare):
    """Test the merlin example."""
    on_switches = {2, 3, 5, 8}

    async def run_before(pilot):
        pilot.app.query_one("Timer").running = False  # This will freeze the clock.
        for switch in pilot.app.query("LabelSwitch"):
            switch.query_one("Switch").value = switch.switch_no in on_switches
        await pilot.pause()

    assert snap_compare(EXAMPLES_DIR / "merlin.py", run_before=run_before)


def test_example_pride(snap_compare):
    """Test the pride example."""
    assert snap_compare(EXAMPLES_DIR / "pride.py")


def test_button_with_console_markup(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4328"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "button_markup.py")


def test_width_100(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4360"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "width_100.py")


def test_button_with_multiline_label(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "button_multiline_label.py")


def test_margin_multiple(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "margin_multiple.py")


def test_dynamic_bindings(snap_compare):
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "dynamic_bindings.py", press=["a", "b", "c"]
    )


def test_grid_gutter(snap_compare):
    # https://github.com/Textualize/textual/issues/4522
    assert snap_compare(SNAPSHOT_APPS_DIR / "grid_gutter.py")


def test_multi_keys(snap_compare):
    # https://github.com/Textualize/textual/issues/4542
    assert snap_compare(SNAPSHOT_APPS_DIR / "multi_keys.py")


def test_data_table_in_tabs(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_tabs.py")


def test_auto_tab_active(snap_compare):
    # https://github.com/Textualize/textual/issues/4593
    assert snap_compare(SNAPSHOT_APPS_DIR / "auto_tab_active.py", press=["space"])


def test_hatch(snap_compare):
    """Test hatch styles."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "hatch.py")


def test_rules(snap_compare):
    """Test rules."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "rules.py")


def test_grid_auto(snap_compare):
    """Test grid with keyline and auto-dimension."""
    # https://github.com/Textualize/textual/issues/4678
    assert snap_compare(SNAPSHOT_APPS_DIR / "grid_auto.py")


def test_footer_compact(snap_compare):
    """Test Footer in the compact style"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "footer_toggle_compact.py")


def test_footer_compact_with_hover(snap_compare):
    """Test Footer in the compact style when the mouse is hovering over a keybinding"""

    async def run_before(pilot) -> None:
        await pilot.hover("Footer", offset=(0, 0))

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "footer_toggle_compact.py", run_before=run_before
    )


def test_footer_standard_after_reactive_change(snap_compare):
    """Test Footer in the standard style after `compact` reactive change"""
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "footer_toggle_compact.py", press=["ctrl+t"]
    )


def test_footer_standard_with_hover(snap_compare):
    """Test Footer in the standard style when the mouse is hovering over a keybinding"""

    async def run_before(pilot) -> None:
        await pilot.press("ctrl+t")
        await pilot.hover("Footer", offset=(0, 0))

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "footer_toggle_compact.py", run_before=run_before
    )


def test_footer_classic_styling(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4557"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "footer_classic_styling.py")


def test_option_list_scrolling_with_multiline_options(snap_compare):
    # https://github.com/Textualize/textual/issues/4705
    assert snap_compare(WIDGET_EXAMPLES_DIR / "option_list_tables.py", press=["up"])


def test_bindings_screen_overrides_show(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4382"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "bindings_screen_overrides_show.py")


def test_scroll_visible_with_margin(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/2181"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "scroll_visible_margin.py", press=["x"])


def test_programmatic_disable_button(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3130"""

    async def run_before(pilot: Pilot) -> None:
        await pilot.hover("#disable-btn")
        await pilot.press("space")

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "programmatic_disable_button.py", run_before=run_before
    )


def test_toggle_style_order(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3421"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "toggle_style_order.py")


def test_component_text_opacity(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/3413"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "component_text_opacity.py")


def test_progress_gradient(snap_compare):
    """Test gradient parameter on ProgressBar"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "progress_gradient.py")


def test_recompose_in_mount(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4799"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "recompose_on_mount.py")


def test_enter_or_leave(snap_compare) -> None:
    async def run_before(pilot: Pilot):
        await pilot.hover("#foo")

    assert snap_compare(SNAPSHOT_APPS_DIR / "enter_or_leave.py", run_before=run_before)


def test_remove_tab_no_animation(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4814"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "remove_tab.py", press=["space"])


def test_auto_height_scrollbar(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4778"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "data_table_auto_height.py")


def test_bind_override(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4755"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "bind_override.py")


def test_command_palette_dismiss_escape(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4856"""

    async def run_before(pilot: Pilot):
        await pilot.press(App.COMMAND_PALETTE_BINDING)
        await pilot.pause()
        await pilot.press("escape")

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "command_palette_dismiss.py", run_before=run_before
    )


def test_command_palette_dismiss_escape_no_results(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4856"""

    async def run_before(pilot: Pilot):
        await pilot.press(App.COMMAND_PALETTE_BINDING)
        await pilot.pause()
        await pilot.press(*"foo")
        await pilot.app.workers.wait_for_complete()
        await pilot.press("escape")

    assert snap_compare(
        SNAPSHOT_APPS_DIR / "command_palette_dismiss.py", run_before=run_before
    )


def test_command_palette_key_change(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4887"""
    assert snap_compare(SNAPSHOT_APPS_DIR / "command_palette_key.py")


def test_split(snap_compare):
    """Test split rule."""
    assert snap_compare(SNAPSHOT_APPS_DIR / "split.py", terminal_size=(100, 30))


def test_system_commands(snap_compare):
    """The system commands should appear in the command palette."""

    class SimpleApp(App):
        def compose(self) -> ComposeResult:
            input = Input()
            input.cursor_blink = False
            yield input

    app = SimpleApp()
    app.animation_level = "none"
    assert snap_compare(
        app,
        terminal_size=(100, 30),
        press=["ctrl+p"],
    )


def test_help_panel(snap_compare):
    """Test help panel."""

    class HelpPanelApp(App):
        def compose(self) -> ComposeResult:
            yield Input()

    async def run_before(pilot: Pilot):
        pilot.app.query(Input).first().cursor_blink = False
        await pilot.press(App.COMMAND_PALETTE_BINDING)
        await pilot.pause()
        await pilot.press(*"keys")
        await pilot.press("enter")
        await pilot.app.workers.wait_for_complete()

    assert snap_compare(HelpPanelApp(), terminal_size=(100, 30), run_before=run_before)


def test_scroll_page_down(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/4914"""
    # Should show 25 at the top
    assert snap_compare(
        SNAPSHOT_APPS_DIR / "scroll_page.py", press=["pagedown"], terminal_size=(80, 25)
    )


def test_maximize(snap_compare):
    """Check that maximize isolates a single widget."""

    class MaximizeApp(App):
        BINDINGS = [("m", "screen.maximize", "maximize focused widget")]

        def compose(self) -> ComposeResult:
            yield Button("Hello")
            yield Button("World")
            yield Footer()

    assert snap_compare(MaximizeApp(), press=["m"])


def test_maximize_container(snap_compare):
    """Check maximizing a widget in a maximizeable container, maximizes the container."""

    class FormContainer(Vertical):
        ALLOW_MAXIMIZE = True
        DEFAULT_CSS = """
        FormContainer {
            width: 50%;
            border: blue;            
        }
        """

    class MaximizeApp(App):
        BINDINGS = [("m", "screen.maximize", "maximize focused widget")]

        def compose(self) -> ComposeResult:
            with FormContainer():
                yield Button("Hello")
                yield Button("World")
            yield Footer()

    assert snap_compare(MaximizeApp(), press=["m"])


def test_check_consume_keys(snap_compare):
    """Check that when an Input is focused it hides printable keys from the footer."""

    class MyApp(App):
        BINDINGS = [
            Binding(key="q", action="quit", description="Quit the app"),
            Binding(
                key="question_mark",
                action="help",
                description="Show help screen",
                key_display="?",
            ),
            Binding(key="delete", action="delete", description="Delete the thing"),
            Binding(key="j", action="down", description="Scroll down", show=False),
        ]

        def compose(self) -> ComposeResult:
            yield Input(placeholder="First Name")
            yield Input(placeholder="Last Name")
            yield Switch()
            yield Footer()

    assert snap_compare(MyApp())


def test_escape_to_minimize(snap_compare):
    """Check escape minimizes. Regression test for https://github.com/Textualize/textual/issues/4939"""

    TEXT = """\
    def hello(name):
        print("hello" + name)

    def goodbye(name):
        print("goodbye" + name)
    """

    class TextAreaExample(App):
        BINDINGS = [("ctrl+m", "screen.maximize")]
        CSS = """
        Screen {
            align: center middle;
        }

        #code-container {
            width: 20;
            height: 10;
        }
        """

        def compose(self) -> ComposeResult:
            with Vertical(id="code-container"):
                text_area = TextArea.code_editor(TEXT)
                text_area.cursor_blink = False
                yield text_area

    # ctrl+m to maximize, escape should minimize
    assert snap_compare(TextAreaExample(), press=["ctrl+m", "escape"])


def test_escape_to_minimize_disabled(snap_compare):
    """Set escape to minimize disabled by app"""

    TEXT = """\
    def hello(name):
        print("hello" + name)

    def goodbye(name):
        print("goodbye" + name)
    """

    class TextAreaExample(App):
        # Disables escape to minimize
        ESCAPE_TO_MINIMIZE = False
        BINDINGS = [("ctrl+m", "screen.maximize")]
        CSS = """
        Screen {
            align: center middle;
        }

        #code-container {
            width: 20;
            height: 10;
        }
        """

        def compose(self) -> ComposeResult:
            with Vertical(id="code-container"):
                text_area = TextArea.code_editor(TEXT)
                text_area.cursor_blink = False
                yield text_area

    # ctrl+m to maximize, escape should *not* minimize
    assert snap_compare(TextAreaExample(), press=["ctrl+m", "escape"])


def test_escape_to_minimize_screen_override(snap_compare):
    """Test escape to minimize can be overridden by the screen"""

    TEXT = """\
    def hello(name):
        print("hello" + name)

    def goodbye(name):
        print("goodbye" + name)
    """

    class TestScreen(Screen):
        # Disabled on the screen
        ESCAPE_TO_MINIMIZE = True

        def compose(self) -> ComposeResult:
            with Vertical(id="code-container"):
                text_area = TextArea.code_editor(TEXT)
                text_area.cursor_blink = False
                yield text_area

    class TextAreaExample(App):
        # Enabled on app
        ESCAPE_TO_MINIMIZE = False
        BINDINGS = [("ctrl+m", "screen.maximize")]
        CSS = """
        Screen {
            align: center middle;
        }

        #code-container {
            width: 20;
            height: 10;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("You are looking at the default screen")

        def on_mount(self) -> None:
            self.push_screen(TestScreen())

    # ctrl+m to maximize, escape *should* minimize
    assert snap_compare(TextAreaExample(), press=["ctrl+m", "escape"])


def test_app_focus_style(snap_compare):
    """Test that app blur style can be selected."""

    class FocusApp(App):
        CSS = """
        Label {
            padding: 1 2;
            margin: 1 2;
            background: $panel;
            border: $primary;
        }
        App:focus {
            .blurred {
                visibility: hidden;
            }
        }

        App:blur {
            .focussed {
                visibility: hidden;
            }
        }

        """

        def compose(self) -> ComposeResult:
            yield Label("BLURRED", classes="blurred")
            yield Label("FOCUSED", classes="focussed")

    async def run_before(pilot: Pilot) -> None:
        pilot.app.post_message(events.AppBlur())
        await pilot.pause()

    assert snap_compare(FocusApp(), run_before=run_before)


def test_ansi(snap_compare):
    """Test ANSI colors."""
    # It is actually impossible to tell from the SVG that ANSI colors were actually used
    # This snapshot test exists as a canary to check if ansi_colors have broken

    class ANSIApp(App):
        CSS = """
        Label {
            background: ansi_blue;
            border: solid ansi_white;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("[red]Red[/] [magenta]Magenta[/]")

    app = ANSIApp(ansi_color=True)
    assert snap_compare(app)


def test_ansi_command_palette(snap_compare):
    """Test command palette on top of ANSI colors."""

    class CommandPaletteApp(App[None]):
        CSS = """
        Label {
            width: 1fr;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("[red]Red[/] [magenta]Magenta[/] " * 200)

        def on_mount(self) -> None:
            self.action_command_palette()

    app = CommandPaletteApp(ansi_color=True)
    assert snap_compare(app)


def test_disabled(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5028"""

    class DisabledApp(App[None]):
        CSS = """
        Log {
            height: 4;
        }
        RichLog {
            height: 4;
        }
        DataTable {
            height: 4;
        }
        OptionList {
            height: 4;
        }
        SelectionList {
            height: 4;
        }
        """

        def compose(self) -> ComposeResult:
            yield Label("Labels don't have a disabled state", disabled=True)
            yield Log(disabled=True)
            yield RichLog(disabled=True)
            yield DataTable(disabled=True)
            yield OptionList("you", "can't", "select", "me", disabled=True)
            yield SelectionList(("Simple SelectionList", "", False), disabled=True)

        def on_mount(self) -> None:
            self.query_one(Log).write("I am disabled")
            self.query_one(RichLog).write("I am disabled")
            self.query_one(DataTable).add_columns("Foo", "Bar")
            self.query_one(DataTable).add_row("Also", "disabled")

    app = DisabledApp()
    assert snap_compare(app)


def test_keymap_bindings_display_footer_and_help_panel(snap_compare):
    """Bindings overridden by the Keymap are shown as expected in the Footer
    and help panel. Testing that the keys work as expected is done elsewhere.

    Footer should show bindings `k` to Increment, and `down` to Decrement.

    Key panel should show bindings `k, plus` to increment,
    and `down, minus, j` to decrement.

    """

    class Counter(App[None]):
        BINDINGS = [
            Binding(
                key="i,up",
                action="increment",
                description="Increment",
                id="app.increment",
            ),
            Binding(
                key="d,down",
                action="decrement",
                description="Decrement",
                id="app.decrement",
            ),
        ]

        def compose(self) -> ComposeResult:
            yield Label("Counter")
            yield Footer()

        def on_mount(self) -> None:
            self.action_show_help_panel()
            self.set_keymap(
                {
                    "app.increment": "k,plus",
                    "app.decrement": "down,minus,j",
                }
            )

    assert snap_compare(Counter())


def test_keymap_bindings_key_display(snap_compare):
    """If a default binding in `BINDINGS` has a key_display, it should be reset
    when that binding is overridden by a Keymap.

    The key_display should be taken from `App.get_key_display`, so in this case
    it should be "THIS IS CORRECT" in the Footer and help panel, not "INCORRECT".
    """

    class MyApp(App[None]):
        BINDINGS = [
            Binding(
                key="i,up",
                action="increment",
                description="Increment",
                id="app.increment",
                key_display="INCORRECT",
            ),
        ]

        def compose(self) -> ComposeResult:
            yield Label("Check the footer and help panel")
            yield Footer()

        def on_mount(self) -> None:
            self.action_show_help_panel()
            self.set_keymap({"app.increment": "k,plus,j,l"})

        def get_key_display(self, binding: Binding) -> str:
            if binding.id == "app.increment":
                return "correct"
            return super().get_key_display(binding)

    assert snap_compare(MyApp())


def test_missing_new_widgets(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5024"""

    class MRE(App):
        BINDINGS = [("z", "toggle_console", "Console")]
        CSS = """
        RichLog { border-top: dashed blue; height: 6; }
        .hidden { display: none; }
        """

        def compose(self):
            yield VerticalScroll()
            yield ProgressBar(
                classes="hidden"
            )  # removing or displaying this widget prevents the bug
            yield Footer()  # clicking "Console" in the footer prevents the bug
            yield RichLog(classes="hidden")

        def on_ready(self) -> None:
            self.query_one(RichLog).write("\n".join(f"line #{i}" for i in range(5)))

        def action_toggle_console(self) -> None:
            self.query_one(RichLog).toggle_class("hidden")

    app = MRE()
    assert snap_compare(app, press=["space", "space", "z"])


def test_pop_until_active(snap_compare):
    """End result should be screen showing 'BASE'"""

    class BaseScreen(Screen):
        def compose(self) -> ComposeResult:
            yield Label("BASE")

    class FooScreen(Screen):
        def compose(self) -> ComposeResult:
            yield Label("Foo")

    class BarScreen(Screen):
        BINDINGS = [("b", "app.make_base_active")]

        def compose(self) -> ComposeResult:
            yield Label("Bar")

    class PopApp(App):
        SCREENS = {"base": BaseScreen}

        async def on_mount(self) -> None:
            # Push base
            await self.push_screen("base")
            # Push two screens
            await self.push_screen(FooScreen())
            await self.push_screen(BarScreen())

        def action_make_base_active(self) -> None:
            self.get_screen("base").pop_until_active()

    app = PopApp()
    # App will push three screens
    # Pressing "b" will call pop_until_active, and pop two screens
    # End result should be screen showing "BASE"
    assert snap_compare(app, press=["b"])


def test_updates_with_auto_refresh(snap_compare):
    """Regression test for https://github.com/Textualize/textual/issues/5056

    After hiding and unhiding the RichLog, you should be able to see 1.5 fully rendered placeholder widgets.
    Prior to this fix, the bottom portion of the screen did not
    refresh after the RichLog was hidden/unhidden while in the presence of the auto-refreshing ProgressBar widget.
    """

    class MRE(App):
        BINDINGS = [
            ("z", "toggle_widget('RichLog')", "Console"),
        ]
        CSS = """
        Placeholder { height: 15; }
        RichLog { height: 6; }
        .hidden { display: none; }
        """

        def compose(self):
            with VerticalScroll():
                for i in range(10):
                    yield Placeholder()
            yield ProgressBar(classes="hidden")
            yield RichLog(classes="hidden")

        def on_ready(self) -> None:
            self.query_one(RichLog).write("\n".join(f"line #{i}" for i in range(5)))

        def action_toggle_widget(self, widget_type: str) -> None:
            self.query_one(widget_type).toggle_class("hidden")

    app = MRE()
    assert snap_compare(app, press=["z", "z"])


def test_push_screen_on_mount(snap_compare):
    """Test pushing (modal) screen immediately on mount, which was not refreshing the base screen.

    Should show a panel partially obscuring Hello World text

    """

    class QuitScreen(ModalScreen[None]):
        """Screen with a dialog to quit."""

        DEFAULT_CSS = """
        QuitScreen {
            align: center middle;
        }

        #dialog {
            grid-size: 2;
            grid-gutter: 1 2;
            grid-rows: 1fr 3;
            padding: 0 1;
            width: 60;
            height: 11;
            border: thick $primary 80%;
            background: $surface;
        }

        #question {
            column-span: 2;
            height: 1fr;
            width: 1fr;
            content-align: center middle;
        }

        Button {
            width: 100%;
        }
        """

        def compose(self) -> ComposeResult:
            yield Grid(
                Label("Are you sure you want to quit?", id="question"), id="dialog"
            )

    class MyApp(App[None]):
        def compose(self) -> ComposeResult:
            s = "Hello World Foo Bar Baz"
            yield Middle(Center(Static(s)))

        def on_mount(self) -> None:
            self.push_screen(QuitScreen())

    app = MyApp()

    assert snap_compare(app)


def test_transparent_background(snap_compare):
    """Check that a transparent background defers to render().

    This should display a colorful gradient, filling the screen.
    """

    COLORS = [
        "#881177",
        "#aa3355",
        "#cc6666",
        "#ee9944",
        "#eedd00",
        "#99dd55",
        "#44dd88",
        "#22ccbb",
        "#00bbcc",
        "#0099cc",
        "#3366bb",
        "#663399",
    ]

    class TransparentApp(App):
        CSS = """
        Screen {
            background: transparent;
        }
        """

        def render(self) -> LinearGradient:
            """Renders a gradient, when the background is transparent."""
            stops = [(i / (len(COLORS) - 1), c) for i, c in enumerate(COLORS)]
            return LinearGradient(30.0, stops)

    app = TransparentApp()
    snap_compare(app)


def test_maximize_allow(snap_compare):
    """Check that App.ALLOW_IN_MAXIMIZED_VIEW is the default.

    If working this should show a header, some text, a focused button, and more text.

    """

    class MaximizeApp(App):
        ALLOW_IN_MAXIMIZED_VIEW = "Header"
        BINDINGS = [("m", "screen.maximize", "maximize focused widget")]

        def compose(self) -> ComposeResult:
            yield Label(
                "Above", classes="-textual-system"
            )  # Allowed in maximize view because it has class -textual-system
            yield Header()  # Allowed because it matches ALLOW_IN_MAXIMIZED_VIEW
            yield Button("Hello")  # Allowed because it is the maximized widget
            yield Label(
                "Below", classes="-textual-system"
            )  # Allowed because it has class -textual-system
            yield Button("World")  # Not allowed
            yield Footer()  # Not allowed

    assert snap_compare(MaximizeApp(), press=["m"])
