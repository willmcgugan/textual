from __future__ import annotations

import asyncio
import os
import selectors
import signal
import sys
import termios
import tty
from codecs import getincrementaldecoder
from threading import Event, Thread
from typing import TYPE_CHECKING, Any

import rich.repr

from textual import events
from textual._loop import loop_last
from textual._parser import ParseError
from textual._xterm_parser import XTermParser
from textual.driver import Driver
from textual.drivers._writer_thread import WriterThread
from textual.geometry import Size
from textual.message import Message
from textual.messages import TerminalSupportInBandWindowResize

if TYPE_CHECKING:
    from textual.app import App


@rich.repr.auto(angular=True)
class LinuxDriver(Driver):
    """Powers display and input for Linux / MacOS"""

    def __init__(
        self,
        app: App,
        *,
        debug: bool = False,
        mouse: bool = True,
        size: tuple[int, int] | None = None,
    ) -> None:
        """Initialize Linux driver.

        Args:
            app: The App instance.
            debug: Enable debug mode.
            mouse: Enable mouse support.
            size: Initial size of the terminal or `None` to detect.
        """
        super().__init__(app, debug=debug, mouse=mouse, size=size)
        self._file = sys.__stderr__
        self.fileno = sys.__stdin__.fileno()
        self.input_tty = sys.__stdin__.isatty()
        self.attrs_before: list[Any] | None = None
        self.exit_event = Event()
        self._key_thread: Thread | None = None
        self._writer_thread: WriterThread | None = None

        # If we've finally and properly come back from a SIGSTOP we want to
        # be able to ask the app to publish its resume signal; to do that we
        # need to know that we came in here via a SIGTSTP; this flag helps
        # keep track of this.
        self._must_signal_resume = False
        self._in_band_window_resize = False
        self._mouse_pixels = False

        # Put handlers for SIGTSTP and SIGCONT in place. These are necessary
        # to support the user pressing Ctrl+Z (or whatever the dev might
        # have bound to call the relevant action on App) to suspend the
        # application.
        signal.signal(signal.SIGTSTP, self._sigtstp_application)
        signal.signal(signal.SIGCONT, self._sigcont_application)

    def _sigtstp_application(self, *_) -> None:
        """Handle a SIGTSTP signal."""
        # If we're supposed to auto-restart, that means we need to shut down
        # first.
        if self._auto_restart:
            self.suspend_application_mode()
            # Flag that we'll need to signal a resume on successful startup
            # again.
            self._must_signal_resume = True
        # Now send a SIGSTOP to our process to *actually* suspend the
        # process.
        os.kill(os.getpid(), signal.SIGSTOP)

    def _sigcont_application(self, *_) -> None:
        """Handle a SICONT application."""
        if self._auto_restart:
            self.resume_application_mode()

    @property
    def can_suspend(self) -> bool:
        """Can this driver be suspended?"""
        return True

    def __rich_repr__(self) -> rich.repr.Result:
        yield self._app

    def _get_terminal_size(self) -> tuple[int, int]:
        """Detect the terminal size.

        Returns:
            The size of the terminal as a tuple of (WIDTH, HEIGHT).
        """
        width: int | None = 80
        height: int | None = 25
        import shutil

        try:
            width, height = shutil.get_terminal_size()
        except (AttributeError, ValueError, OSError):
            try:
                width, height = shutil.get_terminal_size()
            except (AttributeError, ValueError, OSError):
                pass
        width = width or 80
        height = height or 25
        return width, height

    def _enable_mouse_support(self) -> None:
        """Enable reporting of mouse events."""
        if not self._mouse:
            return

        write = self.write
        write("\x1b[?1000h")  # SET_VT200_MOUSE
        write("\x1b[?1003h")  # SET_ANY_EVENT_MOUSE
        write("\x1b[?1015h")  # SET_VT200_HIGHLIGHT_MOUSE
        write("\x1b[?1006h")  # SET_SGR_EXT_MODE_MOUSE

        # write("\x1b[?1007h")
        self.flush()

        # Note: E.g. lxterminal understands 1000h, but not the urxvt or sgr
        #       extensions.

    def _enable_mouse_pixels(self) -> None:
        if not self._mouse:
            return
        self.write("\x1b[?1016h")
        self._mouse_pixels = True

    def _enable_bracketed_paste(self) -> None:
        """Enable bracketed paste mode."""
        self.write("\x1b[?2004h")

    def _query_in_band_window_resize(self) -> None:
        self.write("\x1b[?2048$p")

    def _enable_in_band_window_resize(self) -> None:
        self.write("\x1b[?2048h")

    def _enable_line_wrap(self) -> None:
        self.write("\x1b[?7h")

    def _disable_line_wrap(self) -> None:
        self.write("\x1b[?7l")

    def _disable_in_band_window_resize(self) -> None:
        if self._in_band_window_resize:
            self.write("\x1b[?2048l")

    def _disable_bracketed_paste(self) -> None:
        """Disable bracketed paste mode."""
        self.write("\x1b[?2004l")

    def _disable_mouse_support(self) -> None:
        """Disable reporting of mouse events."""
        if not self._mouse:
            return
        write = self.write
        write("\x1b[?1000l")  #
        write("\x1b[?1003l")  #
        write("\x1b[?1015l")
        write("\x1b[?1006l")
        self.flush()

    def write(self, data: str) -> None:
        """Write data to the output device.

        Args:
            data: Raw data.
        """
        assert self._writer_thread is not None, "Driver must be in application mode"
        self._writer_thread.write(data)

    def start_application_mode(self):
        """Start application mode."""

        def _stop_again(*_) -> None:
            """Signal handler that will put the application back to sleep."""
            os.kill(os.getpid(), signal.SIGSTOP)

        # If we're working with an actual tty...
        # https://github.com/Textualize/textual/issues/4104
        if os.isatty(self.fileno):
            # Set up handlers to ensure that, if there's a SIGTTOU or a SIGTTIN,
            # we go back to sleep.
            signal.signal(signal.SIGTTOU, _stop_again)
            signal.signal(signal.SIGTTIN, _stop_again)
            try:
                # Here we perform a NOP tcsetattr. The reason for this is
                # that, if we're suspended and the user has performed a `bg`
                # in the shell, we'll SIGCONT *but* we won't be allowed to
                # do terminal output; so rather than get into the business
                # of spinning up application mode again and then finding
                # out, we perform a no-consequence change and detect the
                # problem right away.
                termios.tcsetattr(
                    self.fileno, termios.TCSANOW, termios.tcgetattr(self.fileno)
                )
            except termios.error:
                # There was an error doing the tcsetattr; there is no sense
                # in carrying on because we'll be doing a SIGSTOP (see
                # above).
                return
            finally:
                # We don't need to be hooking SIGTTOU or SIGTTIN any more.
                signal.signal(signal.SIGTTOU, signal.SIG_DFL)
                signal.signal(signal.SIGTTIN, signal.SIG_DFL)

        loop = asyncio.get_running_loop()

        def send_size_event() -> None:
            terminal_size = self._get_terminal_size()
            width, height = terminal_size
            textual_size = Size(width, height)
            event = events.Resize(textual_size, textual_size)
            asyncio.run_coroutine_threadsafe(
                self._app._post_message(event),
                loop=loop,
            )

        self._writer_thread = WriterThread(self._file)
        self._writer_thread.start()

        def on_terminal_resize(signum, stack) -> None:
            if not self._in_band_window_resize:
                send_size_event()

        signal.signal(signal.SIGWINCH, on_terminal_resize)

        self.write("\x1b[?1049h")  # Alt screen

        self._enable_mouse_support()
        try:
            self.attrs_before = termios.tcgetattr(self.fileno)
        except termios.error:
            # Ignore attribute errors.
            self.attrs_before = None

        try:
            newattr = termios.tcgetattr(self.fileno)
        except termios.error:
            pass
        else:
            newattr[tty.LFLAG] = self._patch_lflag(newattr[tty.LFLAG])
            newattr[tty.IFLAG] = self._patch_iflag(newattr[tty.IFLAG])

            # VMIN defines the number of characters read at a time in
            # non-canonical mode. It seems to default to 1 on Linux, but on
            # Solaris and derived operating systems it defaults to 4. (This is
            # because the VMIN slot is the same as the VEOF slot, which
            # defaults to ASCII EOT = Ctrl-D = 4.)
            newattr[tty.CC][termios.VMIN] = 1

            try:
                termios.tcsetattr(self.fileno, termios.TCSANOW, newattr)
            except termios.error:
                pass

        self.write("\x1b[?25l")  # Hide cursor
        self.write("\x1b[?1004h")  # Enable FocusIn/FocusOut.
        self.write("\x1b[>1u")  # https://sw.kovidgoyal.net/kitty/keyboard-protocol/

        self.flush()
        self._key_thread = Thread(target=self._run_input_thread)
        send_size_event()
        self._key_thread.start()
        self._request_terminal_sync_mode_support()
        self._query_in_band_window_resize()
        self._enable_bracketed_paste()
        self._disable_line_wrap()

        # Appears to fix an issue enabling mouse support in iTerm 3.5.0
        self._enable_mouse_support()

        # If we need to ask the app to signal that we've come back from a
        # SIGTSTP...
        if self._must_signal_resume:
            self._must_signal_resume = False
            asyncio.run_coroutine_threadsafe(
                self._app._post_message(self.SignalResume()),
                loop=loop,
            )

    def _request_terminal_sync_mode_support(self) -> None:
        """Writes an escape sequence to query the terminal support for the sync protocol."""
        # Terminals should ignore this sequence if not supported.
        # Apple terminal doesn't, and writes a single 'p' in to the terminal,
        # so we will make a special case for Apple terminal (which doesn't support sync anyway).
        if not self.input_tty:
            return
        if os.environ.get("TERM_PROGRAM", "") != "Apple_Terminal":
            self.write("\033[?2026$p")
            self.flush()

    @classmethod
    def _patch_lflag(cls, attrs: int) -> int:
        """Patch termios lflag.

        Args:
            attributes: New set attributes.

        Returns:
            New lflag.

        """
        # if TEXTUAL_ALLOW_SIGNALS env var is set, then allow Ctrl+C to send signals
        ISIG = 0 if os.environ.get("TEXTUAL_ALLOW_SIGNALS") else termios.ISIG

        return attrs & ~(termios.ECHO | termios.ICANON | termios.IEXTEN | ISIG)

    @classmethod
    def _patch_iflag(cls, attrs: int) -> int:
        return attrs & ~(
            # Disable XON/XOFF flow control on output and input.
            # (Don't capture Ctrl-S and Ctrl-Q.)
            # Like executing: "stty -ixon."
            termios.IXON
            | termios.IXOFF
            |
            # Don't translate carriage return into newline on input.
            termios.ICRNL
            | termios.INLCR
            | termios.IGNCR
        )

    def disable_input(self) -> None:
        """Disable further input."""
        try:
            if not self.exit_event.is_set():
                signal.signal(signal.SIGWINCH, signal.SIG_DFL)
                self._disable_mouse_support()
                self.exit_event.set()
                if self._key_thread is not None:
                    self._key_thread.join()
                self.exit_event.clear()
                try:
                    termios.tcflush(self.fileno, termios.TCIFLUSH)
                except termios.error:
                    pass
        except Exception:
            # TODO: log this
            pass

    def stop_application_mode(self) -> None:
        """Stop application mode, restore state."""
        self._disable_bracketed_paste()
        self._enable_line_wrap()
        self._disable_in_band_window_resize()
        self.disable_input()

        if self.attrs_before is not None:
            try:
                termios.tcsetattr(self.fileno, termios.TCSANOW, self.attrs_before)
            except termios.error:
                pass

        # Disable the Kitty keyboard protocol. This must be done before leaving
        # the alt screen. https://sw.kovidgoyal.net/kitty/keyboard-protocol/
        self.write("\x1b[<u")

        # Alt screen false, show cursor
        self.write("\x1b[?1049l")
        self.write("\x1b[?25h")
        self.write("\x1b[?1004l")  # Disable FocusIn/FocusOut.
        self.flush()

    def close(self) -> None:
        """Perform cleanup."""
        if self._writer_thread is not None:
            self._writer_thread.stop()

    def _run_input_thread(self) -> None:
        """
        Key thread target that wraps run_input_thread() to die gracefully if it raises
        an exception
        """
        try:
            self.run_input_thread()
        except BaseException:
            import rich.traceback

            self._app.call_later(
                self._app.panic,
                rich.traceback.Traceback(),
            )

    def run_input_thread(self) -> None:
        """Wait for input and dispatch events."""
        selector = selectors.SelectSelector()
        selector.register(self.fileno, selectors.EVENT_READ)

        fileno = self.fileno
        EVENT_READ = selectors.EVENT_READ

        parser = XTermParser(self._debug)
        feed = parser.feed
        tick = parser.tick

        utf8_decoder = getincrementaldecoder("utf-8")().decode
        decode = utf8_decoder
        read = os.read

        def process_selector_events(
            selector_events: list[tuple[selectors.SelectorKey, int]],
            final: bool = False,
        ) -> None:
            """Process events from selector.

            Args:
                selector_events: List of selector events.
                final: True if this is the last call.

            """
            for last, (_selector_key, mask) in loop_last(selector_events):
                if mask & EVENT_READ:
                    unicode_data = decode(read(fileno, 1024 * 4), final=final and last)
                    if not unicode_data:
                        # This can occur if the stdin is piped
                        break
                    for event in feed(unicode_data):
                        self.process_message(event)
            for event in tick():
                self.process_message(event)

        try:
            while not self.exit_event.is_set():
                process_selector_events(selector.select(0.1))
            selector.unregister(self.fileno)
            process_selector_events(selector.select(0.1), final=True)

        finally:
            selector.close()
            try:
                for event in feed(""):
                    pass
            except (EOFError, ParseError):
                pass

    def process_message(self, message: Message) -> None:
        # intercept in-band window resize
        if isinstance(message, TerminalSupportInBandWindowResize):
            # If it is supported, enabled it
            if message.supported and not message.enabled:
                self._enable_in_band_window_resize()
                self._in_band_window_resize = message.supported
            elif message.enabled:
                self._in_band_window_resize = message.supported
            self._enable_mouse_pixels()
            # Send up-to-date message
            super().process_message(
                TerminalSupportInBandWindowResize(
                    message.supported, self._in_band_window_resize
                )
            )
            return

        super().process_message(message)
