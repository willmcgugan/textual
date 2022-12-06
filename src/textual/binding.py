from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, MutableMapping

import rich.repr

from textual._typing import TypeAlias
from textual.keys import _get_suggested_binding_key

BindingType: TypeAlias = "Binding | tuple[str, str, str]"


class BindingError(Exception):
    """A binding related error."""


class NoBinding(Exception):
    """A binding was not found."""


@dataclass(frozen=True)
class Binding:
    key: str
    """str: Key to bind. This can also be a comma-separated list of keys to map multiple keys to a single action."""
    action: str
    """str: Action to bind to."""
    description: str
    """str: Description of action."""
    show: bool = True
    """bool: Show the action in Footer, or False to hide."""
    key_display: str | None = None
    """str | None: How the key should be shown in footer."""
    universal: bool = False
    """bool: Allow forwarding from app to focused widget."""


@rich.repr.auto
class Bindings:
    """Manage a set of bindings."""

    def __init__(self, bindings: Iterable[BindingType] | None = None) -> None:
        def make_bindings(bindings: Iterable[BindingType]) -> Iterable[Binding]:
            for binding in bindings:
                # If it's a tuple of length 3, convert into a Binding first
                if isinstance(binding, tuple):
                    if len(binding) != 3:
                        raise BindingError(
                            f"BINDINGS must contain a tuple of three strings, not {binding!r}"
                        )
                    binding = Binding(*binding)

                binding_keys = binding.key.split(",")
                for key in binding_keys:
                    if not key.isalnum():
                        msg = "BINDINGS require alphanumeric keys"
                        suggested_key = _get_suggested_binding_key(key)
                        if suggested_key:
                            msg += f"; try replacing '{key}' with '{suggested_key}'"
                        raise BindingError(msg)

                if len(binding_keys) > 1:
                    for key in binding_keys:
                        new_binding = Binding(
                            key=key,
                            action=binding.action,
                            description=binding.description,
                            show=binding.show,
                            key_display=binding.key_display,
                            universal=binding.universal,
                        )
                        yield new_binding
                else:
                    yield binding

        self.keys: MutableMapping[str, Binding] = (
            {binding.key: binding for binding in make_bindings(bindings)}
            if bindings
            else {}
        )

    def __rich_repr__(self) -> rich.repr.Result:
        yield self.keys

    @classmethod
    def merge(cls, bindings: Iterable[Bindings]) -> Bindings:
        """Merge a bindings. Subsequence bound keys override initial keys.

        Args:
            bindings (Iterable[Bindings]): A number of bindings.

        Returns:
            Bindings: New bindings.
        """
        keys: dict[str, Binding] = {}
        for _bindings in bindings:
            keys.update(_bindings.keys)
        return Bindings(keys.values())

    @property
    def shown_keys(self) -> list[Binding]:
        """A list of bindings for shown keys.

        Returns:
            list[Binding]: Shown bindings.
        """
        keys = [binding for binding in self.keys.values() if binding.show]
        return keys

    def bind(
        self,
        keys: str,
        action: str,
        description: str = "",
        show: bool = True,
        key_display: str | None = None,
        universal: bool = False,
    ) -> None:
        """Bind keys to an action.

        Args:
            keys (str): The keys to bind. Can be a comma-separated list of keys.
            action (str): The action to bind the keys to.
            description (str, optional): An optional description for the binding.
            show (bool, optional): A flag to say if the binding should appear in the footer.
            key_display (str | None, optional): Optional string to display in the footer for the key.
            universal (bool, optional): Allow forwarding from the app to the focused widget.
        """
        all_keys = [key.strip() for key in keys.split(",")]
        for key in all_keys:
            self.keys[key] = Binding(
                key,
                action,
                description,
                show=show,
                key_display=key_display,
                universal=universal,
            )

    def get_key(self, key: str) -> Binding:
        """Get a binding if it exists.

        Args:
            key (str): Key to look up.

        Raises:
            NoBinding: If the binding does not exist.

        Returns:
            Binding: A binding object for the key,
        """
        try:
            return self.keys[key]
        except KeyError:
            raise NoBinding(f"No binding for {key}") from None
