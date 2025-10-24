# Loopretry

Loop retry is a library which allow to retry specific code block in Python.

It is different from many other retries libraries because it allows to retry a block
of code, not just a lambda or a function.

Usage

```python

from loopretry import retries
import time

for retry in retries(10):
    with retry():
        # any code you want to retry in case of exception
        assert int(time.time()) % 10 == 0, "Not a round number!"
```

This attempts the block up to 10 times with a 1-second delay between failures. On first success it stops. If the final attempt still fails, the exception is raised.

Typical use is waiting for eventual consistency in small integration tests.

An example for use in pytest, which waits for a metric to appear in Prometheus
for up to 30 seconds:

```python

    for retry in retries(30):
        with retry():
            assert prom_query('myapp_up{server="srv1"}') == 1.0

```

# API

```python
def retries(
    max_attempts: int,
    delay_sec: float = 1.0,
    expected_exception: type[BaseException] | tuple[type[BaseException], ...] = Exception,
) -> Iterable[Callable[[], ContextManager[None]]]
```

- max_attempts: total number of attempts (>= 1).
- delay_sec: delay between failed attempts.
- expected_exception: exception class or tuple of classes to retry on. Defaults to Exception.

Returns an iterable. Each iteration yields a callable that returns a context manager. If the block raises one of expected_exception and attempts remain, the exception is swallowed, a delay is applied, and the loop continues. Otherwise, the exception is propagated.

# License

MIT.

# Contributing

Contributions are welcome.
