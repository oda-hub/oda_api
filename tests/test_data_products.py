import pytest
import json
from astropy.io import fits
import numpy as np

from cdci_data_analysis.analysis.json import CustomJSONEncoder
from oda_api.data_products import NumpyDataProduct

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
