from __future__ import annotations

import asyncio
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, Iterator, Literal, TextIO

from textual import events, log, messages
from textual.events import MouseUp

if TYPE_CHECKING:
    from textual.app import App


class Driver(ABC):
    """A base class for drivers."""

    def __init__(
        self,
        app: App[Any],
        *,
        debug: bool = False,
        mouse: bool = True,
        size: tuple[int, int] | None = None,
    ) -> None:
        """Initialize a driver.

        Args:
            app: The App instance.
            debug: Enable debug mode.
            mouse: Enable mouse support,
            size: Initial size of the terminal or `None` to detect.
        """
        self._app = app
        self._debug = debug
        self._mouse = mouse
        self._size = size
        self._loop = asyncio.get_running_loop()
        self._down_buttons: list[int] = []
        self._last_move_event: events.MouseMove | None = None
        self._auto_restart = True
        """Should the application auto-restart (where appropriate)?"""
        self.cursor_origin: tuple[int, int] | None = None

    @property
    def is_headless(self) -> bool:
        """Is the driver 'headless' (no output)?"""
        return False

    @property
    def is_inline(self) -> bool:
        """Is the driver 'inline' (not full-screen)?"""
        return False

    @property
    def is_web(self) -> bool:
        """Is the driver 'web' (running via a browser)?"""
        return False

    @property
    def can_suspend(self) -> bool:
        """Can this driver be suspended?"""
        return False

    def send_message(self, message: messages.Message) -> None:
        """Send a message to the target app.

        Args:
            message: A message.
        """
        asyncio.run_coroutine_threadsafe(
            self._app._post_message(message), loop=self._loop
        )

    def process_message(self, message: messages.Message) -> None:
        """Perform additional processing on a message, prior to sending.

        Args:
            event: A message to process.
        """
        # NOTE: This runs in a thread.
        # Avoid calling methods on the app.
        message.set_sender(self._app)
        if self.cursor_origin is None:
            offset_x = 0
            offset_y = 0
        else:
            offset_x, offset_y = self.cursor_origin
        if isinstance(message, events.MouseEvent):
            message._x -= offset_x
            message._y -= offset_y
            message._screen_x -= offset_x
            message._screen_y -= offset_y

        if isinstance(message, events.MouseDown):
            if message.button:
                self._down_buttons.append(message.button)
        elif isinstance(message, events.MouseUp):
            if message.button and message.button in self._down_buttons:
                self._down_buttons.remove(message.button)
        elif isinstance(message, events.MouseMove):
            if (
                self._down_buttons
                and not message.button
                and self._last_move_event is not None
            ):
                # Deduplicate self._down_buttons while preserving order.
                buttons = list(dict.fromkeys(self._down_buttons).keys())
                self._down_buttons.clear()
                move_event = self._last_move_event
                for button in buttons:
                    self.send_message(
                        MouseUp(
                            message.widget,
                            x=move_event.x,
                            y=move_event.y,
                            delta_x=0,
                            delta_y=0,
                            button=button,
                            shift=message.shift,
                            meta=message.meta,
                            ctrl=message.ctrl,
                            screen_x=move_event.screen_x,
                            screen_y=move_event.screen_y,
                            style=message.style,
                        )
                    )
            self._last_move_event = message

        self.send_message(message)

    @abstractmethod
    def write(self, data: str) -> None:
        """Write data to the output device.

        Args:
            data: Raw data.
        """

    def flush(self) -> None:
        """Flush any buffered data."""

    @abstractmethod
    def start_application_mode(self) -> None:
        """Start application mode."""

    @abstractmethod
    def disable_input(self) -> None:
        """Disable further input."""

    @abstractmethod
    def stop_application_mode(self) -> None:
        """Stop application mode, restore state."""

    def suspend_application_mode(self) -> None:
        """Suspend application mode.

        Used to suspend application mode and allow uninhibited access to the
        terminal.
        """
        self.stop_application_mode()
        self.close()

    def resume_application_mode(self) -> None:
        """Resume application mode.

        Used to resume application mode after it has been previously
        suspended.
        """
        self.start_application_mode()

    class SignalResume(events.Event):
        """Event sent to the app when a resume signal should be published."""

    @contextmanager
    def no_automatic_restart(self) -> Iterator[None]:
        """A context manager used to tell the driver to not auto-restart.

        For drivers that support the application being suspended by the
        operating system, this context manager is used to mark a body of
        code as one that will manage its own stop and start.
        """
        auto_restart = self._auto_restart
        self._auto_restart = False
        try:
            yield
        finally:
            self._auto_restart = auto_restart

    def close(self) -> None:
        """Perform any final cleanup."""

    def open_url(self, url: str, new_tab: bool = True) -> None:
        """Open a URL in the default web browser.

        Args:
            url: The URL to open.
            new_tab: Whether to open the URL in a new tab.
                This is only relevant when running via the WebDriver,
                and is ignored when called while running through the terminal.
        """
        import webbrowser

        webbrowser.open(url)

    def deliver_binary(
        self,
        binary: BinaryIO | TextIO,
        *,
        delivery_key: str,
        save_path: Path,
        open_method: Literal["browser", "download"] = "download",
        encoding: str | None = None,
        mime_type: str | None = None,
        name: str | None = None,
    ) -> None:
        """Save the file `path_or_file` to `save_path`.

        If running via web through Textual Web or Textual Serve,
        this will initiate a download in the web browser.

        Args:
            binary: The binary file to save.
            delivery_key: The unique key that was used to deliver the file.
            save_path: The location to save the file to.
            open_method: *web only* Whether to open the file in the browser or
                to prompt the user to download it. When running via a standard
                (non-web) terminal, this is ignored.
            encoding: *web only* The text encoding to use when saving the file.
                This will be passed to Python's `open()` built-in function.
                When running via web, this will be used to set the charset
                in the `Content-Type` header.
            mime_type: *web only* The MIME type of the file. This will be used to
                set the `Content-Type` header in the HTTP response.
            name: A user-defined named which will be returned in [`DeliveryComplete`][textual.events.DeliveryComplete]
                and [`DeliveryComplete`][textual.events.DeliveryComplete].

        """

        def save_file_thread(binary: BinaryIO | TextIO, mode: str) -> None:
            try:
                with open(
                    save_path, mode, encoding=encoding or "utf-8"
                ) as destination_file:
                    read = binary.read
                    write = destination_file.write
                    chunk_size = 1024 * 64
                    while True:
                        data = read(chunk_size)
                        if not data:
                            # No data left to read - delivery is complete.
                            self._delivery_complete(
                                delivery_key, save_path=save_path, name=name
                            )
                            break
                        write(data)
            except Exception as error:
                # If any exception occurs during the delivery, pass
                # it on to the app via a DeliveryFailed event.
                log.error(f"Failed to deliver file: {error}")
                import traceback

                log.error(str(traceback.format_exc()))
                self._delivery_failed(delivery_key, exception=error, name=name)
            finally:
                if not binary.closed:
                    binary.close()

        if isinstance(binary, BinaryIO):
            mode = "wb"
        else:
            mode = "w"

        thread = threading.Thread(target=save_file_thread, args=(binary, mode))
        thread.start()

    def _delivery_complete(
        self, delivery_key: str, save_path: Path | None, name: str | None
    ) -> None:
        """Called when a file has been delivered successfully.

        Delivers a DeliveryComplete event to the app.
        """
        self._app.call_from_thread(
            self._app.post_message,
            events.DeliveryComplete(key=delivery_key, path=save_path, name=name),
        )

    def _delivery_failed(
        self, delivery_key: str, exception: BaseException, name: str | None
    ) -> None:
        """Called when a file delivery fails.

        Delivers a DeliveryFailed event to the app.
        """
        self._app.call_from_thread(
            self._app.post_message,
            events.DeliveryFailed(key=delivery_key, exception=exception, name=name),
        )
