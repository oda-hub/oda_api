import json
import os


def test_oda_api_code(dispatcher_live_fixture):
    from oda_api.api import DispatcherAPI
    disp = DispatcherAPI(
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
        f_params = open(scratch_path + '/analysis_parameters.json')
    else:
        f_query_output = open(scratch_path_aliased + '/query_output.json')
        f_params = open(scratch_path_aliased + '/analysis_parameters.json')

    jdata_output = json.load(f_query_output)

    assert 'prod_dictionary' in jdata_output
    assert 'api_code' in jdata_output['prod_dictionary']

    output_api_code = jdata_output['prod_dictionary']['api_code']

    param_dic = json.load(f_params)
    # remove non-needed entries
    param_dic.pop('session_id', None)
    param_dic.pop('query_status', None)
    # rename some keys
    _alias_dict = {}
    _alias_dict['product_type'] = 'product'
    _alias_dict['query_type'] = 'product_type'

    _api_dict = {}
    for k in param_dic.keys():
        if k in _alias_dict.keys():
            n = _alias_dict[k]
        else:
            n = k
        _api_dict[n] = param_dic[k]

    expected_api_code = f'''from oda_api.api import DispatcherAPI
disp=DispatcherAPI(url='http://0.0.0.0:8001', instrument='mock', protocol='https')

par_dict={json.dumps(_api_dict, indent=4)}

data_collection = disp.get_product(**par_dict)
'''

    assert output_api_code == expected_api_code
