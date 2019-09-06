import os
import pytest

@pytest.mark.skipif('DISPATCHER_ENDPOINT' not in os.environ, reason="no DISPATCHER_ENDPOINT variable set")
def test_instruments():
    from oda_api.api import DispatcherAPI
    disp=DispatcherAPI(host="cdcihn/staging-1.2/dispatcher",instrument="mock")
    print(disp.get_instruments_list())
    
