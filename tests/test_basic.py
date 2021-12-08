import json
import os
import jwt
import time
import pytest
import re

import requests
import oda_api.api

from cdci_data_analysis.pytest_fixtures import DispatcherJobState, make_hash, ask

secret_key = 'secretkey_test'
default_exp_time = int(time.time()) + 5000
default_token_payload = dict(
    sub="mtm@mtmco.net",
    name="mmeharga",
    roles="general",
    exp=default_exp_time,
    tem=0,
    mstout=True,
    mssub=True
)

@pytest.mark.slow
def test_show_product(dispatcher_live_fixture, capsys):
    with capsys.disabled():
        from oda_api.api import DispatcherAPI

        disp = DispatcherAPI(url=dispatcher_live_fixture, instrument='mock')
        # let's generate a valid token
        token_payload = {
            **default_token_payload,
            "roles": ["general", "integral-private-qla"],
        }
        encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')
        products = disp.get_product(instrument="isgri",
                                    product="isgri_lc",
                                    product_type="Dummy",
                                    osa_version='OSA11.0',
                                    token=encoded_token
                                    )

    products.show()

    captured = capsys.readouterr()
    print("Show() output: ", captured.out)
    assert captured.out == "ID=0 prod_name=isgri_lc_0_OAO1657m415  meta_data: {'src_name': 'OAO 1657-415', 'time_bin': 0.0115739687598762, 'time': 'TIME', 'rate': 'RATE', 'rate_err': 'ERROR'}\n\n"

    assert hasattr(products, "isgri_lc_0_OAO1657m415")
    assert 'isgri_lc_0_OAO1657m415' in products._n_list
    assert len(products._p_list) == 1
    assert products._p_list[0].name == 'isgri_lc'
    meta_data_dic = dict(
        src_name='OAO 1657-415',
        time_bin=0.0115739687598762,
        time='TIME',
        rate='RATE',
        rate_err='ERROR'
    )
    assert products._p_list[0].meta_data == meta_data_dic


def test_oda_api_code(dispatcher_api):
    disp = dispatcher_api

    disp.get_product(
        product_type="Dummy",
        instrument="empty",
        product="dummy"
    )

    job_id = disp.job_id
    session_id = disp.session_id
    scratch_path = f'scratch_sid_{session_id}_jid_{job_id}'
    scratch_path_aliased = f'scratch_sid_{session_id}_jid_{job_id}_aliased'
    assert os.path.exists(scratch_path) or os.path.exists(scratch_path_aliased)

    if os.path.exists(scratch_path):
        f_query_output = open(scratch_path + '/query_output.json')
    else:
        f_query_output = open(scratch_path_aliased + '/query_output.json')

    jdata_output = json.load(f_query_output)

    assert 'prod_dictionary' in jdata_output
    assert 'api_code' in jdata_output['prod_dictionary']
    output_api_code = jdata_output['prod_dictionary']['api_code']

    expected_api_code = f'''from oda_api.api import DispatcherAPI
disp=DispatcherAPI(url='PRODUCTS_URL/dispatch-data', instrument='mock')

par_dict={{
    "DEC": -29.74516667,
    "RA": 265.97845833,
    "T1": "2017-03-06T13:26:48.000",
    "T2": "2017-03-06T15:32:27.000",
    "T_format": "isot",
    "api": "True",
    "instrument": "empty",
    "oda_api_version": "{oda_api.__version__}",
    "off_line": "False",
    "p_list": [],
    "product": "dummy",
    "product_type": "Dummy",
    "src_name": "1E 1740.7-2942"
}}

data_collection = disp.get_product(**par_dict)
'''

    assert output_api_code.replace('PRODUCTS_URL', dispatcher_api.url) == expected_api_code.replace('PRODUCTS_URL', dispatcher_api.url)


