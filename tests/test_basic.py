import json
import os
import jwt
import time

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


def test_show_product_isgri(dispatcher_long_living_fixture):
    from oda_api.api import DispatcherAPI

    disp = DispatcherAPI(url=dispatcher_long_living_fixture, instrument='mock')
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        "roles": ["general", "integral-private-qla"],
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')
    light_curve = disp.get_product(instrument="isgri",
                                   product="isgri_lc",
                                   product_type="Dummy",
                                   osa_version='OSA11.0',
                                   RA=275.09142677,
                                   DEC=7.18535523,
                                   radius=8,
                                   T1=58193.455,
                                   T2=58246.892,
                                   E1_keV=30,
                                   E2_keV=80,
                                   T_format='mjd',
                                   max_pointings=50,
                                   time_bin=1000,  # time bin in seconds
                                   token=encoded_token,
                                   selected_catalog='{"cat_frame": "fk5", "cat_coord_units": "deg", "cat_column_list": [[0, 1, 2], ["GX 5-1", "MAXI SRC", "H 1820-303"], [96.1907958984375, 74.80066680908203, 66.31670379638672], [270.2771301269531, 270.7560729980469, 275.914794921875], [-25.088342666625977, -29.84027099609375, -30.366628646850586], [0, 1, 0], [0.05000000074505806, 0.05000000074505806, 0.05000000074505806]], "cat_column_names": ["meta_ID", "src_names", "significance", "ra", "dec", "FLAG", "ERR_RAD"], "cat_column_descr": [["meta_ID", "<i8"], ["src_names", "<U10"], ["significance", "<f8"], ["ra", "<f8"], ["dec", "<f8"], ["FLAG", "<i8"], ["ERR_RAD", "<f8"]], "cat_lat_name": "dec", "cat_lon_name": "ra"}')

    light_curve.show()


def test_show_product_jemx(dispatcher_long_living_fixture):
    from oda_api.api import DispatcherAPI
    disp = DispatcherAPI(url=dispatcher_long_living_fixture, instrument='mock')
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        "roles": ["general", "integral-private-qla"],
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')
    par_dict = {
        "src_name": "4U 1700-377",
        "RA": "270.80",
        "DEC": "-29.80",
        "T1": "2021-05-01",
        "T2": "2021-05-05",
        "T_format": "isot",
        "instrument": "jemx",
        "osa_version": "OSA11.0",
        "radius": "4",
        "max_pointings": "50",
        "integral_data_rights": "all-private",
        "jemx_num": "1",
        "E1_keV": "3",
        "E2_keV": "20",
        "product_type": "Real",
        "detection_threshold": "5",
        "product": "jemx_lc",
        "time_bin": "4",
        "time_bin_format": "sec",
        "catalog_selected_objects": "1,2,3",
        "selected_catalog": '{"cat_frame": "fk5", "cat_coord_units": "deg", "cat_column_list": [[0, 1, 2], ["GX 5-1", "MAXI SRC", "H 1820-303"], [96.1907958984375, 74.80066680908203, 66.31670379638672], [270.2771301269531, 270.7560729980469, 275.914794921875], [-25.088342666625977, -29.84027099609375, -30.366628646850586], [0, 1, 0], [0.05000000074505806, 0.05000000074505806, 0.05000000074505806]], "cat_column_names": ["meta_ID", "src_names", "significance", "ra", "dec", "FLAG", "ERR_RAD"], "cat_column_descr": [["meta_ID", "<i8"], ["src_names", "<U10"], ["significance", "<f8"], ["ra", "<f8"], ["dec", "<f8"], ["FLAG", "<i8"], ["ERR_RAD", "<f8"]], "cat_lat_name": "dec", "cat_lon_name": "ra"}',
        "token": encoded_token
    }

    data_collection_lc = disp.get_product(**par_dict)

    data_collection_lc.show()


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
disp=DispatcherAPI(url='http://www.astro.unige.ch/cdci/astrooda_', instrument='mock')

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
