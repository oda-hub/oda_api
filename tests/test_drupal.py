import pytest
import time
import jwt
import os
import requests
import random
import string
import urllib.parse
import uuid

from dateutil import parser
from datetime import datetime

import oda_api
import oda_api.api
import oda_api.gallery_api
from cdci_data_analysis.analysis.drupal_helper import get_observations_for_time_range, get_user_id, generate_gallery_jwt_token
from test_basic import  default_token_payload, secret_key


@pytest.mark.test_drupal
@pytest.mark.parametrize("observation", [None])
@pytest.mark.parametrize("type_source", ["known", "new", None])
@pytest.mark.parametrize("insert_new_source", [True, False])
@pytest.mark.parametrize("force_insert_not_valid_new_source", [True, False])
@pytest.mark.parametrize("validate_source", [True, False])
@pytest.mark.parametrize("apply_fields_source_resolution", [True, False])
def test_image_product_gallery(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, observation, type_source, insert_new_source, force_insert_not_valid_new_source, validate_source, apply_fields_source_resolution):
    import oda_api.plot_tools as pt

    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    source_name = None
    if type_source == "known":
        source_name = "Crab"
    elif type_source == "new":
        source_name = "new_source_" + ''.join(random.choices(string.digits + string.ascii_lowercase, k=5))

    product_name = "isgri_image"
    instrument = "isgri"

    par_dict = {
        "DEC": -24.7456,
        "E1_keV": 28,
        "E2_keV": 50,
        "RA": 263.0090,
        "T1": '1978-01-01T00:00:00',
        "T2": '1981-05-31T23:59:59',
        "radius": 8,
        "src_name": source_name,
        "max_pointings": 10,
        "detection_threshold": "7.0",
        "instrument": instrument,
        "integral_data_rights": "public",
        "off_line": "False",
        "product": product_name,
        "product_type": "Dummy",
        'token': encoded_token
    }

    disp = dispatcher_api_with_gallery

    isgri_image = disp.get_product(**par_dict)

    image_product = pt.OdaImage(isgri_image)
    gallery_image = image_product.get_image_for_gallery()
    fits_file = image_product.write_fits()

    e1_kev = 45
    e2_kev = 95

    dec = 19
    ra = 458

    instrument = 'isgri'
    product_type = "isgri_image"

    product_title = "_".join(
        [instrument, product_type, datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")])

    res = disp.post_data_product_to_gallery(
        product_title=product_title,
        instrument=instrument,
        src_name=source_name,
        insert_new_source=insert_new_source,
        force_insert_not_valid_new_source=force_insert_not_valid_new_source,
        apply_fields_source_resolution=apply_fields_source_resolution,
        validate_source=validate_source,
        gallery_image_path=gallery_image,
        fits_file_path=fits_file,
        observation_id=observation,
        token=encoded_token,
        e1_kev=e1_kev, e2_kev=e2_kev,
        DEC=dec, RA=ra
        )

    if type_source == 'known' and validate_source and apply_fields_source_resolution:
        ra = 83.63
        dec = 22.01

    assert 'title' in res
    assert res['title'][0]['value'] == product_title

    assert 'field_e1_kev' in res
    assert res['field_e1_kev'][0]['value'] == e1_kev

    assert 'field_e2_kev' in res
    assert res['field_e2_kev'][0]['value'] == e2_kev

    assert 'field_dec' in res
    assert round(res['field_dec'][0]['value'], 2) == dec

    assert 'field_ra' in res
    assert round(res['field_ra'][0]['value'], 2) == ra

    link_astrophysical_entity = os.path.join(
        dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
        'rest/relation/node/data_product/field_describes_astro_entity')
    if type_source == 'known' or \
            (type_source == 'new' and (
                    insert_new_source and (force_insert_not_valid_new_source or not validate_source)
            )):
        assert link_astrophysical_entity in res['_links']
        assert len(res['_links'][link_astrophysical_entity]) == len(source_name.split(','))
    else:
        assert link_astrophysical_entity not in res['_links']


@pytest.mark.test_drupal
@pytest.mark.parametrize("observation", ['test observation', None])
@pytest.mark.parametrize("provide_job_id", [True, False])
@pytest.mark.parametrize("provide_session_id", [True, False])
@pytest.mark.parametrize("provide_instrument", [True, False])
@pytest.mark.parametrize("provide_product_type", [True, False])
def test_light_curve_product_gallery(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, observation, provide_job_id, provide_session_id, provide_instrument, provide_product_type):
    import oda_api.plot_tools as pt

    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    source_name = 'OAO 1657-415'
    product_name = "isgri_lc"
    par_dict = {
        "DEC": -24.7456,
        "E1_keV": 28,
        "E2_keV": 50,
        "RA": 263.0090,
        "T1": '2019-01-01T00:00:00',
        "T2": '2019-03-31T23:59:59',
        "radius": 8,
        "src_name": source_name,
        "max_pointings": 10,
        "detection_threshold": "7.0",
        "instrument": "isgri",
        "integral_data_rights": "public",
        "off_line": "False",
        "product": product_name,
        "product_type": "Dummy",
    }

    disp = dispatcher_api_with_gallery

    isgri_lc = disp.get_product(**par_dict)

    light_curve_product = pt.OdaLightCurve(isgri_lc)
    gallery_image = light_curve_product.get_image_for_gallery()
    fits_file_1 = light_curve_product.write_fits(source_name)[0]
    # just some dummy fits file, to test multiple fits file upload
    fits_file_2 = 'data/dummy_prods/query_catalog.fits'

    notebook_link = 'http://test.test/notebook.ipynb'

    e1_kev = 45
    e2_kev = 95

    dec = 19
    ra = 458

    if not provide_job_id:
        job_id = None
    else:
        job_id = disp.job_id
    if not provide_session_id:
        session_id = None
    else:
        session_id = disp.session_id
    if not provide_instrument:
        instrument = None
    else:
        # a difference value
        instrument = 'jemx'
    if not provide_product_type:
        product_type = None
    else:
        product_type = 'jemx_lc'

    additional_html_to_render = '''<table class="table table-responsive">
        <thead class="table-dark">
            <tr>
                <th>Name</th>
                <th>RA</th>
                <th>Dec</th>
                <th>Flux (cts/s)</th>
                <th>Error (cts/s)</th>
                <th>Significance</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Cyg X-1</td>
                <td>299.5855</td>
                <td>35.20497</td>
                <td>75.069</td>
                <td>0.086</td>
                <td>874.6</td>
            </tr>
        </tbody>
    </table>
    '''

    res = disp.post_data_product_to_gallery(product_title=source_name,
                                            gallery_image_path=gallery_image,
                                            fits_file_path=[fits_file_1, fits_file_2],
                                            observation_id=observation,
                                            token=encoded_token,
                                            produced_by=notebook_link,
                                            job_id=job_id,
                                            e1_kev=e1_kev, e2_kev=e2_kev,
                                            instrument=instrument,
                                            product_type=product_type,
                                            src_name=source_name,
                                            DEC=dec, RA=ra,
                                            html_image=additional_html_to_render)

    assert 'title' in res
    assert res['title'][0]['value'] == source_name

    assert 'field_e1_kev' in res
    assert res['field_e1_kev'][0]['value'] == e1_kev

    assert 'field_e2_kev' in res
    assert res['field_e2_kev'][0]['value'] == e2_kev

    assert 'field_dec' in res
    assert res['field_dec'][0]['value'] == dec

    assert 'field_ra' in res
    assert res['field_ra'][0]['value'] == ra

    assert 'field_produced_by' in res
    assert res['field_produced_by'][0]['value'] == notebook_link

    if provide_instrument or (provide_job_id and provide_session_id):
        link_field_instrumentused = os.path.join(dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
                                                 'rest/relation/node/data_product/field_instrumentused')
        assert link_field_instrumentused in res['_links']

    if provide_product_type or (provide_job_id and provide_session_id):
        link_field_data_product_type = os.path.join(dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
                                                 'rest/relation/node/data_product/field_data_product_type')
        assert link_field_data_product_type in res['_links']


@pytest.mark.test_drupal
# @pytest.mark.parametrize("observation", ['test observation', None])
@pytest.mark.parametrize("observation", [None])
@pytest.mark.parametrize("force_insert_not_valid_new_sources", [True, False])
@pytest.mark.parametrize("source_names", ['GX 1+4', 'GX 1+4, Crab, unknown_src, unknown_src_no_link', ['GX 1+4', 'Crab', 'unknown_src', 'unknown_src_no_link'], None])
def test_spectrum_product_gallery(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, observation, source_names, force_insert_not_valid_new_sources):
    import oda_api.plot_tools as pt

    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    source_name = "GX 1+4"
    product_title = source_name
    par_dict = {
        "DEC": -24.7456,
        "E1_keV": 28,
        "E2_keV": 50,
        "RA": 263.0090,
        "T1": '2012-07-03T00:00:00',
        "T2": '2014-04-03T17:59:59',
        "radius": 8,
        "src_name": source_name,
        "max_pointings": 10,
        "detection_threshold": "7.0",
        "instrument": "isgri",
        "integral_data_rights": "public",
        "off_line": "False",
        "product": "isgri_spectrum",
        "product_type": "Dummy",
    }

    disp = dispatcher_api_with_gallery

    isgri_spec = disp.get_product(**par_dict)

    light_curve_product = pt.OdaSpectrum(isgri_spec)
    gallery_image = light_curve_product.get_image_for_gallery(in_source_name=source_name, xlim=[20, 100])

    e1_kev = 45
    e2_kev = 95

    dec = 19
    ra = 458

    res = disp.post_data_product_to_gallery(product_title=source_name,
                                            gallery_image_path=gallery_image,
                                            obsid='19200050089',
                                            T1='2022-09-19T12:01:55',
                                            T2='2022-09-19T21:36:40',
                                            src_name=source_names,
                                            validate_source=True,
                                            force_insert_not_valid_new_source=force_insert_not_valid_new_sources,
                                            insert_new_source=True,
                                            token=encoded_token,
                                            e1_kev=e1_kev, e2_kev=e2_kev,
                                            DEC=dec, RA=ra)

    assert 'title' in res
    assert res['title'][0]['value'] == product_title

    assert 'field_e1_kev' in res
    assert res['field_e1_kev'][0]['value'] == e1_kev

    assert 'field_e2_kev' in res
    assert res['field_e2_kev'][0]['value'] == e2_kev

    assert 'field_dec' in res
    assert 'field_ra' in res

    link_astrophysical_entity = os.path.join(
        dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
        'rest/relation/node/data_product/field_describes_astro_entity')
    if source_names is not None:
        assert link_astrophysical_entity in res['_links']
        if isinstance(source_names, str):
            source_names_list = source_names.split(',')
        else:
            source_names_list = source_names
        if not force_insert_not_valid_new_sources:
            valid_source_names_list = []
            for src_name_test in source_names_list:
                resolved_obj = disp.resolve_source(src_name_test, encoded_token)
                if 'could not be resolved' not in resolved_obj['message']:
                    valid_source_names_list.append(src_name_test)
            assert len(res['_links'][link_astrophysical_entity]) == len(valid_source_names_list)
        else:
            assert len(res['_links'][link_astrophysical_entity]) == len(source_names_list)
    else:
        assert link_astrophysical_entity not in res['_links']


@pytest.mark.test_drupal
def test_get_attachments_observation_product_gallery(dispatcher_api_with_gallery):
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    disp = dispatcher_api_with_gallery

    observation_title = "test with attachments"
    yaml_file_path = ["observation_yaml_dummy_files/obs_rev_2.yaml"]
    params = dict(
        observation_title=observation_title,
        T1=59242.156853982, T2=59243.156853982,
        observation_time_format="MJD",
        yaml_file_path=yaml_file_path,
        create_new=True,
        token=encoded_token
    )
    disp.update_observation_with_title(**params)

    output_get = disp.get_yaml_files_observation_with_title(observation_title=observation_title,
                                                            token=encoded_token)
    assert 'file_path' in output_get
    assert 'file_content' in output_get

    with open('observation_yaml_dummy_files/obs_rev_2.yaml', 'r') as f_yaml_file:
        yaml_file_content = f_yaml_file.read()

    assert yaml_file_content.strip() in output_get['file_content']

    # yaml_parsed = yaml.load(output_get['file_content'], Loader=yaml.FullLoader)
    # yaml_file_content_parsed = yaml.load(yaml_file_content, Loader=yaml.FullLoader)

    # assert yaml_parsed[0] == yaml_file_content_parsed


@pytest.mark.test_drupal
@pytest.mark.parametrize("auto_update", [True, False])
def test_update_update_source_with_title(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, auto_update):
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    user_id_product_creator = get_user_id(
        product_gallery_url=dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
        user_email=token_payload['sub'])

    disp = dispatcher_api_with_gallery

    params = {
        'source_name': 'GX 1+4',
        'token': encoded_token,
        'auto_update': auto_update,
        'source_dec': -24.9,
    }
    res = disp.update_source_with_name(**params)

    if auto_update:
        assert 'field_source_name' in res
        assert res['field_source_dec'][0]['value'] != params['source_dec']
        assert 'field_source_ra' in res
        assert 'field_alternative_names_long_str' in res
        assert 'field_link' in res
        assert 'field_object_type' in res
    else:
        assert res['field_source_dec'][0]['value'] == params['source_dec']


@pytest.mark.test_drupal
@pytest.mark.parametrize("obsid", [1960001, ["1960001", "1960002", "1960003"], [1960001, 1960002, 1960003]])
@pytest.mark.parametrize("yaml_files", [None, "single", "list"])
@pytest.mark.parametrize("observation_time_format", [None, "ISOT", "MJD", "no_value"])
@pytest.mark.parametrize("t_values_format", ["mjd", "ISOT"])
@pytest.mark.parametrize("force_creation_new", [True, False])
def test_update_observation_product_gallery(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, t_values_format, obsid, yaml_files, observation_time_format, force_creation_new):
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    user_id_product_creator = get_user_id(product_gallery_url=dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
                                          user_email=token_payload['sub'])
    gallery_jwt_token = generate_gallery_jwt_token(dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_secret_key'],
                                                   user_id=user_id_product_creator)

    disp = dispatcher_api_with_gallery

    if t_values_format == "mjd":
        t_values = [59242.156853982, 59243.156853982]
    else:
        t_values = ['2021-01-28T03:44:43', '2021-01-29T03:44:43']

    yaml_file_path = None
    if yaml_files == "single":
        yaml_file_path = "observation_yaml_dummy_files/obs_rev_1.yaml"
    elif yaml_files == "list":
        yaml_file_path = ["observation_yaml_dummy_files/obs_rev_1.yaml", "observation_yaml_dummy_files/obs_rev_2.yaml"]

    observation_title = "test observation"

    params = dict(
        observation_title=observation_title,
        T1=t_values[0], T2=t_values[1],
        observation_time_format=observation_time_format,
        yaml_file_path=yaml_file_path,
        obsid=obsid,
        create_new=force_creation_new,
        token=encoded_token
    )

    if observation_time_format == "no_value":
        params.pop("observation_time_format")

    if ((t_values_format == "mjd") and
        (observation_time_format == "ISOT" or observation_time_format is None or observation_time_format == "no_value")) or \
        ((t_values_format == "ISOT") and observation_time_format == "MJD"):
        with pytest.raises(oda_api.api.UserError):
            disp.update_observation_with_title(**params)
    else:
        res = disp.update_observation_with_title(**params)

        assert 'title' in res
        assert res['title'][0]['value'] == observation_title

        assert 'field_rev1' in res
        assert 'field_rev2' in res

        assert 'field_obsid' in res
        if isinstance(obsid, list):
            for single_obsid in obsid:
                assert res['field_obsid'][obsid.index(single_obsid)]['value'] == str(single_obsid)
        else:
            assert res['field_obsid'][0]['value'] == str(obsid)

        # additional check for the time range REST call
        observations_range = get_observations_for_time_range(
            dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
            gallery_jwt_token, t1='2021-01-28T03:44:43', t2='2021-01-29T03:44:43')
        times = observations_range[0]['field_timerange'].split('--')
        t_start = parser.parse(times[0]).strftime('%Y-%m-%dT%H:%M:%S')
        t_end = parser.parse(times[1]).strftime('%Y-%m-%dT%H:%M:%S')
        assert t_start == '2021-01-28T03:44:43'
        assert t_end == '2021-01-29T03:44:43'

        if yaml_files is not None:
            link_field_field_attachments = os.path.join(
                dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
                'rest/relation/node/observation/field_attachments')
            assert link_field_field_attachments in res['_links']
            if yaml_files == "list":
                assert len(res['_links'][link_field_field_attachments]) == len(yaml_file_path)
            else:
                assert len(res['_links'][link_field_field_attachments]) == 1


@pytest.mark.test_drupal
@pytest.mark.parametrize("obsid", [1960001, ["1960001", "1960002", "1960003"], [1960001, 1960002, 1960003]])
@pytest.mark.parametrize("yaml_files", [None, "single"])
@pytest.mark.parametrize("observation_time_format", [None, "ISOT", "MJD", "no_value"])
@pytest.mark.parametrize("t_values_format", ["mjd", "ISOT"])
def test_post_new_observation_product_gallery(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, t_values_format, obsid, yaml_files, observation_time_format):
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    user_id_product_creator = get_user_id(product_gallery_url=dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
                                          user_email=token_payload['sub'])
    gallery_jwt_token = generate_gallery_jwt_token(dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_secret_key'],
                                                   user_id=user_id_product_creator)

    disp = dispatcher_api_with_gallery

    if t_values_format == "mjd":
        t_values = [59242.156853982, 59243.156853982]
    else:
        t_values = ['2021-01-28T03:44:43', '2021-01-29T03:44:43']

    yaml_file_path = None
    if yaml_files == "single":
        yaml_file_path = "observation_yaml_dummy_files/obs_rev_1.yaml"

    observation_title = "test posting observation from oda_api"

    params = dict(
        observation_title=observation_title,
        T1=t_values[0], T2=t_values[1],
        observation_time_format=observation_time_format,
        yaml_file_path=yaml_file_path,
        obsid=obsid,
        token=encoded_token
    )

    if observation_time_format == "no_value":
        params.pop("observation_time_format")

    if ((t_values_format == "mjd") and
        (observation_time_format == "ISOT" or observation_time_format is None or observation_time_format == "no_value")) or \
        ((t_values_format == "ISOT") and observation_time_format == "MJD"):
        with pytest.raises(oda_api.api.UserError):
            disp.post_observation_to_gallery(**params)
    else:
        res = disp.post_observation_to_gallery(**params)

        assert 'title' in res
        assert res['title'][0]['value'] == observation_title

        assert 'field_rev1' in res
        assert 'field_rev2' in res

        assert 'field_obsid' in res
        if isinstance(obsid, list):
            for single_obsid in obsid:
                assert res['field_obsid'][obsid.index(single_obsid)]['value'] == str(single_obsid)
        else:
            assert res['field_obsid'][0]['value'] == str(obsid)

        # additional check for the time range REST call
        observations_range = get_observations_for_time_range(
            dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
            gallery_jwt_token, t1='2021-01-28T03:44:43', t2='2021-01-29T03:44:43')
        times = observations_range[0]['field_timerange'].split('--')
        t_start = parser.parse(times[0]).strftime('%Y-%m-%dT%H:%M:%S')
        t_end = parser.parse(times[1]).strftime('%Y-%m-%dT%H:%M:%S')
        assert t_start == '2021-01-28T03:44:43'
        assert t_end == '2021-01-29T03:44:43'

        if yaml_files is not None:
            link_field_field_attachments = os.path.join(
                dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
                'rest/relation/node/observation/field_attachments')
            assert link_field_field_attachments in res['_links']
            if yaml_files == "list":
                assert len(res['_links'][link_field_field_attachments]) == len(yaml_file_path)
            else:
                assert len(res['_links'][link_field_field_attachments]) == 1


@pytest.mark.test_drupal
@pytest.mark.parametrize("t_values", [[59242.156853982, 59243.156853982],
                                      ['59242.156853982', '59243.156853982'],
                                      ['2021-01-28T03:44:43', '2021-01-29T03:44:43']])
def test_time_mjd_format_product_gallery(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, t_values):
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    user_id_product_creator = get_user_id(product_gallery_url=dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
                                          user_email=token_payload['sub'])
    gallery_jwt_token = generate_gallery_jwt_token(dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_secret_key'],
                                                   user_id=user_id_product_creator)

    disp = dispatcher_api_with_gallery

    utc_format = False
    try:
        float(t_values[0])
    except ValueError:
        utc_format = True

    t1_mjd = t_values[0] # 2021-01-28T03:44:43
    t2_mjd = t_values[1] # 2021-01-29T03:44:43

    res = disp.post_data_product_to_gallery(token=encoded_token, T1=t1_mjd, T2=t2_mjd)

    if not utc_format:
        t1_utc = disp.convert_mjd_to_utc(float(t1_mjd))
        t2_utc = disp.convert_mjd_to_utc(float(t2_mjd))

        assert parser.parse(t1_utc).strftime('%Y-%m-%dT%H:%M:%S') == '2021-01-28T03:44:43'
        assert parser.parse(t2_utc).strftime('%Y-%m-%dT%H:%M:%S') == '2021-01-29T03:44:43'

    link_field_derived_from_observation = os.path.join(
        dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
        'rest/relation/node/data_product/field_derived_from_observation')
    assert link_field_derived_from_observation in res['_links']

    # additional check for the time range REST call
    observations_range = get_observations_for_time_range(
        dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
        gallery_jwt_token, t1='2021-01-28T03:44:43', t2='2021-01-29T03:44:43')
    times = observations_range[0]['field_timerange'].split('--')
    t_start = parser.parse(times[0]).strftime('%Y-%m-%dT%H:%M:%S')
    t_end = parser.parse(times[1]).strftime('%Y-%m-%dT%H:%M:%S')
    assert t_start == '2021-01-28T03:44:43'
    assert t_end == '2021-01-29T03:44:43'


@pytest.mark.test_drupal
@pytest.mark.parametrize("request_product_id", ['Real', 'aaaaaaaaaaaaa'])
def test_update_product_gallery(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, request_product_id):
    import oda_api.plot_tools as pt

    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    source_name = "GX 1+4"
    product_title = source_name
    par_dict = {
        "DEC": -24.7456,
        "E1_keV": 28,
        "E2_keV": 50,
        "RA": 263.0090,
        "T1": '2012-07-03T00:00:00',
        "T2": '2014-04-03T17:59:59',
        "radius": 8,
        "src_name": source_name,
        "max_pointings": 10,
        "detection_threshold": "7.0",
        "instrument": "isgri",
        "integral_data_rights": "public",
        "off_line": "False",
        "product": "isgri_spectrum",
        "product_type": "Dummy",
    }

    disp = dispatcher_api_with_gallery

    isgri_spec = disp.get_product(**par_dict)
    if request_product_id == 'Real':
        request_product_id = oda_api.api.DispatcherAPI.calculate_param_dict_id(par_dict)

    light_curve_product = pt.OdaSpectrum(isgri_spec)
    gallery_image = light_curve_product.get_image_for_gallery(in_source_name=source_name, xlim=[20, 100])

    e1_kev = 45
    e2_kev = 95

    res = disp.post_data_product_to_gallery(product_title=product_title,
                                            gallery_image_path=gallery_image,
                                            product_id=request_product_id,
                                            token=encoded_token,
                                            e1_kev=e1_kev, e2_kev=e2_kev)

    assert 'nid' in res
    nid_creation = res['nid'][0]['value']

    assert 'title' in res
    assert res['title'][0]['value'] == product_title

    assert 'field_e1_kev' in res
    assert res['field_e1_kev'][0]['value'] == e1_kev

    assert 'field_e2_kev' in res
    assert res['field_e2_kev'][0]['value'] == e2_kev

    assert 'field_in_evidence' in res
    assert res['field_in_evidence'][0]['value'] is False

    e1_kev += 10
    e2_kev += 95
    product_title += '_updated'
    observation = 'test observation'

    res = disp.post_data_product_to_gallery(product_title=product_title,
                                            product_id=request_product_id,
                                            observation_id=observation,
                                            token=encoded_token,
                                            in_evidence=True,
                                            e1_kev=e1_kev, e2_kev=e2_kev)

    assert 'nid' in res
    nid_update = res['nid'][0]['value']
    assert nid_update == nid_creation

    assert 'title' in res
    assert res['title'][0]['value'] == product_title

    assert 'field_e1_kev' in res
    assert res['field_e1_kev'][0]['value'] == e1_kev

    assert 'field_e2_kev' in res
    assert res['field_e2_kev'][0]['value'] == e2_kev

    assert 'field_in_evidence' in res
    assert res['field_in_evidence'][0]['value'] is True

    link_field_derived_from_observation = os.path.join(
        dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
        'rest/relation/node/data_product/field_derived_from_observation')
    assert link_field_derived_from_observation in res['_links']


@pytest.mark.test_drupal
def test_delete_product_gallery(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery):
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')
    product_id = 'aaabbbccc_' + str(time.time())
    disp = dispatcher_api_with_gallery

    disp.post_data_product_to_gallery(product_title='Test data product to be deleted',
                                      token=encoded_token,
                                      product_id=product_id,
                                      e1_kev=45, e2_kev=95)

    list_products = disp.get_list_products_with_conditions(token=encoded_token, product_id=product_id)
    assert len(list_products) == 1

    res = disp.delete_data_product_from_gallery_via_product_id(token=encoded_token, product_id=product_id)
    assert res == {}

    list_products = disp.get_list_products_with_conditions(token=encoded_token, product_id=product_id)
    assert len(list_products) == 0


@pytest.mark.test_drupal
@pytest.mark.parametrize("product_type", ["spectrum", "lightcurve", "image"])
def test_product_gallery_get_product_with_conditions(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, product_type):
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        "roles": "general, gallery contributor",
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')
    disp = dispatcher_api_with_gallery
    product_type_arg = 'isgri_lc'
    if product_type == 'spectrum':
        product_type_arg = 'isgri_spectrum'
    elif product_type == 'image':
        product_type_arg = 'isgri_image'

    instrument_name = 'isgri'
    T1 = '2022-07-21T00:29:47'
    T1_revs = 2528

    T2 = '2022-08-23T05:29:11'
    T2_revs = 2540

    source_name = 'test astro entity' + '_' + str(uuid.uuid4())
    product_title = 'test same source different name'
    disp.post_data_product_to_gallery(
        product_title=product_title,
        instrument=instrument_name,
        product_type=product_type_arg,
        src_name=source_name,
        insert_new_source=True,
        token=encoded_token,
        e1_kev=150, e2_kev=350,
        ra=140, dec=-10,
        T1=T1, T2=T2
    )

    if product_type == 'spectrum' or product_type == 'lightcurve':
        for e1_kev, e2_kev, t1, t2 in [
            (100, 350, '2022-07-21T00:29:47', '2022-08-23T05:29:11'),
            (100, 350, '2022-07-19T00:29:47', '2022-08-25T05:29:11'),
            (100, 350, '2022-07-29T00:29:47', '2022-08-01T05:29:11'),
            (100, 350, '2022-07-19T00:29:47', '2022-08-23T05:29:11'),
            (50, 400, '2022-07-21T00:29:47', '2022-08-23T05:29:11'),
            (200, 350, '2022-07-21T00:29:47', '2022-08-23T05:29:11'),
            (50, 300, '2022-07-21T00:29:47', '2022-08-23T05:29:11'),
        ]:
            params = {'time_to_convert': t1,
                      'token': encoded_token}

            c = requests.get(os.path.join(disp.url, "get_revnum"),
                             params={**params}
                             )
            revnum_obj = c.json()
            t1_revs = revnum_obj['revnum']

            params['time_to_convert'] = t2
            c = requests.get(os.path.join(disp.url, "get_revnum"),
                             params={**params}
                             )
            revnum_obj = c.json()

            t2_revs = revnum_obj['revnum']
            if product_type == 'spectrum':
                spectra_list = disp.get_list_spectra_with_conditions(source_name=source_name,
                                                                     t1=t1, t2=t2,
                                                                     instrument=instrument_name,
                                                                     token=encoded_token)
                assert isinstance(spectra_list, list)

                if t1_revs > T1_revs or t2_revs < T2_revs:
                    assert len(spectra_list) == 0
                else:
                    assert len(spectra_list) == 1

            elif product_type == 'lightcurve':
                lightcurves_list = disp.get_list_lightcurve_with_conditions(source_name=source_name,
                                                                        e1_kev=e1_kev, e2_kev=e2_kev,
                                                                        t1=t1, t2=t2,
                                                                        instrument=instrument_name,
                                                                        token=encoded_token)
                assert isinstance(lightcurves_list, list)

                if e1_kev > 150 or e2_kev < 350 or t1_revs > T1_revs or t2_revs < T2_revs:
                    assert len(lightcurves_list) == 0
                else:
                    assert len(lightcurves_list) == 1

    elif product_type == 'image':
        for r in [0, 20, 200]:
            images_list = disp.get_list_images_angular_distance(e1_kev=100, e2_kev=400,
                                                                t1='2022-07-20T00:00:00', t2='2022-08-24T23:59:59',
                                                                ra_ref=100, dec_ref=0, r=r,
                                                                instrument=instrument_name,
                                                                token=encoded_token)
            assert isinstance(images_list, list)

            if r > 20:
                assert any(image.get("title") == product_title for image in images_list)
            else:
                assert all(image.get("title") != product_title for image in images_list)


@pytest.mark.test_drupal
@pytest.mark.parametrize("product_type", ["spectrum", "lightcurve", "image"])
def test_product_gallery_get_product_with_conditions_long_time_range(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, product_type):
    disp = dispatcher_api_with_gallery
    token_payload = {
        **default_token_payload,
        "roles": "general, gallery contributor",
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')
    if product_type == 'spectrum':
        spectra_list = disp.get_list_spectra_with_conditions(t1='2003-01-01T00:00:00', t2='2024-08-24T23:59:59',
                                                             instrument="isgri",
                                                             token=encoded_token,
                                                           max_span_rev=0)
        assert isinstance(spectra_list, list)
        print(f"spectra_list has {len(spectra_list)} products")

    elif product_type == 'image':
        images_list = disp.get_list_images_with_conditions(t1='2003-01-01T00:00:00', t2='2024-08-24T23:59:59',
                                                           instrument="isgri",
                                                           token=encoded_token,
                                                           max_span_rev=0
                                                           )

        assert isinstance(images_list, list)
        print(f"images_list has {len(images_list)} products")
        images_list = disp.get_list_products_with_conditions(token=encoded_token,
                                                                  instrument_name="isgri",
                                                                  product_type='image',
                                                                  rev1_value=100,
                                                                  rev2_value=2800)
        assert isinstance(images_list, dict)
        assert images_list['error_message'] == 'issue when performing a request to the product gallery'

    elif product_type == 'lightcurve':
        lightcurves_list = disp.get_list_lightcurve_with_conditions(t1='2003-01-01T00:00:00', t2='2024-08-24T23:59:59',
                                                                    instrument="isgri",
                                                                    token=encoded_token,
                                                           max_span_rev=0)
        assert isinstance(lightcurves_list, list)
        print(f"lightcurves_list has {len(lightcurves_list)} products")


@pytest.mark.test_drupal
@pytest.mark.parametrize("span_rev", [[100, 2500], [None, 50], [50, None], [None, None]])
def test_product_gallery_get_product_with_conditions_long_time_range_rev_range(dispatcher_api_with_gallery, span_rev):
    disp = dispatcher_api_with_gallery
    images_list = disp.get_list_images_with_conditions(t1='2003-01-01T00:00:00', t2='2024-08-24T23:59:59',
                                                       instrument="isgri",
                                                       min_span_rev=span_rev[0],
                                                       max_span_rev=span_rev[1]
                                                       )

    assert isinstance(images_list, list)
    print(f"images_list has {len(images_list)} products")

    # test the span rev is actually >= 100 and <= 2500
    for image in images_list:
        if span_rev[0] is None:
            span_rev[0] = 0
        if span_rev[1] is None:
            span_rev[1] = 3000
        assert span_rev[0] <= (float(image['rev2']) - float(image['rev1']))  <= span_rev[1]


@pytest.mark.test_drupal
@pytest.mark.parametrize("source_name", ["new", "known"])
def test_product_gallery_get_product_list_by_source_name(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, source_name):
    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        "roles": "general, gallery contributor",
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')
    disp = dispatcher_api_with_gallery

    if source_name == 'new':
        source_name = 'test astro entity' + '_' + str(uuid.uuid4())
        product_title = 'test same source different name'
        disp.post_data_product_to_gallery(product_title=product_title,
                                          token=encoded_token,
                                          insert_new_source=True,
                                          src_name=source_name)

        product_list_given_source = disp.get_list_products_by_source_name(source_name=source_name,
                                                                          token=encoded_token)

        assert isinstance(product_list_given_source, list)
        assert len(product_list_given_source) == 1
        assert 'title' in product_list_given_source[0]
        assert product_list_given_source[0]['title'] == product_title
    else:
        source_name = "V404 Cyg"
        product_list_given_source_name = disp.get_list_products_by_source_name(source_name=source_name,
                                                                               token=encoded_token)

        print(f"List product for source {source_name}: {product_list_given_source_name}")

        source_name = "1RXS J202405.3+335157"
        product_list_given_alternative_name = disp.get_list_products_by_source_name(source_name=source_name,
                                                                                    token=encoded_token)
        print(f"List product for source {source_name}: {product_list_given_alternative_name}")

        # Create sets of dictionaries
        set1 = set(map(lambda d: frozenset(d.items()), product_list_given_source_name))
        set2 = set(map(lambda d: frozenset(d.items()), product_list_given_alternative_name))

        # Find the differences
        diff1 = set1 - set2
        diff2 = set2 - set1

        assert diff2 == set()
        assert diff1 == set()


@pytest.mark.test_drupal
@pytest.mark.parametrize("source_name", ['Mrk 421', 'Mrk421', 'Mrk_421'])
def test_product_gallery_get_astro_entity(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, source_name):

    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        "roles": "general, gallery contributor",
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    disp = dispatcher_api_with_gallery
    disp.post_data_product_to_gallery(product_title='test same source different name',
                                      token=encoded_token,
                                      insert_new_source=True,
                                      src_name=source_name)

    c = requests.get(os.path.join(disp.url, "get_all_astro_entities"),
                     params={'token': encoded_token}
                     )

    assert c.status_code == 200
    drupal_res_obj = c.json()

    assert isinstance(drupal_res_obj, list)
    if source_name == 'Mrk 421':
        assert source_name in drupal_res_obj
    else:
        assert source_name not in drupal_res_obj


@pytest.mark.test_drupal
@pytest.mark.parametrize("source_name", ['Mrk 421', 'Mrk421', 'Mrk_421', 'GX 1+4', 'fake object', None])
def test_resolve_source(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, source_name):
    disp = dispatcher_api_with_gallery

    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    resolved_obj = disp.resolve_source(source_name, encoded_token)

    if source_name is None:
        assert resolved_obj is None
    elif source_name == 'fake object':
        assert 'name' in resolved_obj
        assert 'message' in resolved_obj

        # the name resolver replaces automatically underscores with spaces in the returned name
        assert resolved_obj['name'] == source_name
        assert 'could not be resolved' in resolved_obj['message']
    else:
        assert 'name' in resolved_obj
        assert 'DEC' in resolved_obj
        assert 'RA' in resolved_obj
        assert 'entity_portal_link' in resolved_obj
        assert 'object_type' in resolved_obj
        assert 'object_ids' in resolved_obj
        assert 'RA' in resolved_obj
        assert 'DEC' in resolved_obj
        assert 'message' in resolved_obj

        quoted_source_name = urllib.parse.quote(source_name.strip())

        assert resolved_obj['name'] == source_name.replace('_', ' ')
        assert resolved_obj['entity_portal_link'] == dispatcher_test_conf_with_gallery["product_gallery_options"]["entities_portal_url"]\
            .format(quoted_source_name)


@pytest.mark.test_drupal
@pytest.mark.parametrize("product_type", ['isgri_image', 'jemx_lc', 'aaaaaa', '', None])
@pytest.mark.parametrize("provide_source", [True, False])
def test_check_product_type_policy(dispatcher_api_with_gallery, dispatcher_test_conf_with_gallery, product_type, provide_source):
    disp = dispatcher_api_with_gallery

    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    par_dict = {
        "DEC": -24.7456,
        "E1_keV": 28,
        "E2_keV": 50,
        "RA": 263.0090,
        "T1": '2012-07-03T00:00:00',
        "T2": '2014-04-03T17:59:59',
        "radius": 8,
        "product_type": product_type,
    }

    if provide_source:
        par_dict['src_name'] = 'Crab'

    if product_type == 'jemx_lc' and not provide_source:
        with pytest.raises(oda_api.api.UserError):
            disp.check_gallery_data_product_policy(encoded_token, **par_dict)
    else:
        assert disp.check_gallery_data_product_policy(encoded_token, **par_dict)