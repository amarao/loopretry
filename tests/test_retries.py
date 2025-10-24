import time
import sys
import pytest

from loopretry import retries


def test_invalid_max_attempts(subtests):
    with pytest.raises(ValueError):
        retries(0)
    with subtests.test("negative"):
        with pytest.raises(ValueError):
            retries(-1)


def test_invalid_expected_exception_values_raise_type_error(subtests):
    # Non-exception value
    with pytest.raises(TypeError):
        list(retries(3, expected_exception=123))

    # Instance instead of class
    class E1(Exception):
        pass

    with subtests.test("instance instead of class"):
        with pytest.raises(TypeError):
            list(retries(3, expected_exception=E1()))

    # Tuple containing a non-exception item should fail
    with subtests.test("tuple contains non-exception"):
        with pytest.raises(TypeError):
            list(retries(3, expected_exception=(E1, 42)))


def test_no_exception(subtests):
    iterations = 0
    start = time.monotonic()
    for retry in retries(3, delay_sec=1):
        with retry():
            iterations += 1
    elapsed = time.monotonic() - start
    # Should only iterate once due to immediate success
    assert iterations == 1

    with subtests.test("no sleep on success"):
        assert elapsed < 1


def test_eventual_success_includes_sleeps_between_failures(subtests):
    delay = 0.01
    attempt = 0
    start = time.monotonic()
    for retry in retries(5, delay_sec=delay):
        with retry():
            attempt += 1
            if attempt < 3:
                raise ValueError("try again")
    elapsed = time.monotonic() - start
    # Two failures then success -> expect at least 2 sleeps
    assert attempt == 3
    with subtests.test("elapsed time"):
        assert elapsed >= delay * 2


def test_exhaustion_raises_original_exception_and_sleeps_between_attempts(subtests):
    delay = 0.01
    start = time.monotonic()
    with pytest.raises(ValueError):
        for retry in retries(3, delay_sec=delay):
            with retry():
                raise ValueError("boom")
    elapsed = time.monotonic() - start
    # For 3 attempts, there are 2 sleeps (between attempt 1->2 and 2->3)
    with subtests.test("elapsed time"):
        assert elapsed >= delay * 2


def test_baseexception_not_swallowed():
    class MyBase(BaseException):
        pass

    with pytest.raises(MyBase):
        for retry in retries(3, delay_sec=0.01):
            with retry():
                raise MyBase("do not swallow")


def test_single_attempt_raises_without_retry():
    attempts = 0
    try:
        for retry in retries(1, delay_sec=0.01):
            with retry():
                attempts += 1
                raise ValueError("boom")
        raise AssertionError("Expected ValueError was not raised")
    except ValueError:
        # the exception we want
        pass

    # With a single attempt there must be no retry
    assert attempts == 1


def test_expected_exceptions_catches_custom_exception_eventual_success(subtests):
    class CustomError(Exception):
        pass

    delay = 0.01
    attempt = 0
    start = time.monotonic()
    for retry in retries(5, delay_sec=delay, expected_exception=CustomError):
        with retry():
            attempt += 1
            if attempt < 3:
                raise CustomError("try again")
    elapsed = time.monotonic() - start
    assert attempt == 3
    with subtests.test("elapsed time"):
        assert elapsed >= delay * 2


def test_expected_exceptions_catches_system_exit_eventual_success(subtests):
    delay = 0.01
    attempt = 0
    start = time.monotonic()
    for retry in retries(5, delay_sec=delay, expected_exception=SystemExit):
        with retry():
            attempt += 1
            if attempt < 3:
                sys.exit(
                    "Test test_expected_exceptions_catches_system_exit_eventual_success failed"
                )
    elapsed = time.monotonic() - start
    assert attempt == 3
    with subtests.test("elapsed time"):
        assert elapsed >= delay * 2


def test_expected_exceptions_does_not_catch_non_listed():
    with pytest.raises(TypeError):
        for retry in retries(3, delay_sec=0.01, expected_exception=ValueError):
            with retry():
                raise TypeError("not expected")
