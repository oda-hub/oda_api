import os
import time
import random
import requests
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


def pick_scw():
    scwlist = requests.get("https://www.astro.unige.ch/cdci/astrooda/dispatch-data/"
                "gw/timesystem/api/v1.0/scwlist/cons/"
                "2002-12-17T08:00:00/2020-12-21T08:00:00"
                "?&ra=83&dec=22&radius=200.0&min_good_isgri=1000").json()
    return random.choice(scwlist) + ".001"

def get_disp(wait=True):
    from oda_api.api import DispatcherAPI
    return DispatcherAPI(
                host=get_platform_dispatcher(),
                instrument="isgri",
                wait=wait,
            )
    
def test_waiting():
    from oda_api.api import UserError

    disp = get_disp()

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
                scw_list=pick_scw(),
            )

def test_not_waiting():
    from oda_api.api import DispatcherAPI, UserError

    disp = get_disp(wait=False)
    disp2 = get_disp(wait=False)

    assert not disp.wait
    assert not disp2.wait
    
    with pytest.raises(UserError):
        disp.poll()
    
    disp.get_product(
                instrument="isgri", 
                product="isgri_image", 
                product_type="Real", 
                osa_version="OSA10.2",
                E1_keV=25.0,
                E2_keV=80.0,
                scw_list=pick_scw(),
            )

    disp2.get_product(
                instrument="isgri", 
                product="isgri_image", 
                product_type="Real", 
                osa_version="OSA10.2",
                E1_keV=80.0,
                E2_keV=200.0,
                scw_list=disp.parameters_dict['scw_list'],
            )

    assert disp.is_submitted
    assert not disp.is_complete
    assert disp2.is_submitted
    assert not disp2.is_complete

    done = False
    while not done:
        done = True
        if not disp.is_complete:
            disp.poll()
            done = False

        if not disp2.is_complete:
            disp2.poll()
            done = False

        time.sleep(2)



