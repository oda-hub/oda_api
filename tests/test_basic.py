import json
import os


def test_oda_api_code(dispatcher_live_fixture):
    import oda_api.api
    disp = oda_api.api.DispatcherAPI(
        url=dispatcher_live_fixture
    )

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
disp=DispatcherAPI(url='http://0.0.0.0:8001', instrument='mock')

par_dict={{
    "instrument": "empty",
    "product": "dummy",
    "product_type": "Dummy",
    "off_line": "False",
    "dry_run": "False",
    "api": "True",
    "oda_api_version": "{oda_api.__version__}"
}}

data_collection = disp.get_product(**par_dict)
'''

    assert output_api_code == expected_api_code
