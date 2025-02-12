import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import MonthCalendar


class MonthCalendarApp(App):
    CSS = """
    Screen {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "toggle_show_other_months"),
    ]

    def compose(self) -> ComposeResult:
        yield MonthCalendar(datetime.date(year=2021, month=6, day=3))

    def action_toggle_show_other_months(self) -> None:
        calendar = self.query_one(MonthCalendar)
        calendar.show_other_months = not calendar.show_other_months


if __name__ == "__main__":
    app = MonthCalendarApp()
    app.run()
