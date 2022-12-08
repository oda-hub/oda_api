import json
import os
import jwt
import time
import pytest
import re
import glob
import requests
import oda_api.api
import oda_api.token

from cdci_data_analysis.pytest_fixtures import DispatcherJobState
from conftest import remove_old_token_files, remove_scratch_folders

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


def test_job_id_data_collection(dispatcher_api):
    disp = dispatcher_api

    prods_first = disp.get_product(
        product_type="Dummy",
        instrument="empty",
        product="dummy",
        p=10
    )

    job_id_first_request = prods_first.request_job_id
    f_query_output = None
    list_scratch_dir = glob.glob( f'scratch_sid_*_jid_{job_id_first_request}')
    if len(list_scratch_dir) >= 1:
        f_query_output = open(os.path.join(list_scratch_dir[0], 'query_output.json'))

    assert f_query_output is not None
    jdata_output = json.load(f_query_output)
    assert jdata_output['prod_dictionary']['job_id'] == job_id_first_request

    prods_second = disp.get_product(
        product_type="Dummy",
        instrument="empty",
        product="dummy",
        p=9
    )

    job_id_second_request = prods_second.request_job_id
    f_query_output = None
    list_scratch_dir = glob.glob(f'scratch_sid_*_jid_{job_id_second_request}')
    if len(list_scratch_dir) >= 1:
        f_query_output = open(os.path.join(list_scratch_dir[0], 'query_output.json'))

    assert f_query_output is not None
    jdata_output = json.load(f_query_output)
    assert jdata_output['prod_dictionary']['job_id'] == job_id_second_request

    assert job_id_second_request != job_id_first_request


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


@pytest.mark.parametrize('token_placement', ['oda_env_var', 'file_home', 'file_cur_dir', 'no'])
@pytest.mark.parametrize('token_write_method', ['oda_env_var', 'file_home', 'file_cur_dir', 'no'])
@pytest.mark.parametrize('write_token', [True, False])
def test_token_refresh(dispatcher_live_fixture, token_placement, monkeypatch, write_token, token_write_method, tmpdir):
    remove_old_token_files()
    remove_scratch_folders()

    disp = oda_api.api.DispatcherAPI(url=dispatcher_live_fixture, wait=False)

    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        "roles": ["general", "refresh-tokens"]
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    # reset any existing token locations
    os.makedirs(tmpdir, exist_ok=True)
    monkeypatch.setenv('HOME', tmpdir)

    oda_token_home_fn = os.path.join(tmpdir, ".oda-token")
    if os.path.exists(oda_token_home_fn):
        os.remove(oda_token_home_fn)

    oda_token_cwd_fn = ".oda-token"
    if os.path.exists(oda_token_cwd_fn):
        os.remove(oda_token_cwd_fn)

    monkeypatch.setenv('ODA_TOKEN', '')

    if token_placement == 'oda_env_var':
        monkeypatch.setenv('ODA_TOKEN', encoded_token)

    elif token_placement == 'file_cur_dir':
        with open(oda_token_cwd_fn, "w") as f:
            f.write(encoded_token)

    elif token_placement == 'file_home':
        with open(oda_token_home_fn, "w") as f:
            f.write(encoded_token)

    token_write_method_enum = None
    if token_write_method != 'no':
        token_write_method_enum = oda_api.token.TokenLocation[str.upper(token_write_method)]

    if token_placement == 'no':
        with pytest.raises(RuntimeError, match="unable to refresh the token with any known method"):
            if token_write_method != 'no':
                disp.refresh_token(write_token=write_token, token_write_methods=token_write_method_enum)
            else:
                disp.refresh_token(write_token=write_token)
    else:
        if token_write_method != 'no':
            refreshed_token = disp.refresh_token(write_token=write_token, token_write_methods=token_write_method_enum)
            discovered_token = oda_api.token.discover_token(allow_invalid=True, token_discovery_methods=token_write_method_enum)
        else:
            refreshed_token = disp.refresh_token(write_token=write_token)
            discovered_token = oda_api.token.discover_token(allow_invalid=True)
        if write_token:
            assert refreshed_token == discovered_token
            list_old_token_files = glob.glob('old-oda-token_*')
            assert len(list_old_token_files) == 1
            assert open(list_old_token_files[0]).read() == encoded_token
        else:
            assert refreshed_token != discovered_token


@pytest.mark.parametrize('tokens_tems', [[100, 100],
                                         [100, 150],
                                         [150, 100]])
@pytest.mark.parametrize('tokens_intsubs', [[100, 100],
                                            [100, 150],
                                            [150, 100]])
@pytest.mark.parametrize('tokens_mstouts', [True, False])
@pytest.mark.parametrize('tokens_mssubs', [True, False])
@pytest.mark.parametrize('tokens_msdones', [True, False])
@pytest.mark.parametrize('tokens_fails', [True, False])
@pytest.mark.parametrize('missing_keys', [True, False])
@pytest.mark.parametrize('extra_keys', [True, False])
@pytest.mark.parametrize('tokens_subs', [['sub1', 'sub1'],
                                         ['sub1', 'sub2'],
                                         ['sub2', 'sub1']])
