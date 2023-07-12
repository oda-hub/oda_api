from datetime import datetime

import pytest
import json

from astropy.io import fits
import numpy as np
import time
import os
import typing
from oda_api.json import CustomJSONEncoder
import filecmp

from oda_api.data_products import (LightCurveDataProduct, 
                                   NumpyDataProduct, 
                                   ODAAstropyTable, 
                                   PictureProduct,
                                   BinaryProduct)
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

    ndp.data_unit[1].name = None

    hdu_list_obj = ndp.to_fits_hdu_list()

    assert hdu_list_obj[0].name == 'PRIMARY'
    assert hdu_list_obj[1].name == 'TABLE'


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


@pytest.mark.parametrize('times,values,time_format,expected_units_dict_variants',
                         [(atime.Time(['2022-02-20T13:45:34', '2022-02-20T14:45:34', '2022-02-20T15:45:34']), 
                           [2/u.cm**2/u.s] * 3, 
                           None,
                           [{'TIME': 'd', 'FLUX': '1 / (cm**2 s)', 'ERROR': '1 / (cm**2 s)'},
                            {'TIME': 'd', 'FLUX': '1 / (s cm**2)', 'ERROR': '1 / (s cm**2)'}]),
                                                  
                          (['2022-02-20T13:45:34', '2022-02-20T14:45:34', '2022-02-20T15:45:34'],
                           [2] * 3,
                           None,
                           [{'TIME': 'd'}]),
                          
                          ([59630.3, 59630.5, 59630.7],
                           [2] * 3,
                           'mjd',
                           [{'TIME': 'd'}]),
                          
                          (list(map(datetime.fromisoformat, ['2022-02-20T13:45:34', '2022-02-20T14:45:34', '2022-02-20T15:45:34'])),
                           [2/u.cm**2/u.s] * 3, 
                           None,
                           [{'TIME': 'd', 'FLUX': '1 / (cm**2 s)', 'ERROR': '1 / (cm**2 s)'},
                            {'TIME': 'd', 'FLUX': '1 / (s cm**2)', 'ERROR': '1 / (s cm**2)'}]),
                          ]
                         )
def test_lightcurve_product_from_arrays(times, values, time_format, expected_units_dict_variants):
    errors = [0.05 * x for x in values]
    lc = LightCurveDataProduct.from_arrays(times = times, fluxes = values, errors = errors, time_format=time_format)
    assert lc.data_unit[1].units_dict in expected_units_dict_variants
    assert all(lc.data_unit[1].data['TIME'].astype('int') == 59630)
    
def test_new_binary_product():
    infile = 'tests/test_data/lc.fits'
    bin_prod = BinaryProduct.from_file(infile, name='binprd')
    encoded = bin_prod.encode()
    assert encoded['name'] == 'binprd'
    decoded = BinaryProduct.decode(encoded)
    assert decoded.name == 'binprd'
    decoded.write_file('decbinprd.foo')
    assert filecmp.cmp(infile, 'decbinprd.foo')
    os.remove('decbinprd.foo') 
    