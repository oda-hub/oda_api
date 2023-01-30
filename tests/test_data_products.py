from datetime import datetime

import pytest
import json
from astropy.io import fits
import numpy as np
import time
import jwt
import os
import random
import string
import typing

from oda_api.json import CustomJSONEncoder

import oda_api.api
from oda_api.data_products import LightCurveDataProduct, NumpyDataProduct, ODAAstropyTable, PictureProduct
from astropy import time as atime
from astropy import units as u
from astropy.table import Table
from matplotlib import pyplot as plt

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

# TODO: adapt to new product types and implement corresponding tests
def encode_decode(ndp: typing.Union[NumpyDataProduct, 
                                    ODAAstropyTable, 
                                    PictureProduct]) -> typing.Union[NumpyDataProduct, 
                                                                         ODAAstropyTable, 
                                                                         PictureProduct]:
    ndp_json = json.dumps(ndp, cls=CustomJSONEncoder)

    print(ndp_json)

    if isinstance(ndp, NumpyDataProduct):
        return NumpyDataProduct.decode(ndp_json)    
    
    if isinstance(ndp, ODAAstropyTable):
        return ODAAstropyTable.decode(ndp_json)
    
    if isinstance(ndp, PictureProduct):
        return PictureProduct.decode(ndp_json)
    
    

    
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

def test_astropy_table():
    data = np.zeros((10, 2))
    data[:,0] = range(len(data))
    data[:,1] = range(len(data), 0, -1)
    atable = Table(data, names=['a', 'b'])

    tabp = ODAAstropyTable(atable)

    assert (tabp.table.as_array().tolist() == data).all()
    assert tabp.table.colnames == ['a', 'b']

    tabp_decoded = encode_decode(tabp)

    assert (tabp_decoded.table.as_array().tolist() == data).all()
    assert tabp_decoded.table.colnames == ['a', 'b']
    
def test_bin_image():
    data = np.zeros((10, 2))
    data[:,0] = range(len(data))
    data[:,1] = np.random.rand(len(data))
    plt.plot(data[:,0], data[:,1])
    if os.path.isfile('tmp.png'):
        os.remove('tmp.png')
    plt.savefig('tmp.png')
    with open('tmp.png', 'rb') as fd:
        figdata = fd.read()

    bin_image = PictureProduct.from_file('tmp.png')
    
    assert bin_image.binary_data == figdata
    
    bin_image_decoded = encode_decode(bin_image)
    
    assert bin_image_decoded.binary_data == figdata

@pytest.mark.test_drupal
@pytest.mark.parametrize("observation", ['test observation', None])
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
            (type_source == 'new' and ((force_insert_not_valid_new_source and insert_new_source)
             or (not validate_source and insert_new_source))):
        assert link_astrophysical_entity in res['_links']
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

    res = disp.post_data_product_to_gallery(product_title=source_name,
                                            gallery_image_path=gallery_image,
                                            fits_file_path=[fits_file_1, fits_file_2],
                                            observation_id=observation,
                                            token=encoded_token,
                                            produced_by=notebook_link,
                                            job_id=job_id, session_id=session_id,
                                            e1_kev=e1_kev, e2_kev=e2_kev,
                                            instrument=instrument,
                                            product_type=product_type,
                                            DEC=dec, RA=ra)

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
@pytest.mark.parametrize("observation", ['test observation', None])
@pytest.mark.parametrize("source_name", ['GX 1+4', None])
def test_spectrum_product_gallery(dispatcher_api_with_gallery, observation, source_name):
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
    assert res['field_dec'][0]['value'] == dec

    assert 'field_ra' in res
    assert res['field_ra'][0]['value'] == ra


@pytest.mark.test_drupal
@pytest.mark.parametrize("source_name", ['Mrk 421', 'Mrk_421', 'fake object', None])
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
        assert 'Nothing found' in resolved_obj['message']
    else:
        assert 'name' in resolved_obj
        assert 'resolver' in resolved_obj
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


@pytest.mark.parametrize('times,values,time_format,expected_units_dict',
                         [(atime.Time(['2022-02-20T13:45:34', '2022-02-20T14:45:34', '2022-02-20T15:45:34']), 
                           [2/u.cm**2/u.s] * 3, 
                           None,
                           {'TIME': 'd', 'FLUX': '1 / (cm**2 s)', 'ERROR': '1 / (cm**2 s)'}),
                                                  
                          (['2022-02-20T13:45:34', '2022-02-20T14:45:34', '2022-02-20T15:45:34'],
                           [2] * 3,
                           None,
                           {'TIME': 'd'}),
                          
                          ([59630.3, 59630.5, 59630.7],
                           [2] * 3,
                           'mjd',
                           {'TIME': 'd'}),
                          
                          (list(map(datetime.fromisoformat, ['2022-02-20T13:45:34', '2022-02-20T14:45:34', '2022-02-20T15:45:34'])),
                           [2/u.cm**2/u.s] * 3, 
                           None,
                           {'TIME': 'd', 'FLUX': '1 / (cm**2 s)', 'ERROR': '1 / (cm**2 s)'}),
                          ]
                         )
def test_lightcurve_product_from_arrays(times, values, time_format, expected_units_dict):
    errors = [0.05 * x for x in values]
    lc = LightCurveDataProduct.from_arrays(times = times, fluxes = values, errors = errors, time_format=time_format)
    assert lc.data_unit[1].units_dict == expected_units_dict
    assert all(lc.data_unit[1].data['TIME'].astype('int') == 59630)
    