@pytest.mark.parametrize('tokens_emails', [['email1', 'email1'],
                                           ['email1', 'email2'],
                                           ['email2', 'email1']
                                           ])
@pytest.mark.parametrize('tokens_roles', [[[], ['role1', 'role2']],
                                          [['role1', 'role2'], []],
                                          [['role1', 'role2'], ['role1', 'role2']],
                                          [['role1', 'role2'], ['role1', 'role3', 'role4']],
                                          [['role1', 'role2'], ['role1', 'role2', 'role3']],
                                          [['role1', 'role2', 'role3'], ['role1', 'role2']],
                                          [[], []]
                                          ])
@pytest.mark.parametrize('tokens_exps', [[100, 100],
                                         [100, 150],
                                         [150, 100]
                                         ])
def test_compare_token(tokens_tems, tokens_intsubs, tokens_mstouts, tokens_mssubs, tokens_msdones, tokens_fails,
                       missing_keys, extra_keys, tokens_subs, tokens_emails, tokens_roles, tokens_exps):
    from oda_api.token import token_email_options_numeric, token_email_options_flags

    token1_payload = {
        "sub": tokens_subs[0],
        "email": tokens_emails[0],
        "exp": tokens_exps[0],
        "roles": tokens_roles[0],
        # email options
        "tem": tokens_tems[0],
        "intsub": tokens_intsubs[0],
        "mssub": tokens_mssubs,
        "msdone": tokens_msdones,
        "mstout": tokens_mstouts,
        "msfail": tokens_fails
    }

    token2_payload = {
        'sub': tokens_subs[1],
        'email': tokens_emails[1],
        'exp': tokens_exps[1],
        'roles': tokens_roles[1],
        # email options
        "tem": tokens_tems[1],
        "intsub": tokens_intsubs[1],
        "mssub": tokens_mssubs,
        "msdone": tokens_msdones,
        "mstout": tokens_mstouts,
        "msfail": tokens_fails
    }

    if missing_keys:
        token1_payload.pop('sub')

    if extra_keys:
        token1_payload['extra_key'] = 'test'

    comparison_result = oda_api.token.compare_token(token1_payload, token2_payload)

    assert 'missing_keys' in comparison_result
    if missing_keys:
        assert comparison_result['missing_keys'] == ['sub']
    else:
        assert comparison_result['missing_keys'] == []

    assert 'extra_keys' in comparison_result
    if extra_keys:
        assert comparison_result['extra_keys'] == ['extra_key']
    else:
        assert comparison_result['extra_keys'] == []

    assert 'exp' in comparison_result
    if tokens_exps[0] > tokens_exps[1]:
        assert comparison_result['exp'] == 1
    elif tokens_exps[0] < tokens_exps[1]:
        assert comparison_result['exp'] == -1
    elif tokens_exps[0] == tokens_exps[1]:
        assert comparison_result['exp'] == 0

    assert 'roles' in comparison_result
    token1_roles_difference = set(token1_payload["roles"]) - set(token2_payload["roles"])
    token2_roles_difference = set(token2_payload["roles"]) - set(token1_payload["roles"])
    if token1_roles_difference != set() and token2_roles_difference == set():
        assert comparison_result["roles"] == 1
    elif len(token1_roles_difference) < len(token2_roles_difference) or \
            (len(token1_roles_difference) >= len(token2_roles_difference) and token2_roles_difference != set()):
        assert comparison_result["roles"] == -1
    elif len(token1_roles_difference) == len(token2_roles_difference) and \
            token1_roles_difference == set() and token2_roles_difference == set():
        assert comparison_result["roles"] == 0

    if not missing_keys:
        assert 'sub' in comparison_result
        if tokens_subs[0] == tokens_subs[1]:
            assert comparison_result['sub']
        else:
            assert not comparison_result['sub']
    else:
        assert 'sub' not in comparison_result

    assert 'email' in comparison_result
    if tokens_emails[0] == tokens_emails[1]:
        assert comparison_result['email']
    else:
        assert not comparison_result['email']

    # check email options
    for opt in token_email_options_numeric:
        assert opt in comparison_result
        if token1_payload[opt] > token2_payload[opt]:
            assert comparison_result[opt] == 1
        elif token1_payload[opt] < token2_payload[opt]:
            assert comparison_result[opt] == -1
        else:
            assert comparison_result[opt] == 0

    for opt in token_email_options_flags:
        assert opt in comparison_result
        if token1_payload[opt] == token2_payload[opt]:
            assert comparison_result[opt]
        else:
            assert not comparison_result[opt]

def test_comment(dispatcher_api, capsys):
    disp = dispatcher_api
    
    disp.get_product(
        instrument = 'empty',
        product = 'dummy',
        unkpar = 'foo', 
        product_type='Dummy'
    )
    
    captured = capsys.readouterr()
    
    assert re.search(r'Please note that arguments?.*unkpar.*not used', captured.out)
