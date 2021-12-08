# we could make a plugin, but it's more effort
import pytest
import jwt

from cdci_data_analysis.pytest_fixtures import (
            dispatcher_live_fixture,
            dispatcher_test_conf_fn,
            dispatcher_test_conf,
            dispatcher_debug,
            dispatcher_nodebug,
            dispatcher_long_living_fixture,
            default_token_payload,
        )

pytest_options = ["slow", "dda", "live"]

def pytest_addoption(parser):
    for option in pytest_options:
        parser.addoption(
            f"--run-{option}", action="store_true", default=False, help=f"run {option} tests",
        )
        parser.addoption(
            f"--run-only-{option}", action="store_true", default=False, help=f"run only {option} tests",
        )

def pytest_collection_modifyitems(config, items):
    for option in pytest_options:
        if config.getoption(f"--run-{option}") or config.getoption(f"--run-only-{option}"):
            print(f"--run-{option} given in cli: do not skip slow tests")
        else:
            for item in items:
                if option in item.keywords:
                    item.add_marker(pytest.mark.skip(reason=f"need --run-{option} option to run"))

        if config.getoption(f"--run-only-{option}"):
            for item in items:
                if option not in item.keywords:
                    item.add_marker(pytest.mark.skip(reason=f"--run-only-{option} prevents this test from running"))



@pytest.fixture
def dispatcher_api(dispatcher_live_fixture):
    import oda_api
    disp = oda_api.api.DispatcherAPI(
        url=dispatcher_live_fixture
    )
    disp.allow_token_discovery = False
    return disp
    

@pytest.fixture
def secret_key(dispatcher_test_conf):
    return dispatcher_test_conf['secret_key']

@pytest.fixture
def default_token(default_token_payload, secret_key) -> str:    
    token = jwt.encode(default_token_payload, secret_key, algorithm='HS256')
    # this changes depending on jwt implementation
    if isinstance(token, bytes):
        token = token.decode()
    return token
