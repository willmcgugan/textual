from pathlib import Path

import pytest

from tests.snapshot_tests.language_snippets import SNIPPETS
from textual.pilot import Pilot
from textual.widgets.text_area import Selection, BUILTIN_LANGUAGES
from textual.widgets import RichLog, TextArea, Input, Button
from textual.widgets.text_area import TextAreaTheme

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


def test_richlog_max_lines(snap_compare):
    assert snap_compare("snapshot_apps/richlog_max_lines.py", press=[*"abcde"])


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
            "e", "e", "down", "down", "down", "down", "e", "down", "d", "r"
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


def test_richlog_scroll(snap_compare):
    assert snap_compare(SNAPSHOT_APPS_DIR / "richlog_scroll.py")


def test_richlog_width(snap_compare):
    """Check that min_width applies in RichLog and that we can write
    to the RichLog when it's not visible, and it still renders as expected
    when made visible again."""

    async def setup(pilot):
        from rich.text import Text

        rich_log: RichLog = pilot.app.query_one(RichLog)
        rich_log.write(Text("hello1", style="on red", justify="right"), expand=True)
        rich_log.visible = False
        rich_log.write(Text("world2", style="on green", justify="right"), expand=True)
        rich_log.visible = True
        rich_log.write(Text("hello3", style="on blue", justify="right"), expand=True)
        rich_log.display = False
        rich_log.write(Text("world4", style="on yellow", justify="right"), expand=True)
        rich_log.display = True

    assert snap_compare(SNAPSHOT_APPS_DIR / "richlog_width.py", run_before=setup)


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
        await pilot.pause(0.3)
        await pilot.pause()

    assert snap_compare(SNAPSHOT_APPS_DIR / "tooltips.py", run_before=run_before)


def test_command_palette(snap_compare) -> None:
    async def run_before(pilot) -> None:
        # await pilot.press("ctrl+backslash")
        pilot.app.screen.query_one(Input).cursor_blink = False
        await pilot.press("A")
        await pilot.app.workers.wait_for_complete()

    assert snap_compare(SNAPSHOT_APPS_DIR / "command_palette.py", run_before=run_before)


def test_command_palette_discovery(snap_compare) -> None:
    async def run_before(pilot) -> None:
        pilot.app.screen.query_one(Input).cursor_blink = False
        await pilot.app.workers.wait_for_complete()

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
        press=["ctrl+backslash", "r", "e", "d", "down", "enter"],
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
