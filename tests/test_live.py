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
    assert disp.get_instruments_list() == ['isgri', 'jemx', 'polar', 'spi_acs']
    
def test_waiting():
    from oda_api.api import DispatcherAPI, UserError
    disp=DispatcherAPI(
                host=get_platform_dispatcher(),
                instrument="isgri",
            )

    with pytest.raises(UserError):
        disp.poll()

    assert disp.wait
    
    disp.get_product(
                instrument="isgri", 
                product="isgri_image", 
                product_type="Real", 
                osa_version="OSA10.2",
                E1_keV=25.0,
                E2_keV=80.0,
                scw_list="066500220010.001",
            )

