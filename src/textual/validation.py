"""

This module provides a number of classes for validating input.

See [Validating Input](/widgets/input/#validating-input) for details.

"""

from __future__ import annotations

import math
import re
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Pattern, Sequence
from urllib.parse import urlparse

import rich.repr


@dataclass
class ValidationResult:
    """The result of calling a `Validator.validate` method."""

    failures: Sequence[Failure] = field(default_factory=list)
    """A list of reasons why the value was invalid. Empty if valid=True"""

    @staticmethod
    def merge(results: Sequence["ValidationResult"]) -> "ValidationResult":
        """Merge multiple ValidationResult objects into one.

        Args:
            results: List of ValidationResult objects to merge.

        Returns:
            Merged ValidationResult object.
        """
        is_valid = all(result.is_valid for result in results)
        failures = [failure for result in results for failure in result.failures]
        if is_valid:
            return ValidationResult.success()
        else:
            return ValidationResult.failure(failures)

    @staticmethod
    def success() -> ValidationResult:
        """Construct a successful ValidationResult.

        Returns:
            A successful ValidationResult.
        """
        return ValidationResult()

    @staticmethod
    def failure(failures: Sequence[Failure]) -> ValidationResult:
        """Construct a failure ValidationResult.

        Args:
            failures: The failures.

        Returns:
            A failure ValidationResult.
        """
        return ValidationResult(failures)

    @property
    def failure_descriptions(self) -> list[str]:
        """Utility for extracting failure descriptions as strings.

        Useful if you don't care about the additional metadata included in the `Failure` objects.

        Returns:
            A list of the string descriptions explaining the failing validations.
        """
        return [
            failure.description
            for failure in self.failures
            if failure.description is not None
        ]

    @property
    def is_valid(self) -> bool:
        """True if the validation was successful."""
        return len(self.failures) == 0


@dataclass
class Failure:
    """Information about a validation failure."""

    validator: Validator
    """The Validator which produced the failure."""
    value: str | None = None
    """The value which resulted in validation failing."""
    description: str | None = None
    """An optional override for describing this failure. Takes precedence over any messages set in the Validator."""

    def __post_init__(self) -> None:
        # If a failure message isn't supplied, try to get it from the Validator.
        if self.description is None:
            if self.validator.failure_description is not None:
                self.description = self.validator.failure_description
            else:
                self.description = self.validator.describe_failure(self)

    def __rich_repr__(self) -> rich.repr.Result:  # pragma: no cover
        yield self.value
        yield self.validator
        yield self.description


class Validator(ABC):
    """Base class for the validation of string values.

    Commonly used in conjunction with the `Input` widget, which accepts a
    list of validators via its constructor. This validation framework can also be used to validate any 'stringly-typed'
    values (for example raw command line input from `sys.args`).

    To implement your own `Validator`, subclass this class.

    Example:
        ```python
        class Palindrome(Validator):
            def validate(self, value: str) -> ValidationResult:
                def is_palindrome(value: str) -> bool:
                    return value == value[::-1]
                return self.success() if is_palindrome(value) else self.failure("Not palindrome!")
        ```
    """

    def __init__(self, failure_description: str | None = None) -> None:
        self.failure_description = failure_description
        """A description of why the validation failed.

        The description (intended to be user-facing) to attached to the Failure if the validation fails.
        This failure description is ultimately accessible at the time of validation failure  via the `Input.Changed`
        or `Input.Submitted` event, and you can access it on your message handler (a method called, for example,
        `on_input_changed` or a method decorated with `@on(Input.Changed)`.
        """

    @abstractmethod
    def validate(self, value: str) -> ValidationResult:
        """Validate the value and return a ValidationResult describing the outcome of the validation.

        Args:
            value: The value to validate.

        Returns:
            The result of the validation.
        """

    def describe_failure(self, failure: Failure) -> str | None:
        """Return a string description of the Failure.

        Used to provide a more fine-grained description of the failure. A Validator could fail for multiple
        reasons, so this method could be used to provide a different reason for different types of failure.

        !!! warning

            This method is only called if no other description has been supplied. If you supply a description
            inside a call to `self.failure(description="...")`, or pass a description into the constructor of
            the validator, those will take priority, and this method won't be called.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        return self.failure_description

    def success(self) -> ValidationResult:
        """Shorthand for `ValidationResult(True)`.

        You can return success() from a `Validator.validate` method implementation to signal
        that validation has succeeded.

        Returns:
            A ValidationResult indicating validation succeeded.
        """
        return ValidationResult()

    def failure(
        self,
        description: str | None = None,
        value: str | None = None,
        failures: Failure | Sequence[Failure] | None = None,
    ) -> ValidationResult:
        """Shorthand for signaling validation failure.

        You can return failure(...) from a `Validator.validate` implementation to signal validation succeeded.

        Args:
            description: The failure description that will be used. When used in conjunction with the Input widget,
                this is the description that will ultimately be available inside the handler for `Input.Changed`. If not
                supplied, the `failure_description` from the `Validator` will be used. If that is not supplied either,
                then the `describe_failure` method on `Validator` will be called.
            value: The value that was considered invalid. This is optional, and only needs to be supplied if required
                in your `Input.Changed` handler.
            failures: The reasons the validator failed. If not supplied, a generic `Failure` will be included in the
                ValidationResult returned from this function.

        Returns:
            A ValidationResult representing failed validation, and containing the metadata supplied
                to this function.
        """
        if isinstance(failures, Failure):
            failures = [failures]

        result = ValidationResult(
            failures or [Failure(validator=self, value=value, description=description)],
        )
        return result


class Regex(Validator):
    """A validator that checks the value matches a regex (via `re.fullmatch`)."""

    def __init__(
        self,
        regex: str | Pattern[str],
        flags: int | re.RegexFlag = 0,
        failure_description: str | None = None,
    ) -> None:
        super().__init__(failure_description=failure_description)
        self.regex = regex
        """The regex which we'll validate is matched by the value."""
        self.flags = flags
        """The flags to pass to `re.fullmatch`."""

    class NoResults(Failure):
        """Indicates validation failed because the regex could not be found within the value string."""

    def validate(self, value: str) -> ValidationResult:
        """Ensure that the value matches the regex.

        Args:
            value: The value that should match the regex.

        Returns:
            The result of the validation.
        """
        regex = self.regex
        has_match = re.fullmatch(regex, value, flags=self.flags) is not None
        if not has_match:
            failures = [Regex.NoResults(self, value)]
            return self.failure(failures=failures)
        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        return f"Must match regular expression {self.regex!r} (flags={self.flags})."


