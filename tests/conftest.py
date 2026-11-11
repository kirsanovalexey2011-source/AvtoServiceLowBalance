import pytest

from app.api.auth import limiter


@pytest.fixture(autouse=True)
def isolate_rate_limit_storage():
    """Keep SlowAPI's process-wide counters from leaking between tests."""
    limiter._storage.reset()
    yield
    limiter._storage.reset()