@pytest.mark.parametrize("dry_run_value", [True, False, None, 'not_included'])
def test_dry_run_param(dispatcher_api, dry_run_value):
    disp = dispatcher_api

    params_dic = dict(
        product_type="Dummy",
        instrument="empty",
        product="dummy"
    )

    if dry_run_value != 'not_included':
        params_dic['dry_run'] = dry_run_value

    disp.get_product(
        **params_dic
    )

    job_id = disp.job_id
    session_id = disp.session_id
    scratch_path = f'scratch_sid_{session_id}_jid_{job_id}'
    scratch_path_aliased = f'scratch_sid_{session_id}_jid_{job_id}_aliased'
    assert os.path.exists(scratch_path) or os.path.exists(scratch_path_aliased)

    if os.path.exists(scratch_path):
        f_query_output = open(scratch_path + '/query_output.json')
    else:
        f_query_output = open(scratch_path_aliased + '/query_output.json')

    jdata_output = json.load(f_query_output)

    assert 'prod_dictionary' in jdata_output
    assert 'api_code' in jdata_output['prod_dictionary']
    output_api_code = jdata_output['prod_dictionary']['api_code']

    assert 'dry_run' not in output_api_code

    assert 'analysis_parameters' in jdata_output['prod_dictionary']
    assert 'dry_run' not in jdata_output['prod_dictionary']['analysis_parameters']


def test_default_url_init():
    disp = oda_api.api.DispatcherAPI(
        url=None
    )
    assert disp.url == "https://www.astro.unige.ch/mmoda/dispatch-data"


@pytest.mark.parametrize("protocol_url", ['http://', 'https://', ''])
@pytest.mark.parametrize("init_parameter", ['host', 'url'])
@pytest.mark.parametrize("protocol_parameter_value", ['http', 'https', '', None, 'not_included'])
def test_host_url_init(dispatcher_long_living_fixture, protocol_url, init_parameter, protocol_parameter_value):
    from oda_api.api import UserError

    dispatcher_live_fixture_parameter = re.sub(r"https?://", protocol_url, dispatcher_long_living_fixture)

    args_init = {
        init_parameter: dispatcher_live_fixture_parameter,
    }

    if protocol_parameter_value != 'not_included':
        args_init['protocol'] = protocol_parameter_value

    if (init_parameter == 'url' and protocol_url == '') or \
            (init_parameter == 'host' and
             (protocol_parameter_value is None or
              protocol_parameter_value == '') and protocol_url == ''):
        with pytest.raises(UserError):
            oda_api.api.DispatcherAPI(
                **args_init
            )
    else:
        disp = oda_api.api.DispatcherAPI(
            **args_init
        )
        assert disp.url.startswith('http://') or disp.url.startswith('https://')
        assert re.sub(r"https?://?", '', disp.url) == re.sub(r"https?://?", '', dispatcher_long_living_fixture)


def test_progress(dispatcher_live_fixture):
    DispatcherJobState.remove_scratch_folders()

    disp = oda_api.api.DispatcherAPI(url=dispatcher_live_fixture, wait=False)

    disp.get_product(
        product="dummy",
        instrument="empty-async",
    )

    assert disp.query_status == "submitted"

    disp.poll()

    assert disp.query_status == "submitted"

    c = requests.get(dispatcher_live_fixture + "/call_back",
                        params=dict(
                        job_id=disp.job_id,
                        session_id=disp.session_id,
                        instrument_name="empty-async",
                        action='progress',
                        node_id=f'special_node',
                        message='progressing',
                        # token=disp,
                        # time_original_request=time_request
                    ))

    disp_state = DispatcherJobState(session_id=disp.session_id, job_id=disp.job_id)
    assert disp_state.load_job_state_record("special_node", "progressing")['full_report_dict']['action'] == 'progress'

    disp.poll()
    assert disp.query_status == "progress"

    c = requests.get(dispatcher_live_fixture + "/call_back",
                    params=dict(
                    job_id=disp.job_id,
                    session_id=disp.session_id,
                    # instrument_name="empty-async",
                    action='done',
                    node_id=f'node',
                    message='progressing',
                    # token=disp,
                    # time_original_request=time_request
                ))

    disp_state = DispatcherJobState(session_id=disp.session_id, job_id=disp.job_id)
    assert json.load(open(disp_state.job_monitor_json_fn))['full_report_dict']['action'] == 'done'

    disp.poll()
    assert disp.query_status == "ready"


