from __future__ import annotations

import datetime

import pytest

from textual import on
from textual.app import App, ComposeResult
from textual.coordinate import Coordinate
from textual.widgets import MonthCalendar
from textual.widgets._month_calendar import CalendarGrid
from textual.widgets.month_calendar import InvalidWeekdayNumber


def test_invalid_month_raises_exception():
    with pytest.raises(ValueError):
        _ = MonthCalendar(datetime.date(year=2021, month=13, day=3))


def test_invalid_day_raises_exception():
    with pytest.raises(ValueError):
        _ = MonthCalendar(datetime.date(year=2021, month=6, day=32))


def test_invalid_weekday_number_raises_exception():
    with pytest.raises(InvalidWeekdayNumber):
        _ = MonthCalendar(first_weekday=7)


def test_calendar_dates_property():
    month_calendar = MonthCalendar(datetime.date(year=2021, month=6, day=3))
    first_monday = datetime.date(2021, 5, 31)

    expected_date = first_monday
    for week in range(len(month_calendar._calendar_dates)):
        for day in range(0, 7):
            assert month_calendar._calendar_dates[week][day] == expected_date
            expected_date += datetime.timedelta(days=1)


def test_get_date_coordinate():
    month_calendar = MonthCalendar(datetime.date(year=2021, month=6, day=3))
    target_date = datetime.date(2021, 6, 3)

    actual_coordinate = month_calendar._get_date_coordinate(target_date)

    expected_coordinate = Coordinate(0, 3)
    assert actual_coordinate == expected_coordinate


def test_get_date_coordinate_when_out_of_range_raises_exception():
    month_calendar = MonthCalendar(datetime.date(year=2021, month=6, day=3))

    with pytest.raises(ValueError):
        month_calendar._get_date_coordinate(datetime.date(2021, 1, 1))


async def test_calendar_defaults_to_today_if_no_date_provided():
    class TodayCalendarApp(App):
        def compose(self) -> ComposeResult:
            yield MonthCalendar()

    app = TodayCalendarApp()
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        today = datetime.date.today()
        assert month_calendar.date == today
        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == str(
            today.day
        )


class MonthCalendarApp(App):
    def __init__(
        self,
        date: datetime.date,
        show_other_months: bool = True,
    ) -> None:
        super().__init__()
        self._date = date
        self._show_other_months = show_other_months
        self.messages: list[tuple[str, datetime.date]] = []

    def compose(self) -> ComposeResult:
        yield MonthCalendar(
            date=self._date,
            show_other_months=self._show_other_months,
        )

    @on(MonthCalendar.DateHighlighted)
    @on(MonthCalendar.DateSelected)
    def record(
        self,
        event: MonthCalendar.DateHighlighted | MonthCalendar.DateSelected,
    ) -> None:
        self.messages.append((event.__class__.__name__, event.value))


async def test_calendar_grid_week_header():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        actual_labels = [col.label.plain for col in calendar_grid.columns.values()]
        expected_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        assert actual_labels == expected_labels


async def test_calendar_grid_days():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        for row, week in enumerate(month_calendar._calendar_dates):
            for column, date in enumerate(week):
                actual_day = calendar_grid.get_cell_at(Coordinate(row, column)).plain
                assert isinstance(date, datetime.date)
                expected_day = str(date.day)
                assert actual_day == expected_day


async def test_calendar_grid_after_reactive_date_change_to_different_month():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        month_calendar.date = datetime.date(year=2022, month=10, day=2)

        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == "2"
        expected_first_monday = datetime.date(2022, 9, 26)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "26"


async def test_calendar_grid_after_reactive_date_change_within_same_month():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        month_calendar.date = datetime.date(year=2021, month=6, day=19)

        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == "19"
        expected_first_monday = datetime.date(2021, 5, 31)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "31"


async def test_calendar_grid_after_reactive_first_weekday_change():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        # Change first weekday to Sunday
        month_calendar.first_weekday = 6

        actual_labels = [col.label.plain for col in calendar_grid.columns.values()]
        expected_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        assert actual_labels == expected_labels
        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == "3"
        expected_first_sunday = datetime.date(2021, 5, 30)
        actual_first_sunday = month_calendar._calendar_dates[0][0]
        assert actual_first_sunday == expected_first_sunday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "30"


async def test_show_cursor():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)
        assert calendar_grid.show_cursor is True  # Sanity check

        month_calendar.show_cursor = False

        assert calendar_grid.show_cursor is False


async def test_previous_year():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        month_calendar.previous_year()

        expected_date = datetime.date(2020, 6, 3)
        assert month_calendar.date == expected_date
        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == "3"
        expected_first_monday = datetime.date(2020, 5, 25)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "25"


