from __future__ import annotations


import pytest

from textual.validation import (
    URL,
    Failure,
    File,
    Folder,
    Function,
    Integer,
    Length,
    Number,
    Regex,
    ValidationResult,
    Validator,
)

VALIDATOR = Function(lambda value: True)


def test_ValidationResult_merge_successes():
    results = [ValidationResult.success(), ValidationResult.success()]
    assert ValidationResult.merge(results) == ValidationResult.success()


def test_ValidationResult_merge_failures():
    failure_one = Failure(VALIDATOR, "1")
    failure_two = Failure(VALIDATOR, "2")
    results = [
        ValidationResult.failure([failure_one]),
        ValidationResult.failure([failure_two]),
        ValidationResult.success(),
    ]
    expected_result = ValidationResult.failure([failure_one, failure_two])
    assert ValidationResult.merge(results) == expected_result


def test_ValidationResult_failure_descriptions():
    result = ValidationResult.failure(
        [
            Failure(VALIDATOR, description="One"),
            Failure(VALIDATOR, description="Two"),
            Failure(VALIDATOR, description="Three"),
        ],
    )
    assert result.failure_descriptions == ["One", "Two", "Three"]


class ValidatorWithDescribeFailure(Validator):
    def validate(self, value: str) -> ValidationResult:
        return self.failure()

    def describe_failure(self, failure: Failure) -> str | None:
        return "describe_failure"


def test_Failure_description_priorities_parameter_only():
    number_validator = Number(failure_description="ABC")
    non_number_value = "x"
    result = number_validator.validate(non_number_value)
    # The inline value takes priority over the describe_failure.
    assert result.failures[0].description == "ABC"


def test_Failure_description_priorities_parameter_and_describe_failure():
    validator = ValidatorWithDescribeFailure(failure_description="ABC")
    result = validator.validate("x")
    # Even though the validator has a `describe_failure`, we've provided it
    # inline and the inline value should take priority.
    assert result.failures[0].description == "ABC"


def test_Failure_description_priorities_describe_failure_only():
    validator = ValidatorWithDescribeFailure()
    result = validator.validate("x")
    assert result.failures[0].description == "describe_failure"


class ValidatorWithFailureMessageAndNoDescribe(Validator):
    def validate(self, value: str) -> ValidationResult:
        return self.failure(description="ABC")


def test_Failure_description_parameter_and_description_inside_validate():
    validator = ValidatorWithFailureMessageAndNoDescribe()
    result = validator.validate("x")
    assert result.failures[0].description == "ABC"


class ValidatorWithFailureMessageAndDescribe(Validator):
    def validate(self, value: str) -> ValidationResult:
        return self.failure(value=value, description="ABC")

    def describe_failure(self, failure: Failure) -> str | None:
        return "describe_failure"


def test_Failure_description_describe_and_description_inside_validate():
    # This is kind of a weird case - there's no reason to supply both of
    # these but lets still make sure we're sensible about how we handle it.
    validator = ValidatorWithFailureMessageAndDescribe()
    result = validator.validate("x")
    assert result.failures == [Failure(validator, "x", "ABC")]


@pytest.mark.parametrize(
    "value, minimum, maximum, expected_result",
    [
        ("123", None, None, True),  # valid number, no range
        ("-123", None, None, True),  # valid negative number, no range
        ("123.45", None, None, True),  # valid float, no range
        ("1.23e-4", None, None, True),  # valid scientific notation, no range
        ("abc", None, None, False),  # non-numeric string, no range
        ("123", 100, 200, True),  # valid number within range
        ("99", 100, 200, False),  # valid number but not in range
        ("201", 100, 200, False),  # valid number but not in range
        ("1.23e4", 0, 50000, True),  # valid scientific notation within range
        ("inf", None, None, False),  # infinity never valid
        ("nan", None, None, False),  # nan never valid
        ("-inf", None, None, False),  # nan never valid
        ("-4", 0, 5, False),  # valid negative number, out of range with zero
        ("2", -3, 0, False),  # valid number out of range with zero
        ("-2", -3, 0, True),  # negative in range
    ],
)
def test_Number_validate(value, minimum, maximum, expected_result):
    validator = Number(minimum=minimum, maximum=maximum)
    result = validator.validate(value)
    assert result.is_valid == expected_result


