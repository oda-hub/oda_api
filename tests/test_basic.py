import json
import os
import jwt
import time
import pytest

import oda_api.api


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

    assert output_api_code == expected_api_code or output_api_code == expected_api_code.replace('PRODUCTS_URL', 'http://0.0.0.0:8001')
