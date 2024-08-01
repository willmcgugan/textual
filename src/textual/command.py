"""
This module contains classes for working with Textual's command palette.

See the guide on the [Command Palette](../guide/command_palette.md) for full details.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import (
    CancelledError,
    Queue,
    Task,
    TimeoutError,
    create_task,
    wait,
    wait_for,
)
from dataclasses import dataclass
from functools import total_ordering
from inspect import isclass
from time import monotonic
from typing import TYPE_CHECKING, Any, AsyncGenerator, AsyncIterator, ClassVar, Iterable

import rich.repr
from rich.align import Align
from rich.console import Group, RenderableType
from rich.style import Style
from rich.text import Text
from typing_extensions import Final, TypeAlias

from . import on, work
from .binding import Binding, BindingType
from .containers import Horizontal, Vertical
from .events import Click, Mount
from .fuzzy import Matcher
from .message import Message
from .reactive import var
from .screen import Screen, SystemModalScreen
from .timer import Timer
from .types import IgnoreReturnCallbackType
from .widget import Widget
from .widgets import Button, Input, LoadingIndicator, OptionList, Static
from .widgets.option_list import Option
from .worker import get_current_worker

if TYPE_CHECKING:
    from .app import App, ComposeResult

__all__ = [
    "CommandPalette",
    "DiscoveryHit",
    "Hit",
    "Hits",
    "Matcher",
    "Provider",
]


@dataclass
class Hit:
    """Holds the details of a single command search hit."""

    score: float
    """The score of the command hit.

    The value should be between 0 (no match) and 1 (complete match).
    """

    match_display: RenderableType
    """A string or Rich renderable representation of the hit."""

    command: IgnoreReturnCallbackType
    """The function to call when the command is chosen."""

    text: str | None = None
    """The command text associated with the hit, as plain text.

    If `match_display` is not simple text, this attribute should be provided by the
    [Provider][textual.command.Provider] object.
    """

    help: str | None = None
    """Optional help text for the command."""

    @property
    def prompt(self) -> RenderableType:
        """The prompt to use when displaying the hit in the command palette."""
        return self.match_display

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Hit):
            return self.score < other.score
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Hit):
            return self.score == other.score
        return NotImplemented

    def __post_init__(self) -> None:
        """Ensure 'text' is populated."""
        if self.text is None:
            if isinstance(self.match_display, str):
                self.text = self.match_display
            elif isinstance(self.match_display, Text):
                self.text = self.match_display.plain
            else:
                raise ValueError(
                    "A value for 'text' is required if 'match_display' is not a str or Text"
                )


@dataclass
class DiscoveryHit:
    """Holds the details of a single command search hit."""

    display: RenderableType
    """A string or Rich renderable representation of the hit."""

    command: IgnoreReturnCallbackType
    """The function to call when the command is chosen."""

    text: str | None = None
    """The command text associated with the hit, as plain text.

    If `display` is not simple text, this attribute should be provided by
    the [Provider][textual.command.Provider] object.
    """

    help: str | None = None
    """Optional help text for the command."""

    @property
    def prompt(self) -> RenderableType:
        """The prompt to use when displaying the discovery hit in the command palette."""
        return self.display

    def __lt__(self, other: object) -> bool:
        if isinstance(other, DiscoveryHit):
            assert self.text is not None
            assert other.text is not None
            return other.text < self.text
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Hit):
            return self.text == other.text
        return NotImplemented

    def __post_init__(self) -> None:
        """Ensure 'text' is populated."""
        if self.text is None:
            if isinstance(self.display, str):
                self.text = self.display
            elif isinstance(self.display, Text):
                self.text = self.display.plain
            else:
                raise ValueError(
                    "A value for 'text' is required if 'display' is not a str or Text"
                )


Hits: TypeAlias = AsyncIterator["DiscoveryHit | Hit"]
"""Return type for the command provider's `search` method."""


