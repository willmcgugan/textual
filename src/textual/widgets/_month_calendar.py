from __future__ import annotations

import calendar
import datetime
from typing import Sequence

from rich.text import Text

from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.coordinate import Coordinate
from textual.events import Mount
from textual.message import Message
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import DataTable
from textual.widgets.data_table import CellDoesNotExist


class InvalidWeekdayNumber(Exception):
    """Exception raised if an invalid weekday number is supplied."""


class CalendarGrid(DataTable, inherit_bindings=False):
    """The grid used internally by the `MonthCalendar` widget for displaying
    and navigating dates."""

    # TODO: Ideally we want to hide that there's a DataTable underneath the
    # `MonthCalendar` widget. Is there any mechanism so component classes could be
    # defined in the parent and substitute the component styles in the child?
    # For example, allow styling the header using `.month-calendar--header`
    # rather than `.datatable--header`?
    DEFAULT_CSS = """
    CalendarGrid {
        height: auto;
        width: auto;

        .datatable--header {
            background: $surface;
        }
    }
    """

    async def _on_click(self, event: events.Click) -> None:
        """Prevent selecting an empty cell, in cases where `show_other_months`
        is false in the `MonthCalendar` widget."""
        meta = event.style.meta
        if "row" not in meta or "column" not in meta:
            return
        row_index = meta["row"]
        column_index = meta["column"]
        is_header_click = self.show_header and row_index == -1
        if not is_header_click:
            if self.get_cell_at(Coordinate(row_index, column_index)) is None:
                event.prevent_default()


