import jwt
import time
import random
import requests
import pytest
import logging
import contextlib

from oda_api.api import DispatcherAPI, Unauthorized


# this can be set by pytest ... --log-cli-level DEBUG
logging.getLogger('oda_api').setLevel(logging.DEBUG)
logging.getLogger('oda_api').addHandler(logging.StreamHandler())


secret_key = 'secretkey_test'

default_exp_time = int(time.time()) + 5000
default_token_payload = dict(
    sub="mtm@mtmco.net",
    name="mmeharga",
    roles="general",
    exp=default_exp_time,
    tem=0,
    mstout=True,
    mssub=True,
    intsub=5
)



def get_platform_dispatcher(platform="production-1-2"):
    import odakb.sparql as S

    R = S.select('?p a oda:platform; oda:location ?loc . ?p ?x ?y',
                 '?p ?x ?y', tojdict=True)

    try:
        locations = R["oda:"+platform]["oda:location"]
    except:
        return platform

    try:
        return list(locations.keys())[0]
    except:
        return list(locations)[0]


def pick_scw(kind="any"):
    if kind == "crab":
        return "066500220010.001"
    elif kind == "any":
        scwlist = requests.get("https://www.astro.unige.ch/mmoda/dispatch-data/"
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

        t = cat[cat['src_names'] == source]
        print(t)

        assert len(t) == 1


def test_instruments():
    from oda_api.api import DispatcherAPI
    disp = DispatcherAPI(
        host=get_platform_dispatcher(),
        instrument="mock",
    )
    assert {'isgri', 'jemx', 'polar', 'antares', 'gw', 'spi_acs', 'legacysurvey'} - set(disp.get_instruments_list()) == set()


def test_instrument_description_not_null():
    from oda_api.api import DispatcherAPI
    disp = DispatcherAPI(
        host=get_platform_dispatcher(),
        instrument="mock",
    )
    assert disp.get_instrument_description('isgri') is not None


def test_product_description_not_null():
    from oda_api.api import DispatcherAPI
    disp = DispatcherAPI(
        host=get_platform_dispatcher(),
        instrument="mock",
    )
    assert disp.get_product_description('isgri', 'isgri_image') is not None


@contextlib.contextmanager
def raises_if_failing(scw_kind, exception):
    if scw_kind == "failing":
        try:
            print("\033[31mthis should raise", exception, "\033[0m")
            with pytest.raises(exception):
                yield
        except Exception as e:
            print("this raised something else", e)
            raise
    else:
        yield


@pytest.mark.slow
@pytest.mark.parametrize("platform", ["staging", "staging-1-2", "production-1-2"])
@pytest.mark.parametrize("scw_kind", ["crab", "any", "failing"])
def test_waiting(scw_kind, platform):
    from oda_api.api import UserError, FailedToFindAnyUsefulResults

    disp = get_disp(wait=True, platform=platform)

    with pytest.raises(UserError):
        disp.poll()

    assert disp.wait

    with raises_if_failing(scw_kind, FailedToFindAnyUsefulResults):
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




def test_unauthorized(dispatcher_api):
    from oda_api.api import UserError

    disp = dispatcher_api
    disp.wait=True

    with pytest.raises(UserError):
        disp.poll()

    assert disp.wait

    try:        
        data = disp.get_product(
                instrument="empty",
                product="numerical",
                product_type="Dummy",
                T1="2011-11-11T11:11:11",
                T2="2011-11-11T11:11:11",
                max_pointings=1000,
            )

        raise RuntimeError('did not raise Unauthorized for expired token')
    except Unauthorized as e:
        assert e.message == "Unfortunately, your priviledges are not sufficient to make the request for this particular product and parameter combination.\n"\
                            "- Your priviledge roles include []\n"\
                            "- You are lacking all of the following roles:\n"\
                            " - general: please refer to support for details\n"\
                            "You can request support if you think you should be able to make this request."
    

def test_token_expired(dispatcher_live_fixture):
    from oda_api.api import UserError

    disp = get_disp(wait=True, platform=dispatcher_live_fixture)

    with pytest.raises(UserError):
        disp.poll()

    assert disp.wait

    token_payload = {
                        **default_token_payload,
                        'exp': int(time.time()) - 10,
                    }   

    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    if isinstance(encoded_token, bytes):
        encoded_token = encoded_token.decode()

    try:        
        data = disp.get_product(
                instrument="empty",
                product="dummy",
                product_type="Dummy",
                T1=25.0,
                T2=80.0,
                token=encoded_token
            )

        raise RuntimeError('did not raise Unauthorized for expired token')
    except Unauthorized as e:
        assert e.message == "RequestNotAuthorized():The token provided is expired, please try to logout and login again. If already logged out, please clean the cookies, and resubmit you request."


@pytest.mark.slow
@pytest.mark.parametrize("platform", ["staging", "staging-1-2", "production-1-2"])
@pytest.mark.parametrize("scw_kind", ["crab", "any", "failing"])
def test_not_waiting(scw_kind, platform):
    from oda_api.api import DispatcherAPI, UserError, FailedToFindAnyUsefulResults

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

    with raises_if_failing(scw_kind, FailedToFindAnyUsefulResults):
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


@pytest.mark.slow
@pytest.mark.parametrize("platform", ["staging", "staging-1-2", "production-1-2"])
def test_large_request(platform):

    dummy_request_parameters = dict(
        instrument="isgri",
        product="isgri_image",
        product_type="Dummy",
        osa_version="OSA10.2",
        E1_keV=40.0,
        E2_keV=200.0,
        scw_list="066500550010.001"*300,
        # this needs role
        #scw_list=[f"0665{i:04d}0010.001" for i in range(200)],
    )


    disp = get_disp(wait=True, platform=platform)

    'isgri' in disp.get_instruments_list()

    assert disp.preferred_request_method == "GET"
    assert disp.selected_request_method == "GET"

    product = disp.get_product(
        **dummy_request_parameters
    )
    disp.returned_analysis_parameters_consistency()

    assert disp.preferred_request_method == "GET"
    assert disp.selected_request_method == "POST"

    product = disp.get_product(
        **{            
            **dummy_request_parameters,
            'scw_list': "066500550010.001"
        }
    )
    disp.returned_analysis_parameters_consistency()

    assert disp.preferred_request_method == "GET"
    assert disp.selected_request_method == "GET"


@pytest.mark.slow
@pytest.mark.parametrize("platform", ["staging", "staging-1-2", "production-1-2"])
def test_peculiar_request_causing_pickling_problem(platform):
    import logging
    logging.basicConfig(level='DEBUG')
    logging.getLogger('oda_api').setLevel('DEBUG')
    logging.getLogger('oda_api.api').setLevel('DEBUG')


    import oda_api.api
    disp = oda_api.api.DispatcherAPI(url="http://dispatcher.staging.internal.odahub.io")
    print(disp.get_instruments_list())

    disp.get_product(
        'isgri_image',
        scw_list='193200210010.001,193300510010.001,193400100010.001,193600090010.001,193600150010.001,193800020010.001,193900120010.001,193900160010.001,194000130010.001,194100100010.001,194100130010.001,194300090010.001,194400490010.001,194500020010.001,194500100010.001,194800270010.001,194800310010.001,194900080010.001,194900110010.001,195000330010.001',
        E1_keV='28.0',
        E2_keV='80.0',
        osa_version='OSA11.0',
        RA='275.0914266666666',
        DEC='7.185355',
        detection_threshold=7.0,
        instrument='isgri',
        query_type='Real',
        session_id='EV49GW1UN9427QD9',
     )


@pytest.mark.slow
@pytest.mark.parametrize("platform", ["staging"])
def test_bad_request(platform):
    from oda_api.api import RequestNotUnderstood

    disp = get_disp(wait=True, platform=platform)
    assert disp.wait

    with pytest.raises(RequestNotUnderstood):
        data = disp.get_product(
                instrument="isgri_with_typo",
                product="isgri_image_with_typo",
                product_type="Real",
                osa_version="OSA10.2",
                E1_keV=25.0,
                E2_keV=80.0,
                max_pointings=1000,
            )


def test_reusing_disp_instance(dispatcher_api):

    disp = dispatcher_api
    disp.wait = True

    assert disp.job_id is None
    assert disp.query_status == 'not-prepared'

    data = disp.get_product(
            instrument="empty",
            product="dummy",
            product_type="Dummy",
            T1="2021-05-01T11:11:11",
            T2="2021-05-02T11:11:11",
        )

    assert disp.job_id is not None
    assert disp.query_status == 'done'

    previous_job_id =  disp.job_id

    data = disp.get_product(
            instrument="empty",
            product="dummy",
            product_type="Dummy",
            T1="2021-05-01T11:11:11",
            T2="2021-05-02T11:11:11",
        )

    assert disp.job_id is not None
    assert disp.query_status == 'done'
    assert disp.query_status == 'done'

    # identical request results in the same job id
    assert previous_job_id == disp.job_id

    previous_job_id =  disp.job_id

    data = disp.get_product(
            instrument="empty",
            product="dummy",
            product_type="Dummy",
            T1="2021-05-01T11:11:11",
            T2="2021-05-03T11:11:11",
        )

    assert disp.job_id is not None
    assert disp.query_status is not None

    # different request results in different job id
    assert previous_job_id != disp.job_id