class Provider(ABC):
    """Base class for command palette command providers.

    To create new command provider, inherit from this class and implement
    [`search`][textual.command.Provider.search].
    """

    def __init__(self, screen: Screen[Any], match_style: Style | None = None) -> None:
        """Initialise the command provider.

        Args:
            screen: A reference to the active screen.
        """
        self.__screen = screen
        self.__match_style = match_style
        self._init_task: Task | None = None
        self._init_success = False

    @property
    def focused(self) -> Widget | None:
        """The currently-focused widget in the currently-active screen in the application.

        If no widget has focus this will be `None`.
        """
        return self.__screen.focused

    @property
    def screen(self) -> Screen[object]:
        """The currently-active screen in the application."""
        return self.__screen

    @property
    def app(self) -> App[object]:
        """A reference to the application."""
        return self.__screen.app

    @property
    def match_style(self) -> Style | None:
        """The preferred style to use when highlighting matching portions of the [`match_display`][textual.command.Hit.match_display]."""
        return self.__match_style

    def matcher(self, user_input: str, case_sensitive: bool = False) -> Matcher:
        """Create a [fuzzy matcher][textual.fuzzy.Matcher] for the given user input.

        Args:
            user_input: The text that the user has input.
            case_sensitive: Should matching be case sensitive?

        Returns:
            A [fuzzy matcher][textual.fuzzy.Matcher] object for matching against candidate hits.
        """
        return Matcher(
            user_input, match_style=self.match_style, case_sensitive=case_sensitive
        )

    def _post_init(self) -> None:
        """Internal method to run post init task."""

        async def post_init_task() -> None:
            """Wrapper to post init that runs in a task."""
            try:
                await self.startup()
            except Exception:
                from rich.traceback import Traceback

                self.app.log.error(Traceback())
            else:
                self._init_success = True

        self._init_task = create_task(post_init_task())

    async def _wait_init(self) -> None:
        """Wait for initialization."""
        if self._init_task is not None:
            await self._init_task

    async def startup(self) -> None:
        """Called after the Provider is initialized, but before any calls to `search`."""

    async def _search(self, query: str) -> Hits:
        """Internal method to perform search.

        Args:
            query: The user input to be matched.

        Yields:
            Instances of [`Hit`][textual.command.Hit].
        """
        await self._wait_init()
        if self._init_success:
            # An empty search string is a discovery search, anything else is
            # a conventional search.
            hits = self.search(query) if query else self.discover()
            async for hit in hits:
                if hit is not NotImplemented:
                    yield hit

    @abstractmethod
    async def search(self, query: str) -> Hits:
        """A request to search for commands relevant to the given query.

        Args:
            query: The user input to be matched.

        Yields:
            Instances of [`Hit`][textual.command.Hit].
        """
        yield NotImplemented

    async def discover(self) -> Hits:
        """A default collection of hits for the provider.

        Yields:
            Instances of [`DiscoveryHit`][textual.command.DiscoveryHit].

        Note:
            This is different from
            [`search`][textual.command.Provider.search] in that it should
            yield [`DiscoveryHit`s][textual.command.DiscoveryHit] that
            should be shown by default (before user input).

            It is permitted to *not* implement this method.
        """
        yield NotImplemented

    async def _shutdown(self) -> None:
        """Internal method to call shutdown and log errors."""
        try:
            await self.shutdown()
        except Exception:
            from rich.traceback import Traceback

            self.app.log.error(Traceback())

    async def shutdown(self) -> None:
        """Called when the Provider is shutdown.

        Use this method to perform an cleanup, if required.

        """


