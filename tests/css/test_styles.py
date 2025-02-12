from decimal import Decimal

import pytest
from rich.style import Style

from textual.color import Color
from textual.css.errors import StyleValueError
from textual.css.scalar import Scalar, Unit
from textual.css.styles import RenderStyles, Styles
from textual.dom import DOMNode
from textual.widget import Widget


def test_styles_reset():
    styles = Styles()
    styles.text_style = "not bold"
    assert styles.text_style == Style(bold=False)
    styles.reset()
    assert styles.text_style is Style.null()


def test_has_rule():
    styles = Styles()
    assert not styles.has_rule("text_style")
    styles.text_style = "bold"
    assert styles.has_rule("text_style")
    styles.text_style = None
    assert not styles.has_rule("text_style")


def test_clear_rule():
    styles = Styles()
    styles.text_style = "bold"
    assert styles.has_rule("text_style")
    styles.clear_rule("text_style")
    assert not styles.has_rule("text_style")


def test_get_rules():
    styles = Styles()
    # Empty rules at start
    assert styles.get_rules() == {}
    styles.text_style = "bold"
    assert styles.get_rules() == {"text_style": Style.parse("bold")}
    styles.display = "none"
    assert styles.get_rules() == {
        "text_style": Style.parse("bold"),
        "display": "none",
    }


def test_set_rule():
    styles = Styles()
    assert styles.get_rules() == {}
    styles.set_rule("text_style", Style.parse("bold"))
    assert styles.get_rules() == {"text_style": Style.parse("bold")}


def test_reset():
    styles = Styles()
    assert styles.get_rules() == {}
    styles.set_rule("text_style", Style.parse("bold"))
    assert styles.get_rules() == {"text_style": Style.parse("bold")}
    styles.reset()
    assert styles.get_rules() == {}


def test_merge():
    styles = Styles()
    styles.set_rule("text_style", Style.parse("bold"))
    styles2 = Styles()
    styles2.set_rule("display", "none")
    styles.merge(styles2)
    assert styles.get_rules() == {
        "text_style": Style.parse("bold"),
        "display": "none",
    }


def test_merge_rules():
    styles = Styles()
    styles.set_rule("text_style", Style.parse("bold"))
    styles.merge_rules({"display": "none"})
    assert styles.get_rules() == {
        "text_style": Style.parse("bold"),
        "display": "none",
    }


def test_render_styles_border():
    base = Styles()
    inline = Styles()
    styles_view = RenderStyles(None, base, inline)

    base.border_top = ("heavy", "red")
    # Base has border-top: heavy red
    assert styles_view.border_top == ("heavy", Color.parse("red"))

    inline.border_left = ("round", "green")
    # Base has border-top heavy red, inline has border-left: round green
    assert styles_view.border_top == ("heavy", Color.parse("red"))
    assert styles_view.border_left == ("round", Color.parse("green"))
    assert styles_view.border == (
        ("heavy", Color.parse("red")),
        ("", Color(0, 255, 0)),
        ("", Color(0, 255, 0)),
        ("round", Color.parse("green")),
    )


def test_get_opacity_default():
    styles = RenderStyles(DOMNode(), Styles(), Styles())
    assert styles.text_opacity == 1.0


def test_styles_css_property():
    css = "opacity: 50%; text-opacity: 20%; background: green; color: red; tint: dodgerblue 20%;"
    styles = Styles().parse(css, read_from=("", ""))
    assert styles.css == (
        "background: #008000;\n"
        "color: #FF0000;\n"
        "opacity: 0.5;\n"
        "text-opacity: 0.2;\n"
        "tint: rgba(30,144,255,0.2);"
    )


@pytest.mark.parametrize(
    "set_value, expected",
    [
        [0.2, 0.2],
        [-0.4, 0.0],
        [5.8, 1.0],
        ["25%", 0.25],
        ["-10%", 0.0],
        ["120%", 1.0],
    ],
)
def test_opacity_set_then_get(set_value, expected):
    styles = RenderStyles(DOMNode(), Styles(), Styles())
    styles.text_opacity = set_value
    assert styles.text_opacity == expected


def test_opacity_set_invalid_type_error():
    styles = RenderStyles(DOMNode(), Styles(), Styles())
    with pytest.raises(StyleValueError):
        styles.text_opacity = "invalid value"


def test_opacity_set_allows_integer_value():
    """Regression test for https://github.com/Textualize/textual/issues/3414"""
    styles = RenderStyles(DOMNode(), Styles(), Styles())
    styles.text_opacity = 0
    assert styles.text_opacity == 0.0


@pytest.mark.parametrize(
    "size_dimension_input,size_dimension_expected_output",
    [
        # fmt: off
        [None, None],
        [1, Scalar(1, Unit.CELLS, Unit.WIDTH)],
        [1.0, Scalar(1.0, Unit.CELLS, Unit.WIDTH)],
        [1.2, Scalar(1.2, Unit.CELLS, Unit.WIDTH)],
        [1.2e3, Scalar(1200.0, Unit.CELLS, Unit.WIDTH)],
        ["20", Scalar(20, Unit.CELLS, Unit.WIDTH)],
        ["1.4", Scalar(1.4, Unit.CELLS, Unit.WIDTH)],
        [Scalar(100, Unit.CELLS, Unit.WIDTH), Scalar(100, Unit.CELLS, Unit.WIDTH)],
        [Scalar(10.3, Unit.CELLS, Unit.WIDTH), Scalar(10.3, Unit.CELLS, Unit.WIDTH)],
        [Scalar(10.4, Unit.CELLS, Unit.HEIGHT), Scalar(10.4, Unit.CELLS, Unit.HEIGHT)],
        [Scalar(10.5, Unit.PERCENT, Unit.WIDTH), Scalar(10.5, Unit.WIDTH, Unit.WIDTH)],
        [Scalar(10.6, Unit.PERCENT, Unit.PERCENT), Scalar(10.6, Unit.WIDTH, Unit.WIDTH)],
        [Scalar(10.7, Unit.HEIGHT, Unit.PERCENT), Scalar(10.7, Unit.HEIGHT, Unit.PERCENT)],
        # percentage values are normalised to floats and get the WIDTH "percent_unit":
        [Scalar(11, Unit.PERCENT, Unit.HEIGHT), Scalar(11.0, Unit.WIDTH, Unit.WIDTH)],
        # fmt: on
    ],
)
def test_widget_style_size_can_accept_various_data_types_and_normalize_them(
    size_dimension_input, size_dimension_expected_output
):
    widget = Widget()

    widget.styles.width = size_dimension_input
    assert widget.styles.width == size_dimension_expected_output


@pytest.mark.parametrize(
    "size_dimension_input",
    [
        "a",
        "1.4e3",
        3.14j,
        Decimal("3.14"),
        list(),
        tuple(),
        dict(),
    ],
)
def test_widget_style_size_fails_if_data_type_is_not_supported(size_dimension_input):
    widget = Widget()

    with pytest.raises(StyleValueError):
        widget.styles.width = size_dimension_input
