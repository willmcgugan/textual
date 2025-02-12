from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Callable, Iterable, Iterator, Literal, cast

import rich.repr
from rich.style import Style
from typing_extensions import TypedDict

from textual._animator import DEFAULT_EASING, Animatable, BoundAnimator, EasingFunction
from textual._types import AnimationLevel, CallbackType
from textual.color import Color
from textual.css._style_properties import (
    AlignProperty,
    BooleanProperty,
    BorderProperty,
    BoxProperty,
    ColorProperty,
    DockProperty,
    FractionalProperty,
    HatchProperty,
    IntegerProperty,
    KeylineProperty,
    LayoutProperty,
    NameListProperty,
    NameProperty,
    OffsetProperty,
    OverflowProperty,
    ScalarListProperty,
    ScalarProperty,
    ScrollbarColorProperty,
    SpacingProperty,
    SplitProperty,
    StringEnumProperty,
    StyleFlagsProperty,
    TransitionsProperty,
)
from textual.css.constants import (
    VALID_ALIGN_HORIZONTAL,
    VALID_ALIGN_VERTICAL,
    VALID_BOX_SIZING,
    VALID_CONSTRAIN,
    VALID_DISPLAY,
    VALID_OVERFLOW,
    VALID_OVERLAY,
    VALID_POSITION,
    VALID_SCROLLBAR_GUTTER,
    VALID_TEXT_ALIGN,
    VALID_TEXT_OVERFLOW,
    VALID_TEXT_WRAP,
    VALID_VISIBILITY,
)
from textual.css.scalar import Scalar, ScalarOffset, Unit
from textual.css.scalar_animation import ScalarAnimation
from textual.css.transition import Transition
from textual.css.types import (
    AlignHorizontal,
    AlignVertical,
    BoxSizing,
    Constrain,
    Display,
    Overflow,
    Overlay,
    ScrollbarGutter,
    Specificity3,
    Specificity6,
    TextAlign,
    TextOverflow,
    TextWrap,
    Visibility,
)
from textual.geometry import Offset, Spacing

if TYPE_CHECKING:
    from textual.css.types import CSSLocation
    from textual.dom import DOMNode
    from textual.layout import Layout


class RulesMap(TypedDict, total=False):
    """A typed dict for CSS rules.

    Any key may be absent, indicating that rule has not been set.

    Does not define composite rules, that is a rule that is made of a combination of other rules.
    """

    display: Display
    visibility: Visibility
    layout: "Layout"

    auto_color: bool
    color: Color
    background: Color
    text_style: Style

    background_tint: Color

    opacity: float
    text_opacity: float

    padding: Spacing
    margin: Spacing
    offset: ScalarOffset
    position: str

    border_top: tuple[str, Color]
    border_right: tuple[str, Color]
    border_bottom: tuple[str, Color]
    border_left: tuple[str, Color]

    border_title_align: AlignHorizontal
    border_subtitle_align: AlignHorizontal

    outline_top: tuple[str, Color]
    outline_right: tuple[str, Color]
    outline_bottom: tuple[str, Color]
    outline_left: tuple[str, Color]

    keyline: tuple[str, Color]

    box_sizing: BoxSizing
    width: Scalar
    height: Scalar
    min_width: Scalar
    min_height: Scalar
    max_width: Scalar
    max_height: Scalar

    dock: str
    split: str

    overflow_x: Overflow
    overflow_y: Overflow

    layers: tuple[str, ...]
    layer: str

    transitions: dict[str, Transition]

    tint: Color

    scrollbar_color: Color
    scrollbar_color_hover: Color
    scrollbar_color_active: Color

    scrollbar_corner_color: Color

    scrollbar_background: Color
    scrollbar_background_hover: Color
    scrollbar_background_active: Color

    scrollbar_gutter: ScrollbarGutter

    scrollbar_size_vertical: int
    scrollbar_size_horizontal: int

    align_horizontal: AlignHorizontal
    align_vertical: AlignVertical

    content_align_horizontal: AlignHorizontal
    content_align_vertical: AlignVertical

    grid_size_rows: int
    grid_size_columns: int
    grid_gutter_horizontal: int
    grid_gutter_vertical: int
    grid_rows: tuple[Scalar, ...]
    grid_columns: tuple[Scalar, ...]

    row_span: int
    column_span: int

    text_align: TextAlign

    link_color: Color
    auto_link_color: bool
    link_background: Color
    link_style: Style

    link_color_hover: Color
    auto_link_color_hover: bool
    link_background_hover: Color
    link_style_hover: Style

    auto_border_title_color: bool
    border_title_color: Color
    border_title_background: Color
    border_title_style: Style

    auto_border_subtitle_color: bool
    border_subtitle_color: Color
    border_subtitle_background: Color
    border_subtitle_style: Style

    hatch: tuple[str, Color] | Literal["none"]

    overlay: Overlay
    constrain_x: Constrain
    constrain_y: Constrain

    text_wrap: TextWrap
    text_overflow: TextOverflow


RULE_NAMES = list(RulesMap.__annotations__.keys())
RULE_NAMES_SET = frozenset(RULE_NAMES)
_rule_getter = attrgetter(*RULE_NAMES)


