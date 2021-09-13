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

def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )

def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "dda" in item.keywords:
            item.add_marker(skip_slow)
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


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
def default_token(default_token_payload, secret_key):
    return jwt.encode(default_token_payload, secret_key, algorithm='HS256')
