import pytest
import json
from astropy.io import fits
import numpy as np
import time
import jwt

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
def test_product_gallery_post_product(dispatcher_api):
    import oda_api.plot_tools as pt
    import oda_api.api

    par_dict = {
        "DEC": 263.0090,
        "E1_keV": 28,
        "E2_keV": 50,
        "RA": 263.0090,
        "T1": '2019-01-01T00:00:00',
        "T2": '2019-03-31T23:59:59',
        "radius": 8,
        "src_name": "GX 1+4",
        "max_pointings": 10,
        "detection_threshold": "7.0",
        "instrument": "isgri",
        "integral_data_rights": "public",
        "oda_api_version": "1.1.22",
        "off_line": "False",
        "osa_version": "OSA11.1",
        "product": "isgri_image",
        "product_type": "Dummy",
    }

    # host = "https://www.astro.unige.ch/mmoda/dispatch-data"

    disp = dispatcher_api
    # disp = oda_api.api.DispatcherAPI(url=host)

    isgri_image = disp.get_product(**par_dict)

    image_product = pt.OdaImage(isgri_image)
    gallery_image = image_product.get_image_for_gallery()

    disp.post_data_product_to_gallery(gallery_image)
