from datetime import datetime

import pytest
import json
from astropy.io import fits
from dateutil import parser
import numpy as np
import time
import jwt
import os
import random
import string

from cdci_data_analysis.analysis.json import CustomJSONEncoder
from cdci_data_analysis.analysis.drupal_helper import get_observations_for_time_range, get_user_id, generate_gallery_jwt_token

import oda_api
import oda_api.api
from oda_api.data_products import NumpyDataProduct

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

def encode_decode(ndp: NumpyDataProduct) -> NumpyDataProduct:
    ndp_json = json.dumps(ndp, cls=CustomJSONEncoder)

    print(ndp_json)

    return NumpyDataProduct.decode(ndp_json)



def test_one_image():
    fn = "one_image.fits"

    data = np.zeros((3,3), dtype=np.int16)

    hdu = fits.ImageHDU(data)
    hdu.writeto(fn, overwrite=True)

    ndp = NumpyDataProduct.from_fits_file(fn)

    ndu = ndp.get_data_unit(1)

    assert np.all(ndu.data == data)

    ndu_decoded = encode_decode(ndp).get_data_unit(1)

    assert np.all(ndu_decoded.data == data)


def test_variable_length_table():
    from oda_api.data_products import NumpyDataProduct

    col1 = fits.Column(
        name='var', format='PI()',
        array=np.array([[1,2,3], [11, 12]], dtype=np.object_))

    col2 = fits.Column(
        name='i2', format='2I',
        array=np.array([[101,102], [111, 112]], dtype=np.object_))

    hdu = fits.BinTableHDU.from_columns([col1, col2])

    fn = "vlf_table.fits"

    hdu.writeto(fn, overwrite=True)

    ndp = NumpyDataProduct.from_fits_file(fn)

    ndu = ndp.get_data_unit(1)

    assert list(ndu.data['i2'][0]) == [101, 102]
    assert list(ndu.data['i2'][1]) == [111, 112]
    assert list(ndu.data['var'][0]) == [1, 2, 3]
    assert list(ndu.data['var'][1]) == [11, 12]

    ndu_decoded = encode_decode(ndp).get_data_unit(1)

    assert list(ndu_decoded.data['i2'][0]) == [101, 102]
    assert list(ndu_decoded.data['i2'][1]) == [111, 112]
    assert list(ndu_decoded.data['var'][0]) == [1, 2, 3]
    assert list(ndu_decoded.data['var'][1]) == [11, 12]


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
        "oda_api_version": "1.1.22",
        "off_line": "False",
        "osa_version": "OSA11.1",
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
        "oda_api_version": "1.1.22",
        "off_line": "False",
        "osa_version": "OSA11.1",
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
        "osa_version": "OSA11.1",
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
                                            observation_id=observation,
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
@pytest.mark.parametrize("obsid", [1960001, ["1960001", "1960002", "1960003"]])
@pytest.mark.parametrize("yaml_files", [None, "single", "list"])
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
    elif yaml_files == "list":
        yaml_file_path = ["observation_yaml_dummy_files/obs_rev_1.yaml", "observation_yaml_dummy_files/obs_rev_2.yaml"]

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
                assert res['field_obsid'][obsid.index(single_obsid)]['value'] == single_obsid
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
        "osa_version": "OSA11.1",
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

    e1_kev += 10
    e2_kev += 95
    product_title += '_updated'
    observation = 'test observation'

    res = disp.post_data_product_to_gallery(product_title=product_title,
                                            product_id=request_product_id,
                                            observation_id=observation,
                                            token=encoded_token,
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

    link_field_derived_from_observation = os.path.join(
        dispatcher_test_conf_with_gallery['product_gallery_options']['product_gallery_url'],
        'rest/relation/node/data_product/field_derived_from_observation')
    assert link_field_derived_from_observation in res['_links']


@pytest.mark.test_drupal
@pytest.mark.parametrize("source_name", ['Mrk 421', 'Mrk_421', 'GX 1+4', 'fake object', None])
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

        assert resolved_obj['name'] == source_name.replace('_', ' ')
        assert resolved_obj['entity_portal_link'] == dispatcher_test_conf_with_gallery["product_gallery_options"]["entities_portal_url"]\
            .format(source_name)


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