@pytest.mark.parametrize(
    "regex, value, expected_result",
    [
        (r"\d+", "123", True),  # matches regex for one or more digits
        (r"\d+", "abc", False),  # does not match regex for one or more digits
        (r"[a-z]+", "abc", True),  # matches regex for one or more lowercase letters
        (
            r"[a-z]+",
            "ABC",
            False,
        ),  # does not match regex for one or more lowercase letters
        (r"\w+", "abc123", True),  # matches regex for one or more word characters
        (r"\w+", "!@#", False),  # does not match regex for one or more word characters
    ],
)
def test_Regex_validate(regex, value, expected_result):
    validator = Regex(regex)
    result = validator.validate(value)
    assert result.is_valid == expected_result


@pytest.mark.parametrize(
    "value, minimum, maximum, expected_result",
    [
        ("123", None, None, True),  # valid integer, no range
        ("-123", None, None, True),  # valid negative integer, no range
        ("123.45", None, None, False),  # float, not a valid integer
        ("1.23e-4", None, None, False),  # scientific notation, not a valid integer
        ("abc", None, None, False),  # non-numeric string, not a valid integer
        ("123", 100, 200, True),  # valid integer within range
        ("99", 100, 200, False),  # valid integer but not in range
        ("201", 100, 200, False),  # valid integer but not in range
        (
            "1.23e4",
            None,
            None,
            False,
        ),  # valid scientific notation, even resolving to an integer, is not valid
        ("123.", None, None, False),  # periods not valid in integers
        ("123_456", None, None, True),  # underscores are valid python
        ("_123_456", None, None, False),  # leading underscores are not valid python
        ("-123", -123, -123, True),  # valid negative number in minimal range
    ],
)
def test_Integer_validate(value, minimum, maximum, expected_result):
    validator = Integer(minimum=minimum, maximum=maximum)
    result = validator.validate(value)
    assert result.is_valid == expected_result


@pytest.mark.parametrize(
    "value, min_length, max_length, expected_result",
    [
        ("", None, None, True),  # empty string
        ("test", None, None, True),  # any string with no restrictions
        ("test", 5, None, False),  # shorter than minimum length
        ("test", None, 3, False),  # longer than maximum length
        ("test", 4, 4, True),  # exactly matches minimum and maximum length
        ("test", 2, 6, True),  # within length range
    ],
)
def test_Length_validate(value, min_length, max_length, expected_result):
    validator = Length(minimum=min_length, maximum=max_length)
    result = validator.validate(value)
    assert result.is_valid == expected_result


@pytest.mark.parametrize(
    "value, expected_result",
    [
        ("http://example.com", True),  # valid URL
        ("https://example.com", True),  # valid URL with https
        ("www.example.com", False),  # missing scheme
        ("://example.com", False),  # invalid URL (no scheme)
        ("https:///path", False),  # missing netloc
        (
            "redis://username:pass[word@localhost:6379/0",
            False,
        ),  # invalid URL characters
        ("", False),  # empty string
    ],
)
def test_URL_validate(value, expected_result):
    validator = URL()
    result = validator.validate(value)
    assert result.is_valid == expected_result


@pytest.mark.parametrize(
    "function, failure_description, is_valid",
    [
        ((lambda value: True), None, True),
        ((lambda value: False), "failure!", False),
    ],
)
def test_Function_validate(function, failure_description, is_valid):
    validator = Function(function, failure_description)
    result = validator.validate("x")
    assert result.is_valid is is_valid
    if result.failure_descriptions:
        assert result.failure_descriptions[0] == failure_description


def test_Integer_failure_description_when_NotANumber():
    """Regression test for https://github.com/Textualize/textual/issues/4413"""
    validator = Integer()
    result = validator.validate("x")
    assert result.is_valid is False
    assert result.failure_descriptions[0] == "Must be a valid integer."


# Test File validator


def test_File_existing_file_with_correct_extension(tmp_path):
    # create dir
    tmp_path.mkdir(parents=True, exist_ok=True)
    temp_file = tmp_path / "correct_extension.txt"
    # create file
    temp_file.touch()
    # instantiate File validator
    validator = File(must_exists=True, extensions=".txt")
    result = validator.validate(str(temp_file))
    assert result.is_valid