class StylesBase:
    """A common base class for Styles and RenderStyles"""

    ANIMATABLE = {
        "offset",
        "padding",
        "margin",
        "width",
        "height",
        "min_width",
        "min_height",
        "max_width",
        "max_height",
        "auto_color",
        "color",
        "background",
        "background_tint",
        "opacity",
        "position",
        "text_opacity",
        "tint",
        "scrollbar_color",
        "scrollbar_color_hover",
        "scrollbar_color_active",
        "scrollbar_background",
        "scrollbar_background_hover",
        "scrollbar_background_active",
        "link_color",
        "link_background",
        "link_color_hover",
        "link_background_hover",
        "text_wrap",
        "text_overflow",
    }

    node: DOMNode | None = None

    display = StringEnumProperty(VALID_DISPLAY, "block", layout=True)
    """Set the display of the widget, defining how it's rendered.

    Valid values are "block" or "none".
    
    "none" will hide and allow other widgets to fill the space that this widget would occupy.
    
    Set to None to clear any value that was set at runtime.

    Raises:
        StyleValueError: If an invalid display is specified.
    """

    visibility = StringEnumProperty(VALID_VISIBILITY, "visible", layout=True)
    """Set the visibility of the widget.
    
    Valid values are "visible" or "hidden".

    "hidden" will hide the widget, but reserve the space for this widget.
    If you want to hide the widget and allow another widget to fill the space,
    set the display attribute to "none" instead.
    
    Set to None to clear any value that was set at runtime.

    Raises:
        StyleValueError: If an invalid visibility is specified.
    """

    layout = LayoutProperty()
    """Set the layout of the widget, defining how it's children are laid out.
    
    Valid values are "grid", "horizontal", and "vertical" or None to clear any layout
    that was set at runtime.

    Raises:
        MissingLayout: If an invalid layout is specified.
    """

    auto_color = BooleanProperty(default=False)
    """Enable automatic picking of best contrasting color."""
    color = ColorProperty(Color(255, 255, 255))
    """Set the foreground (text) color of the widget.
    Supports `Color` objects but also strings e.g. "red" or "#ff0000".
    You can also specify an opacity after a color e.g. "blue 10%"
    """
    background = ColorProperty(Color(0, 0, 0, 0))
    """Set the background color of the widget.
    Supports `Color` objects but also strings e.g. "red" or "#ff0000"
    You can also specify an opacity after a color e.g. "blue 10%"
    """
    background_tint = ColorProperty(Color(0, 0, 0, 0))
    """Set a color to tint (blend) with the background.
    Supports `Color` objects but also strings e.g. "red" or "#ff0000"
    You can also specify an opacity after a color e.g. "blue 10%"   
    """
    text_style = StyleFlagsProperty()
    """Set the text style of the widget using Rich StyleFlags.
    e.g. `"bold underline"` or `"b u strikethrough"`.
    """
    opacity = FractionalProperty(children=True)
    """Set the opacity of the widget, defining how it blends with the parent."""
    text_opacity = FractionalProperty()
    """Set the opacity of the content within the widget against the widget's background."""
    padding = SpacingProperty()
    """Set the padding (spacing between border and content) of the widget."""
    margin = SpacingProperty()
    """Set the margin (spacing outside the border) of the widget."""
    offset = OffsetProperty()
    """Set the offset of the widget relative to where it would have been otherwise."""
    position = StringEnumProperty(VALID_POSITION, "relative")
    """If `relative` offset is applied to widgets current position, if `absolute` it is applied to (0, 0)."""

    border = BorderProperty(layout=True)
    """Set the border of the widget e.g. ("round", "green") or "none"."""

    border_top = BoxProperty(Color(0, 255, 0))
    """Set the top border of the widget e.g. ("round", "green") or "none"."""
    border_right = BoxProperty(Color(0, 255, 0))
    """Set the right border of the widget e.g. ("round", "green") or "none"."""
    border_bottom = BoxProperty(Color(0, 255, 0))
    """Set the bottom border of the widget e.g. ("round", "green") or "none"."""
    border_left = BoxProperty(Color(0, 255, 0))
    """Set the left border of the widget e.g. ("round", "green") or "none"."""

    border_title_align = StringEnumProperty(VALID_ALIGN_HORIZONTAL, "left")
    """The alignment of the border title text."""
    border_subtitle_align = StringEnumProperty(VALID_ALIGN_HORIZONTAL, "right")
    """The alignment of the border subtitle text."""

    outline = BorderProperty(layout=False)
    """Set the outline of the widget e.g. ("round", "green") or "none".
    The outline is drawn *on top* of the widget, rather than around it like border.
    """
    outline_top = BoxProperty(Color(0, 255, 0))
    """Set the top outline of the widget e.g. ("round", "green") or "none"."""
    outline_right = BoxProperty(Color(0, 255, 0))
    """Set the right outline of the widget e.g. ("round", "green") or "none"."""
    outline_bottom = BoxProperty(Color(0, 255, 0))
    """Set the bottom outline of the widget e.g. ("round", "green") or "none"."""
    outline_left = BoxProperty(Color(0, 255, 0))
    """Set the left outline of the widget e.g. ("round", "green") or "none"."""

    keyline = KeylineProperty()
    """Keyline parameters."""

    box_sizing = StringEnumProperty(VALID_BOX_SIZING, "border-box", layout=True)
    """Box sizing method ("border-box" or "conetnt-box")"""
    width = ScalarProperty(percent_unit=Unit.WIDTH)
    """Set the width of the widget."""
    height = ScalarProperty(percent_unit=Unit.HEIGHT)
    """Set the height of the widget."""
    min_width = ScalarProperty(percent_unit=Unit.WIDTH, allow_auto=False)
    """Set the minimum width of the widget."""
    min_height = ScalarProperty(percent_unit=Unit.HEIGHT, allow_auto=False)
    """Set the minimum height of the widget."""
    max_width = ScalarProperty(percent_unit=Unit.WIDTH, allow_auto=False)
    """Set the maximum width of the widget."""
    max_height = ScalarProperty(percent_unit=Unit.HEIGHT, allow_auto=False)
    """Set the maximum height of the widget."""
    dock = DockProperty()
    """Set which edge of the parent to dock this widget to e.g. "top", "left", "right", "bottom", "none".
    """
    split = SplitProperty()

    overflow_x = OverflowProperty(VALID_OVERFLOW, "hidden")
    """Control what happens when the content extends horizontally beyond the widget's width.

    Valid values are "scroll", "hidden", or "auto".
    """

    overflow_y = OverflowProperty(VALID_OVERFLOW, "hidden")
    """Control what happens when the content extends vertically beyond the widget's height.

    Valid values are "scroll", "hidden", or "auto".
    """

    layer = NameProperty()
    layers = NameListProperty()
    transitions = TransitionsProperty()

    tint = ColorProperty("transparent")
    """Set the tint of the widget. This allows you apply a opaque color above the widget.

    You can specify an opacity after a color e.g. "blue 10%"
    """
    scrollbar_color = ScrollbarColorProperty("ansi_bright_magenta")
    """Set the color of the handle of the scrollbar."""
    scrollbar_color_hover = ScrollbarColorProperty("ansi_yellow")
    """Set the color of the handle of the scrollbar when hovered."""
    scrollbar_color_active = ScrollbarColorProperty("ansi_bright_yellow")
    """Set the color of the handle of the scrollbar when active (being dragged)."""
    scrollbar_corner_color = ScrollbarColorProperty("#666666")
    """Set the color of the space between the horizontal and vertical scrollbars."""
    scrollbar_background = ScrollbarColorProperty("#555555")
    """Set the background color of the scrollbar (the track that the handle sits on)."""
    scrollbar_background_hover = ScrollbarColorProperty("#444444")
    """Set the background color of the scrollbar when hovered."""
    scrollbar_background_active = ScrollbarColorProperty("black")
    """Set the background color of the scrollbar when active (being dragged)."""

    scrollbar_gutter = StringEnumProperty(
        VALID_SCROLLBAR_GUTTER, "auto", layout=True, refresh_children=True
    )
    """Set to "stable" to reserve space for the scrollbar even when it's not visible.
    This can prevent content from shifting when a scrollbar appears.
    """

    scrollbar_size_vertical = IntegerProperty(default=2, layout=True)
    """Set the width of the vertical scrollbar (measured in cells)."""
    scrollbar_size_horizontal = IntegerProperty(default=1, layout=True)
    """Set the height of the horizontal scrollbar (measured in cells)."""

    align_horizontal = StringEnumProperty(
        VALID_ALIGN_HORIZONTAL, "left", layout=True, refresh_children=True
    )
    align_vertical = StringEnumProperty(
        VALID_ALIGN_VERTICAL, "top", layout=True, refresh_children=True
    )
    align = AlignProperty()

    content_align_horizontal = StringEnumProperty(VALID_ALIGN_HORIZONTAL, "left")
    content_align_vertical = StringEnumProperty(VALID_ALIGN_VERTICAL, "top")
    content_align = AlignProperty()

    grid_rows = ScalarListProperty(percent_unit=Unit.HEIGHT, refresh_children=True)
    grid_columns = ScalarListProperty(percent_unit=Unit.WIDTH, refresh_children=True)

    grid_size_columns = IntegerProperty(default=1, layout=True, refresh_children=True)
    grid_size_rows = IntegerProperty(default=0, layout=True, refresh_children=True)
    grid_gutter_horizontal = IntegerProperty(
        default=0, layout=True, refresh_children=True
    )
    grid_gutter_vertical = IntegerProperty(
        default=0, layout=True, refresh_children=True
    )

    row_span = IntegerProperty(default=1, layout=True)
    column_span = IntegerProperty(default=1, layout=True)

    text_align: StringEnumProperty[TextAlign] = StringEnumProperty(
        VALID_TEXT_ALIGN, "start"
    )

    link_color = ColorProperty("transparent")
    auto_link_color = BooleanProperty(False)
    link_background = ColorProperty("transparent")
    link_style = StyleFlagsProperty()

    link_color_hover = ColorProperty("transparent")
    auto_link_color_hover = BooleanProperty(False)
    link_background_hover = ColorProperty("transparent")
    link_style_hover = StyleFlagsProperty()

    auto_border_title_color = BooleanProperty(default=False)
    border_title_color = ColorProperty(Color(255, 255, 255, 0))
    border_title_background = ColorProperty(Color(0, 0, 0, 0))
    border_title_style = StyleFlagsProperty()

    auto_border_subtitle_color = BooleanProperty(default=False)
    border_subtitle_color = ColorProperty(Color(255, 255, 255, 0))
    border_subtitle_background = ColorProperty(Color(0, 0, 0, 0))
    border_subtitle_style = StyleFlagsProperty()

    hatch = HatchProperty()
    """Add a hatched background effect e.g. ("right", "yellow") or "none" to use no hatch.
    """

    overlay = StringEnumProperty(
        VALID_OVERLAY, "none", layout=True, refresh_parent=True
    )
    constrain_x: StringEnumProperty[Constrain] = StringEnumProperty(
        VALID_CONSTRAIN, "none"
    )
    constrain_y: StringEnumProperty[Constrain] = StringEnumProperty(
        VALID_CONSTRAIN, "none"
    )
    text_wrap: StringEnumProperty[TextWrap] = StringEnumProperty(
        VALID_TEXT_WRAP, "wrap"
    )
    text_overflow: StringEnumProperty[TextOverflow] = StringEnumProperty(
        VALID_TEXT_OVERFLOW, "fold"
    )

    def __textual_animation__(
        self,
        attribute: str,
        start_value: object,
        value: object,
        start_time: float,
        duration: float | None,
        speed: float | None,
        easing: EasingFunction,
        on_complete: CallbackType | None = None,
        level: AnimationLevel = "full",
    ) -> ScalarAnimation | None:
        if self.node is None:
            return None

        # Check we are animating a Scalar or Scalar offset
        if isinstance(start_value, (Scalar, ScalarOffset)):
            # If destination is a number, we can convert that to a scalar
            if isinstance(value, (int, float)):
                value = Scalar(value, Unit.CELLS, Unit.CELLS)

            # We can only animate to Scalar
            if not isinstance(value, (Scalar, ScalarOffset)):
                return None

            from textual.widget import Widget

            assert isinstance(self.node, Widget)
            return ScalarAnimation(
                self.node,
                self,
                start_time,
                attribute,
                value,
                duration=duration,
                speed=speed,
                easing=easing,
                on_complete=(
                    partial(self.node.app.call_later, on_complete)
                    if on_complete is not None
                    else None
                ),
                level=level,
            )
        return None

    def __eq__(self, styles: object) -> bool:
        """Check that Styles contains the same rules."""
        if not isinstance(styles, StylesBase):
            return NotImplemented
        return self.get_rules() == styles.get_rules()

    def __getitem__(self, key: str) -> object:
        if key not in RULE_NAMES_SET:
            raise KeyError(key)
        return getattr(self, key)

    def get(self, key: str, default: object | None = None) -> object:
        return getattr(self, key) if key in RULE_NAMES_SET else default

    def __len__(self) -> int:
        return len(RULE_NAMES)

    def __iter__(self) -> Iterator[str]:
        return iter(RULE_NAMES)

    def __contains__(self, key: object) -> bool:
        return key in RULE_NAMES_SET

    def keys(self) -> Iterable[str]:
        return RULE_NAMES

    def values(self) -> Iterable[object]:
        for key in RULE_NAMES:
            yield getattr(self, key)

    def items(self) -> Iterable[tuple[str, object]]:
        get_rule = self.get_rule
        for key in RULE_NAMES:
            yield (key, getattr(self, key))

    @property
    def gutter(self) -> Spacing:
        """Get space around widget.

        Returns:
            Space around widget content.
        """
        return self.padding + self.border.spacing

    @property
    def auto_dimensions(self) -> bool:
        """Check if width or height are set to 'auto'."""
        has_rule = self.has_rule
        return (has_rule("width") and self.width.is_auto) or (  # type: ignore
            has_rule("height") and self.height.is_auto  # type: ignore
        )

    @property
    def is_relative_width(self, _relative_units={Unit.FRACTION, Unit.PERCENT}) -> bool:
        """Does the node have a relative width?"""
        width = self.width
        return width is not None and width.unit in _relative_units

    @property
    def is_relative_height(self, _relative_units={Unit.FRACTION, Unit.PERCENT}) -> bool:
        """Does the node have a relative width?"""
        height = self.height
        return height is not None and height.unit in _relative_units

    @property
    def is_auto_width(self, _auto=Unit.AUTO) -> bool:
        """Does the node have automatic width?"""
        width = self.width
        return width is not None and width.unit == _auto

    @property
    def is_auto_height(self, _auto=Unit.AUTO) -> bool:
        """Does the node have automatic height?"""
        height = self.height
        return height is not None and height.unit == _auto

    @property
    def is_dynamic_height(
        self, _dynamic_units={Unit.AUTO, Unit.FRACTION, Unit.PERCENT}
    ) -> bool:
        """Does the node have a dynamic (not fixed) height?"""
        height = self.height
        return height is not None and height.unit in _dynamic_units

    @property
    def is_docked(self) -> bool:
        """Is the node docked?"""
        return self.dock != "none"

    @property
    def is_split(self) -> bool:
        """Is the node split?"""
        return self.split != "none"

    def has_rule(self, rule_name: str) -> bool:
        """Check if a rule is set on this Styles object.

        Args:
            rule_name: Rule name.

        Returns:
            ``True`` if the rules is present, otherwise ``False``.
        """
        raise NotImplementedError()

    def clear_rule(self, rule_name: str) -> bool:
        """Removes the rule from the Styles object, as if it had never been set.

        Args:
            rule_name: Rule name.

        Returns:
            ``True`` if a rule was cleared, or ``False`` if the rule is already not set.
        """
        raise NotImplementedError()

    def get_rules(self) -> RulesMap:
        """Get the rules in a mapping.

        Returns:
            A TypedDict of the rules.
        """
        raise NotImplementedError()

    def set_rule(self, rule_name: str, value: object | None) -> bool:
        """Set a rule.

        Args:
            rule_name: Rule name.
            value: New rule value.

        Returns:
            ``True`` if the rule changed, otherwise ``False``.
        """
        raise NotImplementedError()

    def get_rule(self, rule_name: str, default: object = None) -> object:
        """Get an individual rule.

        Args:
            rule_name: Name of rule.
            default: Default if rule does not exists.

        Returns:
            Rule value or default.
        """
        raise NotImplementedError()

    def refresh(
        self,
        *,
        layout: bool = False,
        children: bool = False,
        parent: bool = False,
        repaint: bool = True,
    ) -> None:
        """Mark the styles as requiring a refresh.

        Args:
            layout: Also require a layout.
            children: Also refresh children.
            parent: Also refresh the parent.
            repaint: Repaint the widgets.
        """

    def reset(self) -> None:
        """Reset the rules to initial state."""

    def merge(self, other: StylesBase) -> None:
        """Merge values from another Styles.

        Args:
            other: A Styles object.
        """

    def merge_rules(self, rules: RulesMap) -> None:
        """Merge rules into Styles.

        Args:
            rules: A mapping of rules.
        """

    def get_render_rules(self) -> RulesMap:
        """Get rules map with defaults."""
        # Get a dictionary of rules, going through the properties
        rules = dict(zip(RULE_NAMES, _rule_getter(self)))
        return cast(RulesMap, rules)

    @classmethod
    def is_animatable(cls, rule: str) -> bool:
        """Check if a given rule may be animated.

        Args:
            rule: Name of the rule.

        Returns:
            ``True`` if the rule may be animated, otherwise ``False``.
        """
        return rule in cls.ANIMATABLE

    @classmethod
    def parse(
        cls, css: str, read_from: CSSLocation, *, node: DOMNode | None = None
    ) -> Styles:
        """Parse CSS and return a Styles object.

        Args:
            css: Textual CSS.
            read_from: Location where the CSS was read from.
            node: Node to associate with the Styles.

        Returns:
            A Styles instance containing result of parsing CSS.
        """
        from textual.css.parse import parse_declarations

        styles = parse_declarations(css, read_from)
        styles.node = node
        return styles

    def _get_transition(self, key: str) -> Transition | None:
        """Get a transition.

        Args:
            key: Transition key.

        Returns:
            Transition object or None it no transition exists.
        """
        if key in self.ANIMATABLE:
            return self.transitions.get(key, None)
        else:
            return None

    def _align_width(self, width: int, parent_width: int) -> int:
        """Align the width dimension.

        Args:
            width: Width of the content.
            parent_width: Width of the parent container.

        Returns:
            An offset to add to the X coordinate.
        """
        offset_x = 0
        align_horizontal = self.align_horizontal
        if align_horizontal != "left":
            if align_horizontal == "center":
                offset_x = (parent_width - width) // 2
            else:
                offset_x = parent_width - width

        return offset_x

    def _align_height(self, height: int, parent_height: int) -> int:
        """Align the height dimensions

        Args:
            height: Height of the content.
            parent_height: Height of the parent container.

        Returns:
            An offset to add to the Y coordinate.
        """
        offset_y = 0
        align_vertical = self.align_vertical
        if align_vertical != "top":
            if align_vertical == "middle":
                offset_y = (parent_height - height) // 2
            else:
                offset_y = parent_height - height
        return offset_y

    def _align_size(self, child: tuple[int, int], parent: tuple[int, int]) -> Offset:
        """Align a size according to alignment rules.

        Args:
            child: The size of the child (width, height)
            parent: The size of the parent (width, height)

        Returns:
            Offset required to align the child.
        """
        width, height = child
        parent_width, parent_height = parent
        return Offset(
            self._align_width(width, parent_width),
            self._align_height(height, parent_height),
        )

    @property
    def partial_rich_style(self) -> Style:
        """Get the style properties associated with this node only (not including parents in the DOM).

        Returns:
            Rich Style object.
        """
        style = Style(
            color=(
                self.color.rich_color
                if self.has_rule("color") and self.color.a > 0
                else None
            ),
            bgcolor=(
                self.background.rich_color
                if self.has_rule("background") and self.background.a > 0
                else None
            ),
        )
        style += self.text_style
        return style