async def test_next_year():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        month_calendar.next_year()

        expected_date = datetime.date(2022, 6, 3)
        assert month_calendar.date == expected_date
        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == "3"
        expected_first_monday = datetime.date(2022, 5, 30)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "30"


async def test_previous_year_accounts_for_leap_years():
    app = MonthCalendarApp(date=datetime.date(2024, 2, 29))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)

        month_calendar.previous_year()

        expected_date = datetime.date(2023, 2, 28)
        assert month_calendar.date == expected_date


async def test_next_year_accounts_for_leap_years():
    app = MonthCalendarApp(date=datetime.date(2024, 2, 29))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)

        month_calendar.next_year()

        expected_date = datetime.date(2025, 2, 28)
        assert month_calendar.date == expected_date


async def test_previous_month():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        month_calendar.previous_month()

        expected_date = datetime.date(2021, 5, 3)
        assert month_calendar.date == expected_date
        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == "3"
        expected_first_monday = datetime.date(2021, 4, 26)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "26"


async def test_previous_month_when_month_is_january():
    app = MonthCalendarApp(date=datetime.date(2021, 1, 1))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        month_calendar.previous_month()

        expected_date = datetime.date(2020, 12, 1)
        assert month_calendar.date == expected_date
        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == "1"
        expected_first_monday = datetime.date(2020, 11, 30)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "30"


async def test_previous_month_accounts_for_leap_years():
    app = MonthCalendarApp(date=datetime.date(2024, 3, 29))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)

        month_calendar.previous_month()

        expected_date = datetime.date(2024, 2, 29)
        assert month_calendar.date == expected_date


async def test_previous_month_accounts_for_nonleap_years():
    app = MonthCalendarApp(date=datetime.date(2021, 3, 29))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)

        month_calendar.previous_month()

        expected_date = datetime.date(2021, 2, 28)
        assert month_calendar.date == expected_date


async def test_next_month():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        month_calendar.next_month()

        expected_date = datetime.date(2021, 7, 3)
        assert month_calendar.date == expected_date
        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == "3"
        expected_first_monday = datetime.date(2021, 6, 28)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "28"


async def test_next_month_when_month_is_december():
    app = MonthCalendarApp(date=datetime.date(2021, 12, 1))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        month_calendar.next_month()

        expected_date = datetime.date(2022, 1, 1)
        assert month_calendar.date == expected_date
        assert calendar_grid.get_cell_at(calendar_grid.cursor_coordinate).plain == "1"
        expected_first_monday = datetime.date(2021, 12, 27)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "27"


async def test_next_month_accounts_for_leap_years():
    app = MonthCalendarApp(date=datetime.date(2024, 1, 29))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)

        month_calendar.next_month()

        expected_date = datetime.date(2024, 2, 29)
        assert month_calendar.date == expected_date


async def test_next_month_accounts_for_nonleap_years():
    app = MonthCalendarApp(date=datetime.date(2021, 1, 29))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)

        month_calendar.next_month()

        expected_date = datetime.date(2021, 2, 28)
        assert month_calendar.date == expected_date


async def test_cell_highlighted_updates_date():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)

        await pilot.press("right")
        expected_date = datetime.date(2021, 6, 4)
        assert month_calendar.date == expected_date

        await pilot.press("down")
        expected_date = datetime.date(2021, 6, 11)
        assert month_calendar.date == expected_date

        await pilot.press("left")
        expected_date = datetime.date(2021, 6, 10)
        assert month_calendar.date == expected_date


async def test_hover_coordinate_persists_after_month_changes():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)
        await pilot.hover(MonthCalendar, offset=(3, 3))
        expected_coordinate = Coordinate(2, 0)
        assert calendar_grid.hover_coordinate == expected_coordinate  # Sanity check

        month_calendar.date = datetime.date(year=2022, month=10, day=2)

        assert calendar_grid.hover_coordinate == expected_coordinate


async def test_hover_coordinate_persists_after_first_weekday_changes():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)
        await pilot.hover(MonthCalendar, offset=(3, 3))
        expected_coordinate = Coordinate(2, 0)
        assert calendar_grid.hover_coordinate == expected_coordinate  # Sanity check

        month_calendar.first_weekday = 6  # Sunday

        assert calendar_grid.hover_coordinate == expected_coordinate


async def test_calendar_updates_when_up_key_pressed_on_first_row():
    """Pressing the `up` key when the cursor is on the first row should update
    the date to the previous week and bring that month into view"""

    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)
        assert calendar_grid.cursor_coordinate == Coordinate(0, 3)  # Sanity check

        await pilot.press("up")

        expected_date = datetime.date(2021, 5, 27)
        assert month_calendar.date == expected_date
        assert calendar_grid.cursor_coordinate == Coordinate(4, 3)
        expected_first_monday = datetime.date(2021, 4, 26)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "26"


