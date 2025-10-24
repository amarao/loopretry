from __future__ import annotations

import time
from types import TracebackType
from typing import (
    Callable,
    ContextManager,
    Iterable,
    Iterator,
    Optional,
    Tuple,
    Type,
    Union,
)


ExpectedException = Union[Type[BaseException], Tuple[Type[BaseException], ...]]


def retries(
    max_attempts: int,
    delay_sec: float = 1.0,
    expected_exception: ExpectedException = Exception,
) -> Iterable[Callable[[], ContextManager[None]]]:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    # Validate expected_exception is an exception class or a tuple of them
    def _is_exception_type(obj: object) -> bool:
        try:
            return isinstance(obj, type) and issubclass(obj, BaseException)
        except Exception:
            return False

    if isinstance(expected_exception, tuple):
        if not expected_exception or not all(
            _is_exception_type(e) for e in expected_exception
        ):
            raise TypeError(
                "expected_exception must be an exception type or tuple of exception types"
            )
    elif not _is_exception_type(expected_exception):
        raise TypeError(
            "expected_exception must be an exception type or tuple of exception types"
        )

    class _RetryController:
        def __iter__(self) -> Iterator[Callable[[], ContextManager[None]]]:
            completed: bool = False

            class _RetryAttempt:
                def __init__(self, index: int):
                    self.index: int = index

                def __call__(self) -> "_RetryAttempt":
                    return self

                def __enter__(self) -> None:
                    return None

                def __exit__(
                    self,
                    exc_type: Optional[Type[BaseException]],
                    _exc: Optional[BaseException],
                    _tb: Optional[TracebackType],
                ) -> bool:
                    nonlocal completed
                    if exc_type is None:
                        completed = True
                        return False

                    # Retry only if there are remaining attempts
                    if (
                        exc_type is not None
                        and issubclass(exc_type, expected_exception)
                        and self.index < max_attempts - 1
                    ):
                        time.sleep(delay_sec)
                        return True

                    return False

            for attempt in range(max_attempts):
                if completed:
                    break
                yield _RetryAttempt(attempt)

    return _RetryController()