class Number(Validator):
    """Validator that ensures the value is a number, with an optional range check."""

    def __init__(
        self,
        minimum: float | None = None,
        maximum: float | None = None,
        failure_description: str | None = None,
    ) -> None:
        super().__init__(failure_description=failure_description)
        self.minimum = minimum
        """The minimum value of the number, inclusive. If `None`, the minimum is unbounded."""
        self.maximum = maximum
        """The maximum value of the number, inclusive. If `None`, the maximum is unbounded."""

    class NotANumber(Failure):
        """Indicates a failure due to the value not being a valid number (decimal/integer, inc. scientific notation)"""

    class NotInRange(Failure):
        """Indicates a failure due to the number not being within the range [minimum, maximum]."""

    def validate(self, value: str) -> ValidationResult:
        """Ensure that `value` is a valid number, optionally within a range.

        Args:
            value: The value to validate.

        Returns:
            The result of the validation.
        """
        try:
            float_value = float(value)
        except ValueError:
            return ValidationResult.failure([Number.NotANumber(self, value)])

        if math.isnan(float_value) or math.isinf(float_value):
            return ValidationResult.failure([Number.NotANumber(self, value)])

        if not self._validate_range(float_value):
            return ValidationResult.failure(
                [Number.NotInRange(self, value)],
            )
        return self.success()

    def _validate_range(self, value: float) -> bool:
        """Return a boolean indicating whether the number is within the range specified in the attributes."""
        if self.minimum is not None and value < self.minimum:
            return False
        if self.maximum is not None and value > self.maximum:
            return False
        return True

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        if isinstance(failure, Number.NotANumber):
            return "Must be a valid number."
        elif isinstance(failure, Number.NotInRange):
            if self.minimum is None and self.maximum is not None:
                return f"Must be less than or equal to {self.maximum}."
            elif self.minimum is not None and self.maximum is None:
                return f"Must be greater than or equal to {self.minimum}."
            else:
                return f"Must be between {self.minimum} and {self.maximum}."
        else:
            return None


class Integer(Number):
    """Validator which ensures the value is an integer which falls within a range."""

    class NotAnInteger(Failure):
        """Indicates a failure due to the value not being a valid integer."""

    def validate(self, value: str) -> ValidationResult:
        """Ensure that `value` is an integer, optionally within a range.

        Args:
            value: The value to validate.

        Returns:
            The result of the validation.
        """
        # First, check that we're dealing with a number in the range.
        number_validation_result = super().validate(value)
        if not number_validation_result.is_valid:
            return number_validation_result

        # We know it's a number, but is that number an integer?
        try:
            int(value)
        except ValueError:
            return ValidationResult.failure([Integer.NotAnInteger(self, value)])
        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        if isinstance(failure, (Integer.NotANumber, Integer.NotAnInteger)):
            return "Must be a valid integer."
        elif isinstance(failure, Integer.NotInRange):
            if self.minimum is None and self.maximum is not None:
                return f"Must be less than or equal to {self.maximum}."
            elif self.minimum is not None and self.maximum is None:
                return f"Must be greater than or equal to {self.minimum}."
            else:
                return f"Must be between {self.minimum} and {self.maximum}."
        else:
            return None