async def test_calendar_updates_when_down_key_pressed_on_last_row():
    """Pressing the `down` key when the cursor is on the last row should update
    the date to the next week and bring that month into view"""

    app = MonthCalendarApp(date=datetime.date(2021, 5, 31))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)
        assert calendar_grid.cursor_coordinate == Coordinate(5, 0)  # Sanity check

        await pilot.press("down")

        expected_date = datetime.date(2021, 6, 7)
        assert month_calendar.date == expected_date
        assert calendar_grid.cursor_coordinate == Coordinate(1, 0)
        expected_first_monday = datetime.date(2021, 5, 31)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "31"


async def test_cursor_wraps_around_to_previous_or_next_date():
    """Pressing the `left`/`right` key when the cursor is on the first/last
    column should wrap around the cursor to the previous/next date"""

    app = MonthCalendarApp(date=datetime.date(2021, 6, 6))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)
        assert calendar_grid.cursor_coordinate == Coordinate(0, 6)  # Sanity check

        await pilot.press("right")
        assert month_calendar.date == datetime.date(2021, 6, 7)
        assert calendar_grid.cursor_coordinate == Coordinate(1, 0)

        await pilot.press("left")
        assert month_calendar.date == datetime.date(2021, 6, 6)
        assert calendar_grid.cursor_coordinate == Coordinate(0, 6)


async def test_calendar_updates_when_date_outside_month_highlighted():
    """Highlighting a date from the previous or next month should update the
    calendar to bring that entire month into view"""

    app = MonthCalendarApp(date=datetime.date(2021, 6, 1))
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)
        # Sanity checks
        assert calendar_grid.cursor_coordinate == Coordinate(0, 1)
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "31"

        await pilot.press("left")

        expected_date = datetime.date(2021, 5, 31)
        assert month_calendar.date == expected_date
        assert calendar_grid.cursor_coordinate == Coordinate(5, 0)
        expected_first_monday = datetime.date(2021, 4, 26)
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)).plain == "26"


async def test_calendar_if_show_other_months_is_false():
    """If `show_other_months` is False, only dates from the current month
    should be displayed and other blank cells should not be selectable"""

    app = MonthCalendarApp(
        date=datetime.date(2021, 6, 1),
        show_other_months=False,
    )
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        expected_messages = [("DateHighlighted", datetime.date(2021, 6, 1))]
        expected_coordinate = Coordinate(0, 1)
        expected_date = datetime.date(2021, 6, 1)
        expected_first_monday = None
        actual_first_monday = month_calendar._calendar_dates[0][0]

        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)) == expected_first_monday
        assert month_calendar.date == expected_date
        assert calendar_grid.cursor_coordinate == expected_coordinate
        assert app.messages == expected_messages

        await pilot.click(MonthCalendar, offset=(3, 1))
        assert calendar_grid.cursor_coordinate == expected_coordinate
        assert app.messages == expected_messages
        assert month_calendar.date == expected_date

        await pilot.hover(MonthCalendar, offset=(3, 1))
        assert calendar_grid._show_hover_cursor is False


async def test_calendar_after_reactive_show_other_months_change():
    app = MonthCalendarApp(
        date=datetime.date(2021, 6, 1),
        show_other_months=True,
    )
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)
        calendar_grid = month_calendar.query_one(CalendarGrid)

        month_calendar.show_other_months = False

        expected_first_monday = None
        actual_first_monday = month_calendar._calendar_dates[0][0]
        assert actual_first_monday == expected_first_monday
        assert calendar_grid.get_cell_at(Coordinate(0, 0)) is None


async def test_month_calendar_message_emission():
    app = MonthCalendarApp(date=datetime.date(2021, 6, 3))
    expected_messages = []
    async with app.run_test() as pilot:
        month_calendar = pilot.app.query_one(MonthCalendar)

        expected_messages.append(("DateHighlighted", datetime.date(2021, 6, 3)))
        assert app.messages == expected_messages

        await pilot.press("enter")
        expected_messages.append(("DateSelected", datetime.date(2021, 6, 3)))
        assert app.messages == expected_messages

        await pilot.press("right")
        expected_messages.append(("DateHighlighted", datetime.date(2021, 6, 4)))
        assert app.messages == expected_messages

        await pilot.click(MonthCalendar, offset=(2, 1))
        expected_messages.append(("DateHighlighted", datetime.date(2021, 5, 31)))
        expected_messages.append(("DateSelected", datetime.date(2021, 5, 31)))
        # TODO: This probably shouldn't emit another DateHighlighted message?
        expected_messages.append(("DateHighlighted", datetime.date(2021, 5, 31)))
        assert app.messages == expected_messages

        month_calendar.previous_month()
        await pilot.pause()
        expected_messages.append(("DateHighlighted", datetime.date(2021, 4, 30)))
        assert app.messages == expected_messages