@rich.repr.auto
@dataclass
class Styles(StylesBase):
    node: DOMNode | None = None
    _rules: RulesMap = field(default_factory=RulesMap)
    _updates: int = 0

    important: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.get_rule: Callable[[str, object], object] = self._rules.get  # type: ignore[assignment]
        self.has_rule: Callable[[str], bool] = self._rules.__contains__  # type: ignore[assignment]

    def copy(self) -> Styles:
        """Get a copy of this Styles object."""
        return Styles(
            node=self.node,
            _rules=self.get_rules(),
            important=self.important,
        )

    def clear_rule(self, rule_name: str) -> bool:
        """Removes the rule from the Styles object, as if it had never been set.

        Args:
            rule_name: Rule name.

        Returns:
            ``True`` if a rule was cleared, or ``False`` if it was already not set.
        """
        changed = self._rules.pop(rule_name, None) is not None  # type: ignore
        if changed:
            self._updates += 1
        return changed

    def get_rules(self) -> RulesMap:
        return self._rules.copy()

    def set_rule(self, rule: str, value: object | None) -> bool:
        """Set a rule.

        Args:
            rule: Rule name.
            value: New rule value.

        Returns:
            ``True`` if the rule changed, otherwise ``False``.
        """
        if value is None:
            changed = self._rules.pop(rule, None) is not None  # type: ignore
            if changed:
                self._updates += 1
            return changed
        current = self._rules.get(rule)
        self._rules[rule] = value  # type: ignore
        changed = current != value
        if changed:
            self._updates += 1
        return changed

    def refresh(
        self,
        *,
        layout: bool = False,
        children: bool = False,
        parent: bool = False,
        repaint=True,
    ) -> None:
        node = self.node
        if node is None or not node._is_mounted:
            return
        if parent and node._parent is not None:
            node._parent.refresh(repaint=repaint)
        node.refresh(layout=layout)
        if children:
            for child in node.walk_children(with_self=False, reverse=True):
                child.refresh(layout=layout, repaint=repaint)

    def reset(self) -> None:
        """Reset the rules to initial state."""
        self._updates += 1
        self._rules.clear()  # type: ignore

    def merge(self, other: StylesBase) -> None:
        """Merge values from another Styles.

        Args:
            other: A Styles object.
        """
        self._updates += 1
        self._rules.update(other.get_rules())

    def merge_rules(self, rules: RulesMap) -> None:
        self._updates += 1
        self._rules.update(rules)

    def extract_rules(
        self,
        specificity: Specificity3,
        is_default_rules: bool = False,
        tie_breaker: int = 0,
    ) -> list[tuple[str, Specificity6, Any]]:
        """Extract rules from Styles object, and apply !important css specificity as
        well as higher specificity of user CSS vs widget CSS.

        Args:
            specificity: A node specificity.
            is_default_rules: True if the rules we're extracting are
                default (i.e. in Widget.DEFAULT_CSS) rules. False if they're from user defined CSS.

        Returns:
            A list containing a tuple of <RULE NAME>, <SPECIFICITY> <RULE VALUE>.
        """
        is_important = self.important.__contains__
        default_rules = 0 if is_default_rules else 1
        rules: list[tuple[str, Specificity6, Any]] = [
            (
                rule_name,
                (
                    default_rules,
                    1 if is_important(rule_name) else 0,
                    *specificity,
                    tie_breaker,
                ),
                rule_value,
            )
            for rule_name, rule_value in self._rules.items()
        ]

        return rules

    def __rich_repr__(self) -> rich.repr.Result:
        has_rule = self.has_rule
        for name in RULE_NAMES:
            if has_rule(name):
                yield name, getattr(self, name)
        if self.important:
            yield "important", self.important

    def _get_border_css_lines(
        self, rules: RulesMap, name: str
    ) -> Iterable[tuple[str, str]]:
        """Get pairs of strings containing <RULE NAME>, <RULE VALUE> for border css declarations.

        Args:
            rules: A rules map.
            name: Name of rules (border or outline)

        Returns:
            An iterable of CSS declarations.
        """

        has_rule = rules.__contains__
        get_rule = rules.__getitem__

        has_top = has_rule(f"{name}_top")
        has_right = has_rule(f"{name}_right")
        has_bottom = has_rule(f"{name}_bottom")
        has_left = has_rule(f"{name}_left")
        if not any((has_top, has_right, has_bottom, has_left)):
            # No border related rules
            return

        if all((has_top, has_right, has_bottom, has_left)):
            # All rules are set
            # See if we can set them with a single border: declaration
            top = get_rule(f"{name}_top")
            right = get_rule(f"{name}_right")
            bottom = get_rule(f"{name}_bottom")
            left = get_rule(f"{name}_left")

            if top == right and right == bottom and bottom == left:
                border_type, border_color = rules[f"{name}_top"]  # type: ignore
                yield name, f"{border_type} {border_color.hex}"
                return

        # Check for edges
        if has_top:
            border_type, border_color = rules[f"{name}_top"]  # type: ignore
            yield f"{name}-top", f"{border_type} {border_color.hex}"

        if has_right:
            border_type, border_color = rules[f"{name}_right"]  # type: ignore
            yield f"{name}-right", f"{border_type} {border_color.hex}"

        if has_bottom:
            border_type, border_color = rules[f"{name}_bottom"]  # type: ignore
            yield f"{name}-bottom", f"{border_type} {border_color.hex}"

        if has_left:
            border_type, border_color = rules[f"{name}_left"]  # type: ignore
            yield f"{name}-left", f"{border_type} {border_color.hex}"

    @property
    def css_lines(self) -> list[str]:
        lines: list[str] = []
        append = lines.append

        def append_declaration(name: str, value: str) -> None:
            if name in self.important:
                append(f"{name}: {value} !important;")
            else:
                append(f"{name}: {value};")

        rules = self.get_rules()
        get_rule = rules.get

        if "display" in rules:
            append_declaration("display", rules["display"])
        if "visibility" in rules:
            append_declaration("visibility", rules["visibility"])
        if "padding" in rules:
            append_declaration("padding", rules["padding"].css)
        if "margin" in rules:
            append_declaration("margin", rules["margin"].css)

        for name, rule in self._get_border_css_lines(rules, "border"):
            append_declaration(name, rule)

        for name, rule in self._get_border_css_lines(rules, "outline"):
            append_declaration(name, rule)

        if "offset" in rules:
            x, y = self.offset
            append_declaration("offset", f"{x} {y}")
        if "position" in rules:
            append_declaration("position", self.position)
        if "dock" in rules:
            append_declaration("dock", rules["dock"])
        if "split" in rules:
            append_declaration("split", rules["split"])
        if "layers" in rules:
            append_declaration("layers", " ".join(self.layers))
        if "layer" in rules:
            append_declaration("layer", self.layer)
        if "layout" in rules:
            assert self.layout is not None
            append_declaration("layout", self.layout.name)

        if "color" in rules:
            append_declaration("color", self.color.hex)
        if "background" in rules:
            append_declaration("background", self.background.hex)
        if "background_tint" in rules:
            append_declaration("background-tint", self.background_tint.hex)
        if "text_style" in rules:
            append_declaration("text-style", str(get_rule("text_style")))
        if "tint" in rules:
            append_declaration("tint", self.tint.css)

        if "overflow_x" in rules:
            append_declaration("overflow-x", self.overflow_x)
        if "overflow_y" in rules:
            append_declaration("overflow-y", self.overflow_y)

        if "scrollbar_color" in rules:
            append_declaration("scrollbar-color", self.scrollbar_color.css)
        if "scrollbar_color_hover" in rules:
            append_declaration("scrollbar-color-hover", self.scrollbar_color_hover.css)
        if "scrollbar_color_active" in rules:
            append_declaration(
                "scrollbar-color-active", self.scrollbar_color_active.css
            )

        if "scrollbar_corner_color" in rules:
            append_declaration(
                "scrollbar-corner-color", self.scrollbar_corner_color.css
            )

        if "scrollbar_background" in rules:
            append_declaration("scrollbar-background", self.scrollbar_background.css)
        if "scrollbar_background_hover" in rules:
            append_declaration(
                "scrollbar-background-hover", self.scrollbar_background_hover.css
            )
        if "scrollbar_background_active" in rules:
            append_declaration(
                "scrollbar-background-active", self.scrollbar_background_active.css
            )

        if "scrollbar_gutter" in rules:
            append_declaration("scrollbar-gutter", self.scrollbar_gutter)
        if "scrollbar_size" in rules:
            append_declaration(
                "scrollbar-size",
                f"{self.scrollbar_size_horizontal} {self.scrollbar_size_vertical}",
            )
        else:
            if "scrollbar_size_horizontal" in rules:
                append_declaration(
                    "scrollbar-size-horizontal", str(self.scrollbar_size_horizontal)
                )
            if "scrollbar_size_vertical" in rules:
                append_declaration(
                    "scrollbar-size-vertical", str(self.scrollbar_size_vertical)
                )

        if "box_sizing" in rules:
            append_declaration("box-sizing", self.box_sizing)
        if "width" in rules:
            append_declaration("width", str(self.width))
        if "height" in rules:
            append_declaration("height", str(self.height))
        if "min_width" in rules:
            append_declaration("min-width", str(self.min_width))
        if "min_height" in rules:
            append_declaration("min-height", str(self.min_height))
        if "max_width" in rules:
            append_declaration("max-width", str(self.min_width))
        if "max_height" in rules:
            append_declaration("max-height", str(self.min_height))
        if "transitions" in rules:
            append_declaration(
                "transition",
                ", ".join(
                    f"{name} {transition}"
                    for name, transition in self.transitions.items()
                ),
            )

        if "align_horizontal" in rules and "align_vertical" in rules:
            append_declaration(
                "align", f"{self.align_horizontal} {self.align_vertical}"
            )
        elif "align_horizontal" in rules:
            append_declaration("align-horizontal", self.align_horizontal)
        elif "align_vertical" in rules:
            append_declaration("align-vertical", self.align_vertical)

        if "content_align_horizontal" in rules and "content_align_vertical" in rules:
            append_declaration(
                "content-align",
                f"{self.content_align_horizontal} {self.content_align_vertical}",
            )
        elif "content_align_horizontal" in rules:
            append_declaration(
                "content-align-horizontal", self.content_align_horizontal
            )
        elif "content_align_vertical" in rules:
            append_declaration("content-align-vertical", self.content_align_vertical)

        if "text_align" in rules:
            append_declaration("text-align", self.text_align)

        if "border_title_align" in rules:
            append_declaration("border-title-align", self.border_title_align)
        if "border_subtitle_align" in rules:
            append_declaration("border-subtitle-align", self.border_subtitle_align)

        if "opacity" in rules:
            append_declaration("opacity", str(self.opacity))
        if "text_opacity" in rules:
            append_declaration("text-opacity", str(self.text_opacity))

        if "grid_columns" in rules:
            append_declaration(
                "grid-columns",
                " ".join(str(scalar) for scalar in self.grid_columns or ()),
            )
        if "grid_rows" in rules:
            append_declaration(
                "grid-rows",
                " ".join(str(scalar) for scalar in self.grid_rows or ()),
            )
        if "grid_size_columns" in rules:
            append_declaration("grid-size-columns", str(self.grid_size_columns))
        if "grid_size_rows" in rules:
            append_declaration("grid-size-rows", str(self.grid_size_rows))

        if "grid_gutter_horizontal" in rules:
            append_declaration(
                "grid-gutter-horizontal", str(self.grid_gutter_horizontal)
            )
        if "grid_gutter_vertical" in rules:
            append_declaration("grid-gutter-vertical", str(self.grid_gutter_vertical))

        if "row_span" in rules:
            append_declaration("row-span", str(self.row_span))
        if "column_span" in rules:
            append_declaration("column-span", str(self.column_span))

        if "link_color" in rules:
            append_declaration("link-color", self.link_color.css)
        if "link_background" in rules:
            append_declaration("link-background", self.link_background.css)
        if "link_style" in rules:
            append_declaration("link-style", str(self.link_style))

        if "link_color_hover" in rules:
            append_declaration("link-color-hover", self.link_color_hover.css)
        if "link_background_hover" in rules:
            append_declaration("link-background-hover", self.link_background_hover.css)
        if "link_style_hover" in rules:
            append_declaration("link-style-hover", str(self.link_style_hover))

        if "border_title_color" in rules:
            append_declaration("title-color", self.border_title_color.css)
        if "border_title_background" in rules:
            append_declaration("title-background", self.border_title_background.css)
        if "border_title_style" in rules:
            append_declaration("title-text-style", str(self.border_title_style))

        if "border_subtitle_color" in rules:
            append_declaration("subtitle-color", self.border_subtitle_color.css)
        if "border_subtitle_background" in rules:
            append_declaration(
                "subtitle-background", self.border_subtitle_background.css
            )
        if "border_subtitle_text_style" in rules:
            append_declaration("subtitle-text-style", str(self.border_subtitle_style))
        if "overlay" in rules:
            append_declaration("overlay", str(self.overlay))
        if "constrain_x" in rules and "constrain_y" in rules:
            if self.constrain_x == self.constrain_y:
                append_declaration("constrain", self.constrain_x)
            else:
                append_declaration(
                    "constrain", f"{self.constrain_x} {self.constrain_y}"
                )
        elif "constrain_x" in rules:
            append_declaration("constrain-x", self.constrain_x)
        elif "constrain_y" in rules:
            append_declaration("constrain-y", self.constrain_y)

        if "keyline" in rules:
            keyline_type, keyline_color = self.keyline
            if keyline_type != "none":
                append_declaration("keyline", f"{keyline_type}, {keyline_color.css}")
        if "hatch" in rules:
            hatch_character, hatch_color = self.hatch
            append_declaration("hatch", f'"{hatch_character}" {hatch_color.css}')
        if "text_wrap" in rules:
            append_declaration("text-wrap", self.text_wrap)
        if "text_overflow" in rules:
            append_declaration("text-overflow", self.text_overflow)
        lines.sort()
        return lines

    @property
    def css(self) -> str:
        return "\n".join(self.css_lines)