class Length(Validator):
    """Validate that a string is within a range (inclusive)."""

    def __init__(
        self,
        minimum: int | None = None,
        maximum: int | None = None,
        failure_description: str | None = None,
    ) -> None:
        super().__init__(failure_description=failure_description)
        self.minimum = minimum
        """The inclusive minimum length of the value, or None if unbounded."""
        self.maximum = maximum
        """The inclusive maximum length of the value, or None if unbounded."""

    class Incorrect(Failure):
        """Indicates a failure due to the length of the value being outside the range."""

    def validate(self, value: str) -> ValidationResult:
        """Ensure that value falls within the maximum and minimum length constraints.

        Args:
            value: The value to validate.

        Returns:
            The result of the validation.
        """
        too_short = self.minimum is not None and len(value) < self.minimum
        too_long = self.maximum is not None and len(value) > self.maximum
        if too_short or too_long:
            return ValidationResult.failure([Length.Incorrect(self, value)])
        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        if isinstance(failure, Length.Incorrect):
            if self.minimum is None and self.maximum is not None:
                return f"Must be shorter than {self.maximum} characters."
            elif self.minimum is not None and self.maximum is None:
                return f"Must be longer than {self.minimum} characters."
            else:
                return f"Must be between {self.minimum} and {self.maximum} characters."
        return None


class Function(Validator):
    """A flexible validator which allows you to provide custom validation logic."""

    def __init__(
        self,
        function: Callable[[str], bool],
        failure_description: str | None = None,
    ) -> None:
        super().__init__(failure_description=failure_description)
        self.function = function
        """Function which takes the value to validate and returns True if valid, and False otherwise."""

    class ReturnedFalse(Failure):
        """Indicates validation failed because the supplied function returned False."""

    def validate(self, value: str) -> ValidationResult:
        """Validate that the supplied function returns True.

        Args:
            value: The value to pass into the supplied function.

        Returns:
            A ValidationResult indicating success if the function returned True,
                and failure if the function return False.
        """
        is_valid = self.function(value)
        if is_valid:
            return self.success()
        return self.failure(failures=Function.ReturnedFalse(self, value))

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        return self.failure_description


class URL(Validator):
    """Validator that checks if a URL is valid (ensuring a scheme is present)."""

    class InvalidURL(Failure):
        """Indicates that the URL is not valid."""

    def validate(self, value: str) -> ValidationResult:
        """Validates that `value` is a valid URL (contains a scheme).

        Args:
            value: The value to validate.

        Returns:
            The result of the validation.
        """
        invalid_url = ValidationResult.failure([URL.InvalidURL(self, value)])
        try:
            parsed_url = urlparse(value)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                return invalid_url
        except ValueError:
            return invalid_url

        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        return "Must be a valid URL."


class File(Validator):
    def __init__(
        self,
        must_exists: bool = False,
        must_not_exists: bool = False,
        required_permissions: str | None = None,
        extensions: str | list[str] | None = None,
        failure_description: str | None = None,
    ) -> None:
        """
        Initialize the file validator.

        :param must_exist: Specify if the file must exist.
        :param must__not_exist: Specify if the file must not exist.
        :param required_permissions: File permission to check (e.g., "r", "w", "x", "rwx").
        :param extensions: Expected file extension (e.g., ".txt").
        """
        super().__init__(failure_description=failure_description)
        self.must_exists = must_exists
        self.must_not_exists = must_not_exists
        if self.must_exists and self.must_not_exists:
            raise ValueError(
                "Conflicts on existence contraints, a path must exists or not"
            ) from None
        self.required_permissions = required_permissions or ""
        self.extensions = [extensions] if isinstance(extensions, str) else extensions

    class NotAFile(Failure):
        """Indicate that the path is not a file."""

    class DoesNotExists(Failure):
        """Indicate that the file does not exists."""

    class AlreadyExists(Failure):
        """Indicate that the file exists and should not."""

    class ExtensionFileNotSupported(Failure):
        """Indicate that the file exists and should not."""

    class IsNotReadable(Failure):
        """Indicate that the file is not readable."""

    class IsNotWritable(Failure):
        """Indicate that the file is not writable."""

    class IsNotExecutable(Failure):
        """Indicate that the file is not executable."""

    def validate(self, value: str) -> ValidationResult:
        """Check if the given path meets all file requirements."""
        file_path = Path(value)

        # Check if path is a file
        if file_path.exists() and not file_path.is_file():
            return ValidationResult.failure([File.NotAFile(self, value)])

        # Check existence
        if self.must_exists and not file_path.exists():
            return ValidationResult.failure([File.DoesNotExists(self, value)])
        if self.must_not_exists and file_path.exists():
            return ValidationResult.failure([File.AlreadyExists(self, value)])

        # Check file permissions
        if file_path.exists():
            if "r" in self.required_permissions:
                if not os.access(file_path, mode=os.R_OK):
                    return ValidationResult.failure([File.IsNotReadable(self, value)])
            if "w" in self.required_permissions:
                if not os.access(file_path, mode=os.W_OK):
                    return ValidationResult.failure([File.IsNotWritable(self, value)])
            if "x" in self.required_permissions:
                if not os.access(file_path, mode=os.X_OK):
                    return ValidationResult.failure([File.IsNotExecutable(self, value)])

        # Check file extension
        if self.extensions and file_path.suffix not in self.extensions:
            return ValidationResult.failure(
                [File.ExtensionFileNotSupported(self, value)]
            )

        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        if isinstance(failure, File.NotAFile):
            return "Path is not a file"
        elif isinstance(failure, File.DoesNotExists):
            return "File does not exist"
        elif isinstance(failure, File.AlreadyExists):
            return "File does already exist"
        elif isinstance(failure, File.IsNotReadable):
            return "File is not readable by this user"
        elif isinstance(failure, File.IsNotWritable):
            return "File is not writable by this user"
        elif isinstance(failure, File.IsNotExecutable):
            return "File is not executable by this user"
        elif isinstance(failure, File.ExtensionFileNotSupported):
            return f"File has not a valid extensions, supported extensions are: {self.extensions}"
        return None