def test_File_existing_file_with_wrong_extension(tmp_path):
    # create dir
    tmp_path.mkdir(parents=True, exist_ok=True)
    temp_file = tmp_path / "wrong_extension.txt"
    # create file
    temp_file.touch()
    # instantiate File validator
    validator = File(must_exists=True, extensions=".md")
    result = validator.validate(str(temp_file))
    assert not result.is_valid
    assert (
        result.failure_descriptions[0]
        == "File has not a valid extensions, supported extensions are: ['.md']"
    )


def test_File_non_existing_file_when_must_exist(tmp_path):
    # create dir
    temp_file = tmp_path / "nonexisting_file.txt"
    # instantiate File validator
    validator = File(must_exists=True)
    result = validator.validate(str(temp_file))
    assert not result.is_valid
    assert result.failure_descriptions[0] == "File does not exist"


def test_File_non_existing_file_when_must_not_exist(tmp_path):
    temp_file = tmp_path / "nonexisting_file.txt"
    # instantiate File validator
    validator = File(must_exists=False)
    result = validator.validate(str(temp_file))
    assert result.is_valid


def test_File_existing_file_without_permission(tmp_path):
    # create dir
    tmp_path.mkdir(parents=True, exist_ok=True)
    temp_file = tmp_path / "wrong_permission.txt"
    # create file
    temp_file.touch()
    # instantiate File validator
    # Simulate no read permission
    temp_file.chmod(0o200)
    validator = File(must_exists=True, required_permissions="r")
    result = validator.validate(str(temp_file))
    assert not result.is_valid
    assert result.failure_descriptions[0] == "File is not readable by this user"


def test_File_existing_file_with_required_permission(tmp_path):
    # create dir
    tmp_path.mkdir(parents=True, exist_ok=True)
    temp_file = tmp_path / "correct_permission.txt"
    # create file
    temp_file.touch()
    # instantiate File validator
    validator = File(must_exists=True, required_permissions="r")
    result = validator.validate(str(temp_file))
    assert result.is_valid


def test_File_conflict_existence_contraints(tmp_path):
    # instantiate File validator
    with pytest.raises(ValueError):
        File(must_exists=True, must_not_exists=True, extensions=".txt")


# Test Folder validator


def test_Folder_existing_folder_with_permissions(tmp_path):
    # create dir
    tmp_path.mkdir(parents=True, exist_ok=True)
    # instantiate File validator
    validator = Folder(must_exists=True, required_permissions="rwx")
    result = validator.validate(str(tmp_path))
    assert result.is_valid


def test_Folder_non_existing_folder_when_must_exist(tmp_path):
    temp_folder = tmp_path / "nonexisting_folder"
    validator = Folder(must_exists=True)
    result = validator.validate(str(temp_folder))
    assert not result.is_valid
    assert result.failure_descriptions[0] == "Folder does not exist"


def test_Folder_non_existing_folder_when_must_not_exist(tmp_path):
    temp_folder = tmp_path / "nonexisting_folder"
    validator = Folder(must_exists=False)
    result = validator.validate(temp_folder)
    assert result.is_valid


def test_Folder_existing_folder_without_write_permission(tmp_path):
    temp_folder = tmp_path / "nowrite_permission"
    temp_folder.mkdir(parents=True, exist_ok=True)
    # Remove write permission
    temp_folder.chmod(0o500)
    validator = Folder(must_exists=True, required_permissions="w")
    result = validator.validate(str(temp_folder))
    assert not result.is_valid
    assert result.failure_descriptions[0] == "Folder is not writable by this user"


def test_Folder_existing_folder_without_execute_permission(tmp_path):
    temp_folder = tmp_path / "noexec_permission"
    temp_folder.mkdir(parents=True, exist_ok=True)
    # Remove execute permission
    temp_folder.chmod(0o600)
    validator = Folder(must_exists=True, required_permissions="x")
    result = validator.validate(str(temp_folder))
    assert not result.is_valid
    assert result.failure_descriptions[0] == "Folder is not executable by this user"


def test_Folder_is_file(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    temp_file = tmp_path / "a_file.txt"
    temp_file.touch()
    validator = Folder(must_exists=True)
    result = validator.validate(str(temp_file))
    assert not result.is_valid
    assert result.failure_descriptions[0] == "Path is not a folder"


def test_Folder_conflict_existence_contraints(tmp_path):
    # instantiate File validator
    with pytest.raises(ValueError):
        Folder(must_exists=True, must_not_exists=True)
