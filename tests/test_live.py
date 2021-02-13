import os
import pytest

def get_platform_dispatcher(platform="staging-1-2"):
    import odakb.sparql as S
    return list(S.select('?p a oda:platform; oda:location ?loc . ?p ?x ?y', '?p ?x ?y', tojdict=True)
                ["oda:staging-1-2"]["oda:location"].keys())[0]

def test_instruments():
    from oda_api.api import DispatcherAPI
    disp=DispatcherAPI(
                host=get_platform_dispatcher(),
                instrument="mock",
            )
    print(disp.get_instruments_list())
    