@rich.repr.auto
@total_ordering
class Command(Option):
    """Class that holds a command in the [`CommandList`][textual.command.CommandList]."""

    def __init__(
        self,
        prompt: RenderableType,
        command: DiscoveryHit | Hit,
        id: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialise the option.

        Args:
            prompt: The prompt for the option.
            command: The details of the command associated with the option.
            id: The optional ID for the option.
            disabled: The initial enabled/disabled state. Enabled by default.
        """
        super().__init__(prompt, id, disabled)
        self.command = command
        """The details of the command associated with the option."""

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Command):
            return self.command < other.command
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Command):
            return self.command == other.command
        return NotImplemented


class CommandList(OptionList, can_focus=False):
    """The command palette command list."""

    DEFAULT_CSS = """
    CommandList {
        visibility: hidden;
        border-top: blank;
        border-bottom: hkey $primary;
        border-left: none;
        border-right: none;
        height: auto;
        max-height: 70vh;
        background: transparent;
        padding: 0;
        text-style: bold;
    }

    CommandList:focus {
        border: blank;
    }

    CommandList.--visible {
        visibility: visible;
    }

    CommandList.--populating {
        border-bottom: none;
    }

    CommandList > .option-list--option-highlighted {
        background: $primary;
    }

    CommandList > .option-list--option {
        padding-left: 2;
    }
    """


class SearchIcon(Static, inherit_css=False):
    """Widget for displaying a search icon before the command input."""

    DEFAULT_CSS = """
    SearchIcon {
        color: #000;  /* required for snapshot tests */
        margin-left: 1;
        margin-top: 1;
        width: 2;
    }
    """

    icon: var[str] = var("🔎")
    """The icon to display."""

    def render(self) -> RenderableType:
        """Render the icon.

        Returns:
            The icon renderable.
        """
        return self.icon


class CommandInput(Input):
    """The command palette input control."""

    DEFAULT_CSS = """
    CommandInput, CommandInput:focus {
        border: blank;
        width: 1fr;
        background: transparent;
        padding-left: 0;
    }
    """


class CommandPalette(SystemModalScreen):
    """The Textual command palette."""

    AUTO_FOCUS = "CommandInput"

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "command-palette--help-text",
        "command-palette--highlight",
    }
    """
    | Class | Description |
    | :- | :- |
    | `command-palette--help-text` | Targets the help text of a matched command. |
    | `command-palette--highlight` | Targets the highlights of a matched command. |
    """

    DEFAULT_CSS = """
    
   
    CommandPalette:inline {
        /* If the command palette is invoked in inline mode, we may need additional lines. */
        min-height: 20;
    }
    CommandPalette {
        background: $background 60%;
        align-horizontal: center;      
    }

    CommandPalette > .command-palette--help-text {           
        text-style: dim not bold;       
    }

    CommandPalette:dark > .command-palette--highlight {
        text-style: bold;
        color: $warning;
    }
    CommandPalette > .command-palette--highlight {
        text-style: bold;
        color: $warning-darken-2;
    }

    CommandPalette > Vertical {
        margin-top: 3; 
        height: 100%;
        visibility: hidden;
        background: $primary 20%;      
    }

    CommandPalette #--input {
        height: auto;
        visibility: visible;
        border: hkey $primary;
    }

    CommandPalette #--input.--list-visible {
        border-bottom: none;
    }

    CommandPalette #--input Label {
        margin-top: 1;
        margin-left: 1;
    }

    CommandPalette #--input Button {
        min-width: 7;
        margin-right: 1;
    }

    CommandPalette #--results {
        overlay: screen;
        height: auto;
    }

    CommandPalette LoadingIndicator {
        height: auto;
        visibility: hidden;
        border-bottom: hkey $primary;
    }

    CommandPalette LoadingIndicator.--visible {
        visibility: visible;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+end, shift+end", "command_list('last')", show=False),
        Binding("ctrl+home, shift+home", "command_list('first')", show=False),
        Binding("down", "cursor_down", show=False),
        Binding("escape", "escape", "Exit the command palette"),
        Binding("pagedown", "command_list('page_down')", show=False),
        Binding("pageup", "command_list('page_up')", show=False),
        Binding("up", "command_list('cursor_up')", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | ctrl+end, shift+end | Jump to the last available commands. |
    | ctrl+home, shift+home | Jump to the first available commands. |
    | down | Navigate down through the available commands. |
    | escape | Exit the command palette. |
    | pagedown | Navigate down a page through the available commands. |
    | pageup | Navigate up a page through the available commands. |
    | up | Navigate up through the available commands. |
    """

    run_on_select: ClassVar[bool] = True
    """A flag to say if a command should be run when selected by the user.

    If `True` then when a user hits `Enter` on a command match in the result
    list, or if they click on one with the mouse, the command will be
    selected and run. If set to `False` the input will be filled with the
    command and then `Enter` should be pressed on the keyboard or the 'go'
    button should be pressed.
    """

    _list_visible: var[bool] = var(False, init=False)
    """Internal reactive to toggle the visibility of the command list."""

    _show_busy: var[bool] = var(False, init=False)
    """Internal reactive to toggle the visibility of the busy indicator."""

    _calling_screen: var[Screen[Any] | None] = var(None)
    """A record of the screen that was active when we were called."""

    _PALETTE_ID: Final[str] = "--command-palette"
    """The internal ID for the command palette."""

    @dataclass
    class OptionHighlighted(Message):
        """Posted to App when an option is highlighted in the command palette."""

        highlighted_event: OptionList.OptionHighlighted
        """The option highlighted event from the OptionList within the command palette."""

    @dataclass
    class Opened(Message):
        """Posted to App when the command palette is opened."""

    @dataclass
    class Closed(Message):
        """Posted to App when the command palette is closed."""

        option_selected: bool
        """True if an option was selected, False if the palette was closed without selecting an option."""

    def __init__(self) -> None:
        """Initialise the command palette."""
        super().__init__(id=self._PALETTE_ID)
        self._selected_command: DiscoveryHit | Hit | None = None
        """The command that was selected by the user."""
        self._busy_timer: Timer | None = None
        """Keeps track of if there's a busy indication timer in effect."""
        self._no_matches_timer: Timer | None = None
        """Keeps track of if there are 'No matches found' message waiting to be displayed."""
        self._providers: list[Provider] = []
        """List of Provider instances involved in searches."""

    @staticmethod
    def is_open(app: App) -> bool:
        """Is the command palette current open?

        Args:
            app: The app to test.

        Returns:
            `True` if the command palette is currently open, `False` if not.
        """
        return app.screen.id == CommandPalette._PALETTE_ID

    @property
    def _provider_classes(self) -> set[type[Provider]]:
        """The currently available command providers.

        This is a combination of the command providers defined [in the
        application][textual.app.App.COMMANDS] and those [defined in
        the current screen][textual.screen.Screen.COMMANDS].
        """

        def get_providers(root: App | Screen) -> Iterable[type[Provider]]:
            """Get providers from app or screen.

            Args:
                root: The app or screen.

            Returns:
                An iterable of providers.
            """
            for provider in root.COMMANDS:
                if isclass(provider) and issubclass(provider, Provider):
                    yield provider
                else:
                    # Lazy loaded providers
                    yield provider()  # type: ignore

        return (
            set()
            if self._calling_screen is None
            else {*get_providers(self.app), *get_providers(self._calling_screen)}
        )

    def compose(self) -> ComposeResult:
        """Compose the command palette.

        Returns:
            The content of the screen.
        """
        with Vertical():
            with Horizontal(id="--input"):
                yield SearchIcon()
                yield CommandInput(placeholder="Search for commands…")
                if not self.run_on_select:
                    yield Button("\u25b6")
            with Vertical(id="--results"):
                yield CommandList()
                yield LoadingIndicator()

    def _on_click(self, event: Click) -> None:  # type: ignore[override]
        """Handle the click event.

        Args:
            event: The click event.

        This method is used to allow clicking on the 'background' as a
        method of dismissing the palette.
        """
        if self.get_widget_at(event.screen_x, event.screen_y)[0] is self:
            self._cancel_gather_commands()
            self.app.post_message(CommandPalette.Closed(option_selected=False))
            self.dismiss()

    def _on_mount(self, _: Mount) -> None:
        """Configure the command palette once the DOM is ready."""

        self.app.post_message(CommandPalette.Opened())
        self._calling_screen = self.app.screen_stack[-2]

        match_style = self.get_component_rich_style(
            "command-palette--highlight", partial=True
        )

        assert self._calling_screen is not None
        self._providers = [
            provider_class(self._calling_screen, match_style)
            for provider_class in self._provider_classes
        ]
        for provider in self._providers:
            provider._post_init()
        self._gather_commands("")

    async def _on_unmount(self) -> None:  # type: ignore[override]
        """Shutdown providers when command palette is closed."""
        if self._providers:
            await wait(
                [create_task(provider._shutdown()) for provider in self._providers],
            )
            self._providers.clear()

    def _stop_busy_countdown(self) -> None:
        """Stop any busy countdown that's in effect."""
        if self._busy_timer is not None:
            self._busy_timer.stop()
            self._busy_timer = None

    _BUSY_COUNTDOWN: Final[float] = 0.5
    """How many seconds to wait for commands to come in before showing we're busy."""

    def _start_busy_countdown(self) -> None:
        """Start a countdown to showing that we're busy searching."""
        self._stop_busy_countdown()

        def _become_busy() -> None:
            if self._list_visible:
                self._show_busy = True

        self._busy_timer = self.set_timer(self._BUSY_COUNTDOWN, _become_busy)

    def _stop_no_matches_countdown(self) -> None:
        """Stop any 'No matches' countdown that's in effect."""
        if self._no_matches_timer is not None:
            self._no_matches_timer.stop()
            self._no_matches_timer = None

    _NO_MATCHES_COUNTDOWN: Final[float] = 0.5
    """How many seconds to wait before showing 'No matches found'."""

    def _start_no_matches_countdown(self, search_value: str) -> None:
        """Start a countdown to showing that there are no matches for the query.

        Args:
            search_value: The value being searched for.

        Adds a 'No matches found' option to the command list after
        `_NO_MATCHES_COUNTDOWN` seconds.
        """
        self._stop_no_matches_countdown()

        def _show_no_matches() -> None:
            # If we were actually searching for something, show that we
            # found no matches.
            if search_value:
                command_list = self.query_one(CommandList)
                command_list.add_option(
                    Option(
                        Align.center(Text("No matches found", style="not bold")),
                        disabled=True,
                        id=self._NO_MATCHES,
                    )
                )
                self._list_visible = True
            else:
                # The search value was empty, which means we were in
                # discover mode; in that case it makes no sense to show that
                # no matches were found. Lack of commands that can be
                # discovered is a situation we don't need to highlight.
                self._list_visible = False

        self._no_matches_timer = self.set_timer(
            self._NO_MATCHES_COUNTDOWN,
            _show_no_matches,
        )

    def _watch__list_visible(self) -> None:
        """React to the list visible flag being toggled."""
        self.query_one(CommandList).set_class(self._list_visible, "--visible")
        self.query_one("#--input", Horizontal).set_class(
            self._list_visible, "--list-visible"
        )
        if not self._list_visible:
            self._show_busy = False

    async def _watch__show_busy(self) -> None:
        """React to the show busy flag being toggled.

        This watcher adds or removes a busy indication depending on the
        flag's state.
        """
        self.query_one(LoadingIndicator).set_class(self._show_busy, "--visible")
        self.query_one(CommandList).set_class(self._show_busy, "--populating")

    @staticmethod
    async def _consume(hits: Hits, commands: Queue[DiscoveryHit | Hit]) -> None:
        """Consume a source of matching commands, feeding the given command queue.

        Args:
            hits: The hits to consume.
            commands: The command queue to feed.
        """
        async for hit in hits:
            await commands.put(hit)

    async def _search_for(
        self, search_value: str
    ) -> AsyncGenerator[DiscoveryHit | Hit, bool]:
        """Search for a given search value amongst all of the command providers.

        Args:
            search_value: The value to search for.

        Yields:
            The hits made amongst the registered command providers.
        """

        # Set up a queue to stream in the command hits from all the providers.
        commands: Queue[DiscoveryHit | Hit] = Queue()

        # Fire up an instance of each command provider, inside a task, and
        # have them go start looking for matches.
        searches = [
            create_task(
                self._consume(
                    provider._search(search_value),
                    commands,
                )
            )
            for provider in self._providers
        ]

        # Set up a delay for showing that we're busy.
        self._start_busy_countdown()

        # Assume the search isn't aborted.
        aborted = False

        # Now, while there's some task running...
        while not aborted and any(not search.done() for search in searches):
            try:
                # ...briefly wait for something on the stack. If we get
                # something yield it up to our caller.
                aborted = yield await wait_for(commands.get(), 0.1)
            except TimeoutError:
                # A timeout is fine. We're just going to go back round again
                # and see if anything else has turned up.
                pass
            except CancelledError:
                # A cancelled error means things are being aborted.
                aborted = True
            else:
                # There was no timeout, which means that we managed to yield
                # up that command; we're done with it so let the queue know.
                commands.task_done()

        # Check through all the finished searches, see if any have
        # exceptions, and log them. In most other circumstances we'd
        # re-raise the exception and quit the application, but the decision
        # has been made to find and log exceptions with command providers.
        #
        # https://github.com/Textualize/textual/pull/3058#discussion_r1310051855
        for search in searches:
            if search.done():
                exception = search.exception()
                if exception is not None:
                    from rich.traceback import Traceback

                    self.log.error(
                        Traceback.from_exception(
                            type(exception), exception, exception.__traceback__
                        )
                    )

        # Having finished the main processing loop, we're not busy any more.
        # Anything left in the queue (see next) will fall out more or less
        # instantly. If we're aborted, that means a fresh search is incoming
        # and it'll have cleaned up the countdown anyway, so don't do that
        # here as they'll be a clash.
        if not aborted:
            self._stop_busy_countdown()

        # If all the providers are pretty fast it could be that we've reached
        # this point but the queue isn't empty yet. So here we flush the
        # queue of anything left.
        while not aborted and not commands.empty():
            aborted = yield await commands.get()

        # If we were aborted, ensure that all of the searches are cancelled.
        if aborted:
            for search in searches:
                search.cancel()

    def _refresh_command_list(
        self, command_list: CommandList, commands: list[Command], clear_current: bool
    ) -> None:
        """Refresh the command list.

        Args:
            command_list: The widget that shows the list of commands.
            commands: The commands to show in the widget.
            clear_current: Should the current content of the list be cleared first?
        """
        # For the moment, this is a fairly naive approach to populating the
        # command list with a list of commands. Every time we add a
        # new one we're nuking the list of options and populating them
        # again. If this turns out to not be a great approach, we may try
        # and get a lot smarter with this (ideally OptionList will grow a
        # method to sort its content in an efficient way; but for now we'll
        # go with "worse is better" wisdom).
        highlighted = (
            command_list.get_option_at_index(command_list.highlighted)
            if command_list.highlighted is not None and not clear_current
            else None
        )
        command_list.clear_options().add_options(commands)
        if highlighted is not None and highlighted.id:
            command_list.highlighted = command_list.get_option_index(highlighted.id)
        self._list_visible = bool(command_list.option_count)

    _RESULT_BATCH_TIME: Final[float] = 0.25
    """How long to wait before adding commands to the command list."""

    _NO_MATCHES: Final[str] = "--no-matches"
    """The ID to give the disabled option that shows there were no matches."""

    _GATHER_COMMANDS_GROUP: Final[str] = "--textual-command-palette-gather-commands"
    """The group name of the command gathering worker."""

    @work(exclusive=True, group=_GATHER_COMMANDS_GROUP)
    async def _gather_commands(self, search_value: str) -> None:
        """Gather up all of the commands that match the search value.

        Args:
            search_value: The value to search for.
        """

        # We'll potentially use the help text style a lot so let's grab it
        # the once for use in the loop further down.
        help_style = self.get_component_rich_style(
            "command-palette--help-text", partial=True
        )

        # The list to hold on to the commands we've gathered from the
        # command providers.
        gathered_commands: list[Command] = []

        # Get a reference to the widget that we're going to drop the
        # (display of) commands into.
        command_list = self.query_one(CommandList)

        # If there's just one option in the list, and it's the item that
        # tells the user there were no matches, let's remove that. We're
        # starting a new search so we don't want them thinking there's no
        # matches already.
        if (
            command_list.option_count == 1
            and command_list.get_option_at_index(0).id == self._NO_MATCHES
        ):
            command_list.remove_option(self._NO_MATCHES)

        # Each command will receive a sequential ID. This is going to be
        # used to find commands back again when we update the visible list
        # and want to settle the selection back on the command it was on.
        command_id = 0

        # We're going to be checking in on the worker as we loop around, so
        # grab a reference to that.
        worker = get_current_worker()

        # Reset busy mode.
        self._show_busy = False

        # A flag to keep track of if the current content of the command hit
        # list needs to be cleared. The initial clear *should* be in
        # `_input`, but doing so caused an unsightly "flash" of the list; so
        # here we sacrifice "correct" code for a better-looking UI.
        clear_current = True

        # We're going to batch updates over time, so start off pretending
        # we've just done an update.
        last_update = monotonic()

        # Kick off the search, grabbing the iterator.
        search_routine = self._search_for(search_value)
        search_results = search_routine.__aiter__()

        # We're going to be doing the send/await dance in this code, so we
        # need to grab the first yielded command to start things off.
        try:
            hit = await search_results.__anext__()
        except StopAsyncIteration:
            # We've been stopped before we've even really got going, likely
            # because the user is very quick on the keyboard.
            hit = None

        while hit:
            # Turn the command into something for display, and add it to the
            # list of commands that have been gathered so far.
            prompt = hit.prompt
            if hit.help:
                help_text = Text(hit.help)
                help_text.stylize(help_style)
                prompt = Group(prompt, help_text)
            gathered_commands.append(Command(prompt, hit, id=str(command_id)))

            # Before we go making any changes to the UI, we do a quick
            # double-check that the worker hasn't been cancelled. There's
            # little point in doing UI work on a value that isn't needed any
            # more.
            if worker.is_cancelled:
                break

            # Having made it this far, it's safe to update the list of
            # commands that match the input. Note that we batch up the
            # results and only refresh the list once every so often; this
            # helps reduce how much UI work needs to be done, but at the
            # same time we keep the update frequency often enough so that it
            # looks like things are moving along.
            now = monotonic()
            if (now - last_update) > self._RESULT_BATCH_TIME:
                self._refresh_command_list(
                    command_list, gathered_commands, clear_current
                )
                clear_current = False
                last_update = now

            # Bump the ID.
            command_id += 1

            # Finally, get the available command from the incoming queue;
            # note that we send the worker cancelled status down into the
            # search method.
            try:
                hit = await search_routine.asend(worker.is_cancelled)
            except StopAsyncIteration:
                break

        # On the way out, if we're still in play, ensure everything has been
        # dropped into the command list.
        if not worker.is_cancelled:
            self._refresh_command_list(command_list, gathered_commands, clear_current)

        # One way or another, we're not busy any more.
        self._show_busy = False

        # If we didn't get any hits, and we're not cancelled, that would
        # mean nothing was found. Give the user positive feedback to that
        # effect.
        if command_list.option_count == 0 and not worker.is_cancelled:
            self._start_no_matches_countdown(search_value)

    def _cancel_gather_commands(self) -> None:
        """Cancel any operation that is gather commands."""
        self.app.workers.cancel_group(self, self._GATHER_COMMANDS_GROUP)

    @on(Input.Changed)
    def _input(self, event: Input.Changed) -> None:
        """React to input in the command palette.

        Args:
            event: The input event.
        """
        event.stop()
        self._cancel_gather_commands()
        self._stop_no_matches_countdown()
        self._gather_commands(event.value.strip())

    @on(OptionList.OptionSelected)
    def _select_command(self, event: OptionList.OptionSelected) -> None:
        """React to a command being selected from the dropdown.

        Args:
            event: The option selection event.
        """
        event.stop()
        self._cancel_gather_commands()
        input = self.query_one(CommandInput)
        with self.prevent(Input.Changed):
            assert isinstance(event.option, Command)
            input.value = str(event.option.command.text)
            self._selected_command = event.option.command
        input.action_end()
        self._list_visible = False
        self.query_one(CommandList).clear_options()
        if self.run_on_select:
            self._select_or_command()

    @on(Input.Submitted)
    @on(Button.Pressed)
    def _select_or_command(
        self, event: Input.Submitted | Button.Pressed | None = None
    ) -> None:
        """Depending on context, select or execute a command."""
        # If the list is visible, that means we're in "pick a command"
        # mode...
        if event is not None:
            event.stop()
        if self._list_visible:
            # ...so if nothing in the list is highlighted yet...
            if self.query_one(CommandList).highlighted is None:
                # ...cause the first completion to be highlighted.
                self._action_cursor_down()
            else:
                # The list is visible, something is highlighted, the user
                # made a selection "gesture"; let's go select it!
                self._action_command_list("select")
        else:
            # The list isn't visible, which means that if we have a
            # command...
            if self._selected_command is not None:
                # ...we should return it to the parent screen and let it
                # decide what to do with it (hopefully it'll run it).
                self._cancel_gather_commands()
                self.app.post_message(CommandPalette.Closed(option_selected=True))
                self.dismiss()
                self.call_later(self._selected_command.command)

    @on(OptionList.OptionHighlighted)
    def _stop_event_leak(self, event: OptionList.OptionHighlighted) -> None:
        """Stop any unused events so they don't leak to the application."""
        event.stop()
        self.app.post_message(CommandPalette.OptionHighlighted(highlighted_event=event))

    def _action_escape(self) -> None:
        """Handle a request to escape out of the command palette."""
        if self._list_visible:
            self._list_visible = False
        else:
            self._cancel_gather_commands()
            self.app.post_message(CommandPalette.Closed(option_selected=False))
            self.dismiss()

    def _action_command_list(self, action: str) -> None:
        """Pass an action on to the [`CommandList`][textual.command.CommandList].

        Args:
            action: The action to pass on to the [`CommandList`][textual.command.CommandList].
        """
        try:
            command_action = getattr(self.query_one(CommandList), f"action_{action}")
        except AttributeError:
            return
        command_action()

    def _action_cursor_down(self) -> None:
        """Handle the cursor down action.

        This allows the cursor down key to either open the command list, if
        it's closed but has options, or if it's open with options just
        cursor through them.
        """
        commands = self.query_one(CommandList)
        if commands.option_count and not self._list_visible:
            self._list_visible = True
            commands.highlighted = 0
        elif (
            commands.option_count
            and not commands.get_option_at_index(0).id == self._NO_MATCHES
        ):
            self._action_command_list("cursor_down")
