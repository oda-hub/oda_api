import pytest
import json
from astropy.io import fits
import numpy as np
import time
import jwt
import os

from cdci_data_analysis.analysis.json import CustomJSONEncoder
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
@pytest.mark.parametrize("observation", ['test observation', None])
@pytest.mark.parametrize("source_name", ['GX 1+4', None])
def test_image_product_gallery(dispatcher_api_with_gallery, observation, source_name):
    import oda_api.plot_tools as pt

    # let's generate a valid token
    token_payload = {
        **default_token_payload,
        'roles': 'general, gallery contributor'
    }
    encoded_token = jwt.encode(token_payload, secret_key, algorithm='HS256')

    product_name = "isgri_image"
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
        "instrument": "isgri",
        "integral_data_rights": "public",
        "oda_api_version": "1.1.22",
        "off_line": "False",
        "osa_version": "OSA11.1",
        "product": product_name,
        "product_type": "Dummy",
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

    res = disp.post_data_product_to_gallery(src_name=source_name,
                                            gallery_image_path=gallery_image,
                                            fits_file_path=fits_file,
                                            observation_id=observation,
                                            token=encoded_token,
                                            e1_kev=e1_kev, e2_kev=e2_kev,
                                            DEC=dec, RA=ra
                                            )

    if source_name is None:
        source_name = 'source'
    prod_title = source_name + "_" + product_name

    assert 'title' in res
    assert res['title'][0]['value'] == prod_title

    assert 'field_e1_kev' in res
    assert res['field_e1_kev'][0]['value'] == e1_kev

    assert 'field_e2_kev' in res
    assert res['field_e2_kev'][0]['value'] == e2_kev

    assert 'field_dec' in res
    assert res['field_dec'][0]['value'] == dec

    assert 'field_ra' in res
    assert res['field_ra'][0]['value'] == ra


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