# Validator for folder paths
class Folder(Validator):
    def __init__(
        self,
        must_exists: bool = False,
        must_not_exists: bool = False,
        required_permissions: str | None = None,
        failure_description: str | None = None,
    ) -> None:
        """
        Initialize the folder validator.

        :param must_exists: Specify if the folder must exist.
        :param must_not_exists: Specify if the folder must not exist.
        :param required_permission: Folder permission to check (e.g., "r", "w", "x").
        """
        super().__init__(failure_description=failure_description)
        self.must_exists = must_exists
        self.must_not_exists = must_not_exists
        if self.must_exists and self.must_not_exists:
            raise ValueError(
                "Conflicts on existence contraints, a path must exists or not"
            ) from None
        self.required_permissions = required_permissions or ""

    class NotAFolder(Failure):
        """Indicate that the path is not a folder."""

    class DoesNotExists(Failure):
        """Indicate that the file does not exists."""

    class AlreadyExists(Failure):
        """Indicate that the file exists and should not."""

    class IsNotReadable(Failure):
        """Indicate that the file is not readable."""

    class IsNotWritable(Failure):
        """Indicate that the file is not writable."""

    class IsNotExecutable(Failure):
        """Indicate that the file is not executable."""

    def validate(self, value: str) -> ValidationResult:
        """Check if the given path meets all file requirements."""
        folder_path = Path(value)

        # Check if path is a folder
        if folder_path.exists() and not folder_path.is_dir():
            return ValidationResult.failure([Folder.NotAFolder(self, value)])

        # Check existence
        if self.must_exists and not folder_path.exists():
            return ValidationResult.failure([Folder.DoesNotExists(self, value)])
        if self.must_not_exists and folder_path.exists():
            return ValidationResult.failure([Folder.AlreadyExists(self, value)])

        # Check file permissions
        if folder_path.exists():
            if "r" in self.required_permissions:
                if not os.access(folder_path, mode=os.R_OK):
                    return ValidationResult.failure([Folder.IsNotReadable(self, value)])
            if "w" in self.required_permissions:
                if not os.access(folder_path, mode=os.W_OK):
                    return ValidationResult.failure([Folder.IsNotWritable(self, value)])
            if "x" in self.required_permissions:
                if not os.access(folder_path, mode=os.X_OK):
                    return ValidationResult.failure(
                        [Folder.IsNotExecutable(self, value)]
                    )

        return self.success()

    def describe_failure(self, failure: Failure) -> str | None:
        """Describes why the validator failed.

        Args:
            failure: Information about why the validation failed.

        Returns:
            A string description of the failure.
        """
        if isinstance(failure, Folder.NotAFolder):
            return "Path is not a folder"
        elif isinstance(failure, Folder.DoesNotExists):
            return "Folder does not exist"
        elif isinstance(failure, Folder.AlreadyExists):
            return "Folder does already exist"
        elif isinstance(failure, Folder.IsNotReadable):
            return "Folder is not readable by this user"
        elif isinstance(failure, Folder.IsNotWritable):
            return "Folder is not writable by this user"
        elif isinstance(failure, Folder.IsNotExecutable):
            return "Folder is not executable by this user"
        return None
