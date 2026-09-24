import pytest

from src.core.config import Config
from src.interceptors.network_interceptor import NetworkInterceptor


@pytest.fixture(scope="session")
def config() -> Config:
    return Config.from_env()


@pytest.fixture
def interceptor(page):
    captured = NetworkInterceptor()
    captured.start_capture(page.context)
    yield captured


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    if report.when == "call" and report.failed:
        captured = item.funcargs.get("interceptor")
        if captured is not None:
            captured.save_failure(item.name)
