import os
import time
import random
import requests
import pytest

def get_platform_dispatcher(platform="staging-1-2"):
    import odakb.sparql as S

    R = S.select('?p a oda:platform; oda:location ?loc . ?p ?x ?y', '?p ?x ?y', tojdict=True)
    locations = R["oda:"+platform]["oda:location"]

    try:
        return list(locations.keys())[0]
    except:
        return list(locations)[0]

def test_instruments():
    from oda_api.api import DispatcherAPI
    disp=DispatcherAPI(
                host=get_platform_dispatcher(),
                instrument="mock",
            )
    assert disp.get_instruments_list() == ['isgri', 'jemx', 'polar', 'spi_acs']


def pick_scw(kind="any"):
    if kind == "crab":
        return "066500220010.001"
    elif kind == "any":
        scwlist = requests.get("https://www.astro.unige.ch/cdci/astrooda/dispatch-data/"
                    "gw/timesystem/api/v1.0/scwlist/cons/"
                    "2002-12-17T08:00:00/2020-12-21T08:00:00"
                    "?&ra=83&dec=22&radius=200.0&min_good_isgri=1000").json()
        return random.choice(scwlist) + ".001"
    elif kind == "failing":
        return "280200770010.001"

def get_disp(wait=True, platform="staging-1-2"):
    from oda_api.api import DispatcherAPI
    return DispatcherAPI(
                host=get_platform_dispatcher(platform),
                instrument="isgri",
                wait=wait,
            )
    
def validate_data(data, scw_kind):
    if scw_kind == "crab":
        source = "Crab"

        cat = data.dispatcher_catalog_1.table

        t = cat[ cat['src_names'] == source ]
        print(t)

        assert len(t) == 1

@pytest.mark.parametrize("platform", ["staging-1-3", "staging-1-2", "production-1-2"])
@pytest.mark.parametrize("scw_kind", ["crab", "any", "failing"])
def test_waiting(scw_kind, platform):
    from oda_api.api import UserError

    disp = get_disp(wait=True, platform=platform)

    with pytest.raises(UserError):
        disp.poll()

    assert disp.wait
    
    data = disp.get_product(
                instrument="isgri", 
                product="isgri_image", 
                product_type="Real", 
                osa_version="OSA10.2",
                E1_keV=25.0,
                E2_keV=80.0,
                scw_list=pick_scw(kind=scw_kind),
            )

    print(data._n_list)

    validate_data(data, scw_kind)


@pytest.mark.parametrize("platform", ["staging-1-3", "staging-1-2", "production-1-2"])
@pytest.mark.parametrize("scw_kind", ["crab", "any", "failing"])
def test_not_waiting(scw_kind, platform):
    from oda_api.api import DispatcherAPI, UserError

    disp = get_disp(wait=False, platform=platform)
    disp2 = get_disp(wait=False, platform=platform)

    assert not disp.wait
    assert not disp2.wait
    
    with pytest.raises(UserError):
        disp.poll()
    
    print("\033[31mto first request...\033[0m")
    data = disp.get_product(
                instrument="isgri", 
                product="isgri_image", 
                product_type="Real", 
                osa_version="OSA10.2",
                E1_keV=25.0,
                E2_keV=80.0,
                scw_list=pick_scw(kind=scw_kind),
            )
    print("\033[31mfirst request:", data, "\033[0m")

    print("\033[31mto first request d2...\033[0m")
    data2 = disp2.get_product(
                instrument="isgri", 
                product="isgri_image", 
                product_type="Real", 
                osa_version="OSA10.2",
                E1_keV=40.0,
                E2_keV=200.0,
                scw_list=disp.parameters_dict['scw_list'],
            )
    print("\033[31mfirst request d2:", data, "\033[0m")

    if scw_kind == "any":
        assert disp.is_submitted
        assert not disp.is_complete

        assert disp2.is_submitted
        assert not disp2.is_complete

    done = False
    while not done:
        print("looping!")

        done = True
        if not disp.is_complete:
            data = disp.poll()
            done = False
            print("disp.is_complete NOT")
        else:
            print("disp.is_complete!")

        if not disp2.is_complete:
            data2 = disp2.poll()
            done = False
            print("disp2.is_complete NOT")
        else:
            print("disp2.is_complete!")

        time.sleep(2)

    validate_data(data, scw_kind)
    validate_data(data2, scw_kind)


@pytest.mark.skip(reason="to fix")
@pytest.mark.parametrize("platform", ["staging-1-3"])
def test_failing(platform):
    from oda_api.api import DispatcherAPI, UserError

    disp = get_disp(wait=True, platform=platform)

    assert disp.wait
    
    with pytest.raises(UserError):
        disp.poll()
    
    disp.get_product(
                instrument="isgri", 
                product="isgri_image", 
                product_type="Real", 
                osa_version="OSA10.2",
                E1_keV=25.0,
                E2_keV=80.0,
                scw_list=pick_scw(kind="failing"),
            )


    done = False
    while not done:
        done = True
        if not disp.is_complete:
            disp.poll()
            done = False

        time.sleep(2)