class MonthCalendar(Widget):
    BINDINGS = [
        Binding("enter", "select_date", "Select date", show=False),
        Binding("up", "previous_week", "Previous week", show=False),
        Binding("down", "next_week", "Next week", show=False),
        Binding("right", "next_day", "Next day", show=False),
        Binding("left", "previous_day", "Previous day", show=False),
        Binding("pageup", "previous_month", "Previous month", show=False),
        Binding("pagedown", "next_month", "Next month", show=False),
        Binding("ctrl+pageup", "previous_year", "Previous year", show=False),
        Binding("ctrl+pagedown", "next_year", "Next year", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | enter | Select the date under the cursor. |
    | up | Move to the previous week. |
    | down | Move to the next week. |
    | right | Move to the next day.|
    | left | Move to the previous day. |
    | pageup | Move to the previous month. |
    | pagedown | Move to the next month. |
    | ctrl+pageup | Move to the previous year. |
    | ctrl+pagedown | Move to the next year. |
    """

    COMPONENT_CLASSES = {
        "month-calendar--outside-month",
    }
    """
    | Class | Description |
    | :- | :- |
    | `month-calendar--outside-month` | Target the dates outside the current calendar month. |
    """

    # TODO: min-width?
    DEFAULT_CSS = """
    MonthCalendar {
        height: auto;
        width: auto;
        min-height: 7;

        .month-calendar--outside-month {
            color: gray;
        }
    }
    """

    date: Reactive[datetime.date] = Reactive(datetime.date.today)
    """The date currently highlighted and sets the displayed month in the
    calendar."""
    first_weekday: Reactive[int] = Reactive(0)
    """The first day of the week in the calendar. Monday is 0 (the default),
    Sunday is 6."""
    show_cursor: Reactive[bool] = Reactive(True)
    """Whether to display a cursor for navigating dates within the calendar."""
    show_other_months: Reactive[bool] = Reactive(True)
    """Whether to display dates from other months for a six-week calendar."""

    class DateHighlighted(Message):
        """Posted by the `MonthCalendar` widget when the cursor moves to
        highlight a new date.

        Can be handled using `on_month_calendar_date_highlighted` in a subclass
        of `MonthCalendar` or in a parent node in the DOM.
        """

        def __init__(
            self,
            month_calendar: MonthCalendar,
            value: datetime.date,
        ) -> None:
            super().__init__()
            self.month_calendar: MonthCalendar = month_calendar
            """The `MonthCalendar` that sent this message."""
            self.value: datetime.date = value
            """The highlighted date."""

        @property
        def control(self) -> MonthCalendar:
            """Alias for the `MonthCalendar` that sent this message."""
            return self.month_calendar

    class DateSelected(Message):
        """Posted by the `MonthCalendar` widget when a date is selected.

        Can be handled using `on_month_calendar_date_selected` in a subclass
        of `MonthCalendar` or in a parent node in the DOM.
        """

        def __init__(
            self,
            month_calendar: MonthCalendar,
            value: datetime.date,
        ) -> None:
            super().__init__()
            self.month_calendar: MonthCalendar = month_calendar
            """The `MonthCalendar` that sent this message."""
            self.value: datetime.date = value
            """The selected date."""

        @property
        def control(self) -> MonthCalendar:
            """Alias for the `MonthCalendar` that sent this message."""
            return self.month_calendar

    def __init__(
        self,
        date: datetime.date = datetime.date.today(),
        *,
        first_weekday: int = 0,
        show_cursor: bool = True,
        show_other_months: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize a MonthCalendar widget.

        Args:
            date: The initial date to be highlighted (if `show_cursor` is True)
                and sets the displayed month in the calendar. Defaults to today
                if not supplied.
            first_weekday: The first day of the week in the calendar.
                Monday is 0 (the default), Sunday is 6.
            show_cursor: Whether to display a cursor for navigating dates within
                the calendar.
            show_other_months: Whether to display dates from other months for
                a six-week calendar.
            name: The name of the widget.
            id: The ID of the widget in the DOM.
            classes: The CSS classes of the widget.
            disabled: Whether the widget is disabled or not.
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.date = date
        self.first_weekday = first_weekday
        self._calendar = calendar.Calendar(first_weekday)
        """A `Calendar` object from Python's `calendar` module used for
        preparing the calendar data for this widget."""
        self.show_cursor = show_cursor
        self.show_other_months = show_other_months
        self._calendar_dates = self._get_calendar_dates()
        """The matrix of `datetime.date` objects for this month calendar, where
        each row represents a week. See the `_get_calendar_dates` method for
        details."""

    def compose(self) -> ComposeResult:
        yield CalendarGrid(show_cursor=self.show_cursor)

    @on(CalendarGrid.CellHighlighted)
    def _on_calendar_grid_cell_highlighted(
        self,
        event: CalendarGrid.CellHighlighted,
    ) -> None:
        """Post a `DateHighlighted` message when a date cell is highlighted in
        the calendar grid."""
        event.stop()
        assert event.value is not None
        cursor_row, cursor_column = event.coordinate
        new_date = self._calendar_dates[cursor_row][cursor_column]
        assert isinstance(new_date, datetime.date)
        # Avoid possible race condition by setting the `date` reactive
        # without invoking the watcher. When mashing the arrow keys, this
        # otherwise would cause the app to lag or freeze entirely.
        old_date = self.date
        self.set_reactive(MonthCalendar.date, new_date)
        if (new_date.month != old_date.month) or (new_date.year != old_date.year):
            self._calendar_dates = self._get_calendar_dates()
            self._update_calendar_grid(update_week_header=False)

        self.post_message(MonthCalendar.DateHighlighted(self, self.date))

    @on(CalendarGrid.CellSelected)
    def _on_calendar_grid_cell_selected(
        self,
        event: CalendarGrid.CellSelected,
    ) -> None:
        """Post a `DateSelected` message when a date cell is selected in
        the calendar grid."""
        event.stop()
        assert event.value is not None
        # We cannot rely on the `event.coordinate` for the selected date,
        # as selecting a date from the previous or next month will update the
        # calendar to bring that entire month into view and the date at this
        # co-ordinate will have changed! Thankfully it is safe to instead
        # simply use the calendar `date`, as clicking a table cell will emit a
        # `CellHighlighted` message *before* the `CellSelected` message.
        self.post_message(MonthCalendar.DateSelected(self, self.date))

    @on(CalendarGrid.HeaderSelected)
    def _on_calendar_grid_header_selected(
        self,
        event: CalendarGrid.HeaderSelected,
    ) -> None:
        """Stop the propagation of the `HeaderSelected` message from the
        underlying `DataTable`. Currently the `MonthCalendar` does not post its
        own message when the header is selected as there doesn't seem any
        practical purpose, but this could be easily added in future if needed."""
        event.stop()
        pass

    def previous_month(self) -> None:
        """Move to the previous month."""
        year = self.date.year
        month = self.date.month - 1
        if month < 1:
            year -= 1
            month += 12
        day = min(self.date.day, calendar.monthrange(year, month)[1])
        self.date = datetime.date(year, month, day)

    def next_month(self) -> None:
        """Move to the next month."""
        year = self.date.year
        month = self.date.month + 1
        if month > 12:
            year += 1
            month -= 12
        day = min(self.date.day, calendar.monthrange(year, month)[1])
        self.date = datetime.date(year, month, day)

    def previous_year(self) -> None:
        """Move to the previous year."""
        year = self.date.year - 1
        month = self.date.month
        day = min(self.date.day, calendar.monthrange(year, month)[1])
        self.date = datetime.date(year, month, day)

    def next_year(self) -> None:
        """Move to the next year."""
        year = self.date.year + 1
        month = self.date.month
        day = min(self.date.day, calendar.monthrange(year, month)[1])
        self.date = datetime.date(year, month, day)

    def _on_mount(self, _: Mount) -> None:
        self._update_calendar_grid(update_week_header=True)

        def hide_hover_cursor_if_blank_cell(hover_coordinate: Coordinate) -> None:
            calendar_grid = self.query_one(CalendarGrid)
            try:
                hover_cell_value = calendar_grid.get_cell_at(hover_coordinate)
            except CellDoesNotExist:
                calendar_grid._set_hover_cursor(False)
                return
            if hover_cell_value is None:
                calendar_grid._set_hover_cursor(False)

        self.watch(
            self.query_one(CalendarGrid),
            "hover_coordinate",
            hide_hover_cursor_if_blank_cell,
        )

    def _update_calendar_grid(self, update_week_header: bool) -> None:
        """Update the grid to display the dates of the current month calendar.
        If specified, this will also update the weekday names in the header.

        Args:
            update_week_header: Whether the weekday names in the header should
                be updated (e.g. following a change to the `first_weekday`).
        """
        calendar_grid = self.query_one(CalendarGrid)
        old_hover_coordinate = calendar_grid.hover_coordinate
        calendar_grid.clear()

        if update_week_header:
            old_columns = calendar_grid.columns.copy()
            for old_column in old_columns:
                calendar_grid.remove_column(old_column)

            day_names = calendar.day_abbr
            for day in self._calendar.iterweekdays():
                calendar_grid.add_column(day_names[day])

        with self.prevent(CalendarGrid.CellHighlighted):
            for week in self._calendar_dates:
                calendar_grid.add_row(
                    *[
                        self._format_day(date) if date is not None else None
                        for date in week
                    ]
                )

        date_coordinate = self._get_date_coordinate(self.date)
        calendar_grid.cursor_coordinate = date_coordinate

        calendar_grid.hover_coordinate = old_hover_coordinate

    def _format_day(self, date: datetime.date) -> Text:
        """Format a date for display in the calendar.

        Args:
            date: The date to format for display in the calendar.

        Returns:
            A Rich Text object containing the day.
        """
        formatted_day = Text(str(date.day), justify="center")
        if date.month != self.date.month:
            outside_month_style = self.get_component_rich_style(
                "month-calendar--outside-month", partial=True
            )
            formatted_day.stylize(outside_month_style)
        return formatted_day

    def _get_calendar_dates(self) -> list[Sequence[datetime.date | None]]:
        """Returns a matrix of `datetime.date` objects for this month calendar,
        where each row represents a week. If `show_other_months` is True, this
        returns a six-week calendar including dates from the previous and next
        month. If `show_other_months` is False, only weeks required for the
        month are included and any dates outside the month are 'None'."""

        month_weeks = self._calendar.monthdatescalendar(self.date.year, self.date.month)
        calendar_dates: list[Sequence[datetime.date | None]]

        if not self.show_other_months:
            calendar_dates = [
                [date if date.month == self.date.month else None for date in week]
                for week in month_weeks
            ]
            return calendar_dates

        calendar_dates = [list(week) for week in month_weeks]

        if len(calendar_dates) < 6:
            previous_month_weeks = self._get_previous_month_weeks()
            next_month_weeks = self._get_next_month_weeks()

            current_first_date = calendar_dates[0][0]
            assert isinstance(current_first_date, datetime.date)
            current_last_date = calendar_dates[-1][6]
            assert isinstance(current_last_date, datetime.date)

            if len(calendar_dates) == 4:
                calendar_dates = (
                    [previous_month_weeks[-1]] + calendar_dates + [next_month_weeks[0]]
                )
            elif current_first_date.day == 1:
                calendar_dates = [previous_month_weeks[-1]] + calendar_dates
            elif current_last_date.month == self.date.month:
                calendar_dates = calendar_dates + [next_month_weeks[0]]
            else:
                calendar_dates = calendar_dates + [next_month_weeks[1]]

        assert len(calendar_dates) == 6

        return calendar_dates

    def _get_previous_month_weeks(self) -> list[list[datetime.date]]:
        """Returns a matrix of `datetime.date` objects for the previous month,
        used by the `_get_calendar_dates` method."""
        previous_month = self.date.month - 1
        previous_month_year = self.date.year
        if previous_month < 1:
            previous_month_year -= 1
            previous_month += 12
        return self._calendar.monthdatescalendar(previous_month_year, previous_month)

    def _get_next_month_weeks(self) -> list[list[datetime.date]]:
        """Returns a matrix of `datetime.date` objects for the next month,
        used by the `_get_calendar_dates` method."""
        next_month = self.date.month + 1
        next_month_year = self.date.year
        if next_month > 12:
            next_month_year += 1
            next_month -= 12
        return self._calendar.monthdatescalendar(next_month_year, next_month)

    def _get_date_coordinate(self, date: datetime.date) -> Coordinate:
        """Get the coordinate in the calendar grid for a specified date.

        Args:
            date: The date for which to find the corresponding coordinate.

        Returns:
            The coordinate in the calendar grid for the specified date.

        Raises:
            ValueError: If the date is out of range for the current month calendar.
        """
        for week_index, week in enumerate(self._calendar_dates):
            if date in week:
                return Coordinate(week_index, week.index(date))

        raise ValueError("Date is out of range for the current month calendar.")

    def validate_first_weekday(self, first_weekday: int) -> int:
        if not 0 <= first_weekday <= 6:
            raise InvalidWeekdayNumber(
                "Weekday number must be between 0 (Monday) and 6 (Sunday)."
            )
        return first_weekday

    def watch_date(self, old_date: datetime.date, new_date: datetime.date) -> None:
        if not self.is_mounted:
            return
        if (new_date.month != old_date.month) or (new_date.year != old_date.year):
            self._calendar_dates = self._get_calendar_dates()
            self._update_calendar_grid(update_week_header=False)
        else:
            calendar_grid = self.query_one(CalendarGrid)
            cursor_row, cursor_column = calendar_grid.cursor_coordinate
            if self._calendar_dates[cursor_row][cursor_column] != new_date:
                date_coordinate = self._get_date_coordinate(self.date)
                calendar_grid.cursor_coordinate = date_coordinate

    def watch_first_weekday(self) -> None:
        self._calendar = calendar.Calendar(self.first_weekday)
        self._calendar_dates = self._get_calendar_dates()
        if not self.is_mounted:
            return
        self._update_calendar_grid(update_week_header=True)

    def watch_show_cursor(self, show_cursor: bool) -> None:
        if not self.is_mounted:
            return
        calendar_grid = self.query_one(CalendarGrid)
        calendar_grid.show_cursor = show_cursor

    def watch_show_other_months(self) -> None:
        self._calendar_dates = self._get_calendar_dates()
        if not self.is_mounted:
            return
        self._update_calendar_grid(update_week_header=False)

    def action_select_date(self) -> None:
        """Select the date under the cursor."""
        calendar_grid = self.query_one(CalendarGrid)
        calendar_grid.action_select_cursor()

    def action_previous_day(self) -> None:
        """Move to the previous day."""
        self.date -= datetime.timedelta(days=1)

    def action_next_day(self) -> None:
        """Move to the next day."""
        self.date += datetime.timedelta(days=1)

    def action_previous_week(self) -> None:
        """Move to the previous week."""
        self.date -= datetime.timedelta(weeks=1)

    def action_next_week(self) -> None:
        """Move to the next week."""
        self.date += datetime.timedelta(weeks=1)

    def action_previous_month(self) -> None:
        """Move to the previous month."""
        self.previous_month()

    def action_next_month(self) -> None:
        """Move to the next month."""
        self.next_month()

    def action_previous_year(self) -> None:
        """Move to the previous year."""
        self.previous_year()

    def action_next_year(self) -> None:
        """Move to the next year."""
        self.next_year()