def test_retry(dispatcher_live_fixture, caplog):
    DispatcherJobState.remove_scratch_folders()

    def third_try_get(*args, **kwargs):        
        if 'run_analysis' in args[0] and len(requests.exceptions_to_raise) > 0:
            raise requests.exceptions_to_raise.pop()

        return requests._get(*args, **kwargs)

    requests._get = requests.get
    requests.get = third_try_get
    requests.exceptions_to_raise = [requests.exceptions.Timeout, ConnectionError, oda_api.api.DispatcherNotAvailable]

    disp = oda_api.api.DispatcherAPI(url=dispatcher_live_fixture, wait=False)
    disp.n_max_tries = 4
    disp.retry_sleep_s = 0.1

    disp.get_product(
        product="dummy",
        instrument="empty-async")
    
    for level, message, number in [
        ('DEBUG', '- error on the remote server', 3),
        ('INFO', '- error on the remote server', 0),
        ('WARNING', 'possibly temporary problem in calling server', 3),
    ]:
        assert len([record for record in caplog.records if record.levelname == level and message in record.message]) == number, \
               "lacking message '{}' in: \n{}".format(message, '\n>>>> '.join([record.message for record in caplog.records if record.levelname == level]))
    
    disp.n_max_tries = 1
    requests.exceptions_to_raise = [requests.exceptions.Timeout]
    
    with pytest.raises(oda_api.api.RemoteException):
        disp.get_product(
            product="dummy",
            instrument="empty-async")
    
    requests.get = requests._get

@pytest.mark.parametrize('exception_kind', ['json', 'text'])
def test_dispatcher_exception(dispatcher_live_fixture, caplog, exception_kind):
    from requests.models import Response

    DispatcherJobState.remove_scratch_folders()

    #TODO: the whole HTTP 410 is not relevant, this should be adressed in the dispatcher
    # https://github.com/oda-hub/dispatcher-app/issues/139
 
    def get_exception(*args, **kwargs):                        
        response = Response()
        response.status_code = 500

        if exception_kind == "json":
            response._content = json.dumps({"cdci_data_analysis_version":"1.3.1",
                    "config":{"dispatcher-config":
                        {"cfg_dict":
                            {"dispatcher":
                                {"bind_options":
                                    {"bind_host":"0.0.0.0","bind_port":8000},
                                "dispatcher_callback_url_base":"http://dispatcher.production.iu.odahub.io:31611",
                                "dummy_cache":"dummy-cache",
                                "products_url":"https://frontend-staging.obsuks1.unige.ch/mmoda/"}},
                                "origin":{"filepath":"/dispatcher/conf/conf_env.yml","set_by":"command line /pyenv/versions/3.8.5/lib/python3.8/site-packages/cdci_data_analysis/flask_app/app.py:cdci_data_analysis.flask_app.app"}
                                }},
                    "debug_mode":"no",
                    "error_message":"Expecting value: line 1 column 1 (char 0)",
                    "installed_instruments":["magic","isgri","jemx","polar","antares","spi_acs"],
                    "message":"request not valid",
                    "oda_api_version":"1.1.25"}).encode()
        elif exception_kind == "text":
            response._content = "something's wrong!".encode()
        else:
            RuntimeError()

        return response

    requests._get = requests.get
    requests.get = get_exception
    
    disp = oda_api.api.DispatcherAPI(url=dispatcher_live_fixture, wait=False)

    with pytest.raises(oda_api.api.DispatcherException) as e:
        disp.get_product(
                product="dummy",            
                instrument="empty-async")
    
    if exception_kind == "json":        
        assert repr(e.value) == "[ DispatcherException: Expecting value: line 1 column 1 (char 0) ]"
    elif exception_kind == "text":
        assert repr(e.value) == "[ DispatcherException: something's wrong! ]"
    else:
        raise RuntimeError()
    
    requests.get = requests._get