@rich.repr.auto
class RenderStyles(StylesBase):
    """Presents a combined view of two Styles object: a base Styles and inline Styles."""

    def __init__(self, node: DOMNode, base: Styles, inline_styles: Styles) -> None:
        self.node = node
        self._base_styles = base
        self._inline_styles = inline_styles
        self._animate: BoundAnimator | None = None
        self._updates: int = 0
        self._rich_style: tuple[int, Style] | None = None
        self._gutter: tuple[int, Spacing] | None = None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RenderStyles):
            return (
                self._base_styles._rules == other._base_styles._rules
                and self._inline_styles._rules == other._inline_styles._rules
            )
        return NotImplemented

    @property
    def _cache_key(self) -> int:
        """A cache key, that changes when any style is changed.

        Returns:
            An opaque integer.
        """
        return self._updates + self._base_styles._updates + self._inline_styles._updates

    @property
    def base(self) -> Styles:
        """Quick access to base (css) style."""
        return self._base_styles

    @property
    def inline(self) -> Styles:
        """Quick access to the inline styles."""
        return self._inline_styles

    @property
    def rich_style(self) -> Style:
        """Get a Rich style for this Styles object."""
        assert self.node is not None
        return self.node.rich_style

    @property
    def gutter(self) -> Spacing:
        """Get space around widget.

        Returns:
            Space around widget content.
        """
        # This is (surprisingly) a bit of a bottleneck
        if self._gutter is not None:
            cache_key, gutter = self._gutter
            if cache_key == self._cache_key:
                return gutter
        gutter = self.padding + self.border.spacing
        self._gutter = (self._cache_key, gutter)
        return gutter

    def animate(
        self,
        attribute: str,
        value: str | float | Animatable,
        *,
        final_value: object = ...,
        duration: float | None = None,
        speed: float | None = None,
        delay: float = 0.0,
        easing: EasingFunction | str = DEFAULT_EASING,
        on_complete: CallbackType | None = None,
        level: AnimationLevel = "full",
    ) -> None:
        """Animate an attribute.

        Args:
            attribute: Name of the attribute to animate.
            value: The value to animate to.
            final_value: The final value of the animation. Defaults to `value` if not set.
            duration: The duration (in seconds) of the animation.
            speed: The speed of the animation.
            delay: A delay (in seconds) before the animation starts.
            easing: An easing method.
            on_complete: A callable to invoke when the animation is finished.
            level: Minimum level required for the animation to take place (inclusive).
        """
        if self._animate is None:
            assert self.node is not None
            self._animate = self.node.app.animator.bind(self)
        assert self._animate is not None
        self._animate(
            attribute,
            value,
            final_value=final_value,
            duration=duration,
            speed=speed,
            delay=delay,
            easing=easing,
            on_complete=on_complete,
            level=level,
        )

    def __rich_repr__(self) -> rich.repr.Result:
        yield self.node
        for rule_name in RULE_NAMES:
            if self.has_rule(rule_name):
                yield rule_name, getattr(self, rule_name)

    def refresh(
        self,
        *,
        layout: bool = False,
        children: bool = False,
        parent: bool = False,
        repaint: bool = True,
    ) -> None:
        self._inline_styles.refresh(
            layout=layout, children=children, parent=parent, repaint=repaint
        )

    def merge(self, other: StylesBase) -> None:
        """Merge values from another Styles.

        Args:
            other: A Styles object.
        """
        self._inline_styles.merge(other)

    def merge_rules(self, rules: RulesMap) -> None:
        self._inline_styles.merge_rules(rules)
        self._updates += 1

    def reset(self) -> None:
        """Reset the rules to initial state."""
        self._inline_styles.reset()
        self._updates += 1

    def has_rule(self, rule_name: str) -> bool:
        """Check if a rule has been set."""
        return self._inline_styles.has_rule(rule_name) or self._base_styles.has_rule(
            rule_name
        )

    def has_any_rules(self, *rule_names: str) -> bool:
        """Check if any of the supplied rules have been set.

        Args:
            rule_names: Number of rules.

        Returns:
            `True` if any of the supplied rules have been set, `False` if none have.
        """
        inline_has_rule = self._inline_styles.has_rule
        base_has_rule = self._base_styles.has_rule
        return any(inline_has_rule(name) or base_has_rule(name) for name in rule_names)

    def set_rule(self, rule_name: str, value: object | None) -> bool:
        self._updates += 1
        return self._inline_styles.set_rule(rule_name, value)

    def get_rule(self, rule_name: str, default: object = None) -> object:
        if self._inline_styles.has_rule(rule_name):
            return self._inline_styles.get_rule(rule_name, default)
        return self._base_styles.get_rule(rule_name, default)

    def clear_rule(self, rule_name: str) -> bool:
        """Clear a rule (from inline)."""
        self._updates += 1
        return self._inline_styles.clear_rule(rule_name)

    def get_rules(self) -> RulesMap:
        """Get rules as a dictionary"""
        rules = {**self._base_styles._rules, **self._inline_styles._rules}
        return cast(RulesMap, rules)

    @property
    def css(self) -> str:
        """Get the CSS for the combined styles."""
        styles = Styles()
        styles.merge(self._base_styles)
        styles.merge(self._inline_styles)
        combined_css = styles.css
        return combined_css
