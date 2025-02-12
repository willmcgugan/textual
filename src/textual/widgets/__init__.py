from __future__ import annotations

import typing
from importlib import import_module

from textual.case import camel_to_snake

# For any new built-in Widget we create, not only do we have to import them here and add them to `__all__`,
# but also to the `__init__.pyi` file in this same folder - otherwise text editors and type checkers won't
# be able to "see" them.
if typing.TYPE_CHECKING:
    from textual.widget import Widget
    from textual.widgets._button import Button
    from textual.widgets._checkbox import Checkbox
    from textual.widgets._collapsible import Collapsible
    from textual.widgets._content_switcher import ContentSwitcher
    from textual.widgets._data_table import DataTable
    from textual.widgets._digits import Digits
    from textual.widgets._directory_tree import DirectoryTree
    from textual.widgets._footer import Footer
    from textual.widgets._header import Header
    from textual.widgets._help_panel import HelpPanel
    from textual.widgets._input import Input
    from textual.widgets._key_panel import KeyPanel
    from textual.widgets._label import Label
    from textual.widgets._link import Link
    from textual.widgets._list_item import ListItem
    from textual.widgets._list_view import ListView
    from textual.widgets._loading_indicator import LoadingIndicator
    from textual.widgets._log import Log
    from textual.widgets._markdown import Markdown, MarkdownViewer
    from textual.widgets._masked_input import MaskedInput
    from textual.widgets._month_calendar import MonthCalendar
    from textual.widgets._option_list import OptionList
    from textual.widgets._placeholder import Placeholder
    from textual.widgets._pretty import Pretty
    from textual.widgets._progress_bar import ProgressBar
    from textual.widgets._radio_button import RadioButton
    from textual.widgets._radio_set import RadioSet
    from textual.widgets._rich_log import RichLog
    from textual.widgets._rule import Rule
    from textual.widgets._select import Select
    from textual.widgets._selection_list import SelectionList
    from textual.widgets._sparkline import Sparkline
    from textual.widgets._static import Static
    from textual.widgets._switch import Switch
    from textual.widgets._tabbed_content import TabbedContent, TabPane
    from textual.widgets._tabs import Tab, Tabs
    from textual.widgets._text_area import TextArea
    from textual.widgets._tooltip import Tooltip
    from textual.widgets._tree import Tree
    from textual.widgets._welcome import Welcome

__all__ = [
    "Button",
    "Checkbox",
    "Collapsible",
    "ContentSwitcher",
    "DataTable",
    "Digits",
    "DirectoryTree",
    "Footer",
    "Header",
    "HelpPanel",
    "Input",
    "KeyPanel",
    "Label",
    "Link",
    "ListItem",
    "ListView",
    "LoadingIndicator",
    "Log",
    "Markdown",
    "MarkdownViewer",
    "MaskedInput",
    "MonthCalendar",
    "OptionList",
    "Placeholder",
    "Pretty",
    "ProgressBar",
    "RadioButton",
    "RadioSet",
    "RichLog",
    "Rule",
    "Select",
    "SelectionList",
    "Sparkline",
    "Static",
    "Switch",
    "Tab",
    "TabbedContent",
    "TabPane",
    "Tabs",
    "TextArea",
    "Tooltip",
    "Tree",
    "Welcome",
]

_WIDGETS_LAZY_LOADING_CACHE: dict[str, type[Widget]] = {}


# Let's decrease startup time by lazy loading our Widgets:
def __getattr__(widget_class: str) -> type[Widget]:
    try:
        return _WIDGETS_LAZY_LOADING_CACHE[widget_class]
    except KeyError:
        pass

    if widget_class not in __all__:
        raise AttributeError(f"Package 'textual.widgets' has no class '{widget_class}'")

    widget_module_path = f"._{camel_to_snake(widget_class)}"
    module = import_module(widget_module_path, package="textual.widgets")
    class_ = getattr(module, widget_class)

    _WIDGETS_LAZY_LOADING_CACHE[widget_class] = class_
    return class_
