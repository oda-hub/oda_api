from datetime import datetime
import logging

import pytest
import json

from astropy.io import fits
import numpy as np
import time
import os
import typing
from oda_api.api import DataCollection
from oda_api.json import CustomJSONEncoder
import filecmp

from oda_api.data_products import (LightCurveDataProduct, 
                                   NumpyDataProduct, 
                                   ODAAstropyTable, 
                                   PictureProduct,
                                   BinaryProduct,
                                   TextLikeProduct)
from astropy import time as atime
from astropy import units as u
from astropy.table import Table
from matplotlib import pyplot as plt

import base64
import pickle

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


def test_variable_length_rmf():
    # "compressed" (by removing small matrix values, special RMF spec) RMF is stored in variable length table
    # which is not well supported by astropy

    isgri_rmf_dp_post_scan = NumpyDataProduct.from_fits_file("tests/test_data/isgri_rmf_Crab.fits")
    isgri_rmf_dp_post_scan.data_unit[2].to_fits_hdu()
    encoded_numpy_data_prod_postscan = isgri_rmf_dp_post_scan.encode()
    decoded_numpy_data_prod_postscan = NumpyDataProduct.decode(encoded_numpy_data_prod_postscan)                
    decoded_numpy_data_prod_postscan.data_unit[2].to_fits_hdu()
    
    isgri_rmf_dp = NumpyDataProduct.from_fits_file("tests/test_data/isgri_rmf_Crab.fits")
    encoded_numpy_data_prod = isgri_rmf_dp.encode()
    decoded_numpy_data_prod = NumpyDataProduct.decode(encoded_numpy_data_prod)                    
    decoded_numpy_data_prod.data_unit[2].to_fits_hdu()

        
def test_rmf():
    isgri_rmf_dp = NumpyDataProduct.from_fits_file("tests/test_data/isgri_rmf_Crab.fits")

    for ID, _d in enumerate(isgri_rmf_dp.data_unit):
        print(ID, _d.header['EXTNAME'], _d.to_fits_hdu())
        
    encoded_numpy_data_prod = isgri_rmf_dp.encode()
    decoded_numpy_data_prod = NumpyDataProduct.decode(encoded_numpy_data_prod)
    
    # this is the higher-level call causing the above error in nb2workflow
    _hdul = fits.HDUList()
    for ID, _d in enumerate(decoded_numpy_data_prod.data_unit):
        print(ID, _d.header['EXTNAME'])
        try:
            _hdul.append(_d.to_fits_hdu())
        except Exception as ee:
            # print(ee)
            raise Exception(ee)
        
    # this reproduces the commands done inside the above call (?)
    binarys = base64.b64decode(encoded_numpy_data_prod['data_unit_list'][2]['binarys'])
    try:
        pickle.loads(binarys, encoding='bytes')
        print('pickle test successful')
    except Exception as ee:
        raise Exception(ee)

        

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

@pytest.mark.parametrize('ext', ['png', 'jpg', 'svg', 'webp', 'tiff'])
def test_bin_image(ext):
    data = np.zeros((10, 2))
    data[:,0] = range(len(data))
    data[:,1] = np.random.rand(len(data))
    plt.plot(data[:,0], data[:,1])
    if os.path.isfile(f'tmp.{ext}'):
        os.remove(f'tmp.{ext}')
    plt.savefig(f'tmp.{ext}')
    with open(f'tmp.{ext}', 'rb') as fd:
        figdata = fd.read()

    bin_image = PictureProduct.from_file(f'tmp.{ext}')
    
    assert bin_image.binary_data == figdata
    
    bin_image_decoded = encode_decode(bin_image)
    
    assert bin_image_decoded.binary_data == figdata


@pytest.mark.parametrize('times,values,time_format,expected_units_dict_variants,timedel',
                         [(atime.Time(['2022-02-20T13:45:34', '2022-02-20T14:45:34', '2022-02-20T15:45:34']), 
                           [2/u.cm**2/u.s] * 3, 
                           None,
                           [{'TIME': 'd', 'FLUX': '1 / (cm**2 s)', 'ERROR': '1 / (cm**2 s)'},
                            {'TIME': 'd', 'FLUX': '1 / (s cm**2)', 'ERROR': '1 / (s cm**2)'}],
                           None),
                                                  
                          (['2022-02-20T13:45:34', '2022-02-20T14:45:34', '2022-02-20T15:45:34'],
                           [2] * 3,
                           None,
                           [{'TIME': 'd'}],
                           0.5),
                          
                          ([59630.3, 59630.5, 59630.7],
                           [2] * 3,
                           'mjd',
                           [{'TIME': 'd', 'TIMEDEL': 'd'}],
                           [0.5] * 3),
                          
                          (list(map(datetime.fromisoformat, ['2022-02-20T13:45:34', '2022-02-20T14:45:34', '2022-02-20T15:45:34'])),
                           [2/u.cm**2/u.s] * 3, 
                           None,
                           [{'TIME': 'd', 'FLUX': '1 / (cm**2 s)', 'ERROR': '1 / (cm**2 s)'},
                            {'TIME': 'd', 'FLUX': '1 / (s cm**2)', 'ERROR': '1 / (s cm**2)'}],
                           None),
                          ]
                         )
def test_lightcurve_product_from_arrays(times, values, time_format, 
                                        expected_units_dict_variants, timedel):
    errors = [0.05 * x for x in values]
    lc = LightCurveDataProduct.from_arrays(times=times, fluxes=values, 
                                           errors=errors, 
                                           time_format=time_format, 
                                           timedel=timedel)
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
    
def test_decode_wrong_replacement():
    infile = 'tests/test_data/1E_1740_7_2942_isgri_mosaic_clean_significance25_40.fits.gz'
    npd = NumpyDataProduct.from_fits_file(infile)
    encode_decode(npd)


def test_textlike_product_write_file_roundtrip(tmp_path):
    prod = TextLikeProduct('hello world', name='textprod')

    out_txt = tmp_path / 'hello.txt'
    prod.write_file(str(out_txt))
    assert out_txt.read_text(encoding='utf-8') == 'hello world'


def test_picture_product_write_file_roundtrip(tmp_path):
    fn = tmp_path / 'plot.png'
    plt.plot([0, 1], [0, 1])
    plt.savefig(str(fn))
    plt.close()

    picture = PictureProduct.from_file(str(fn), name='picprod')
    out_fn = tmp_path / 'out_plot.png'
    picture.write_file(str(out_fn))

    assert out_fn.read_bytes() == fn.read_bytes()


def test_odaatable_write_file_roundtrip(tmp_path):
    data = np.zeros((3, 2))
    data[:, 0] = range(len(data))
    data[:, 1] = range(len(data), 0, -1)
    table = Table(data, names=['a', 'b'])
    tabp = ODAAstropyTable(table, name='tableprod')

    out_fn = tmp_path / 'table.fits'
    tabp.write_file(str(out_fn))

    loaded = ODAAstropyTable.from_file(str(out_fn), format='fits')
    assert loaded.table.colnames == ['a', 'b']
    assert np.array_equal(np.asarray(loaded.table['a']), data[:, 0])
    assert np.array_equal(np.asarray(loaded.table['b']), data[:, 1])


def test_numpy_data_product_write_file_roundtrip(tmp_path):
    fn = tmp_path / 'numeric.fits'
    hdu = fits.PrimaryHDU(np.arange(4).reshape((2, 2)))
    hdu.writeto(str(fn), overwrite=True)

    prod = NumpyDataProduct.from_file(str(fn))
    out_fn = tmp_path / 'roundtrip.fits'
    prod.write_file(str(out_fn))

    loaded = NumpyDataProduct.from_file(str(out_fn))
    assert np.array_equal(loaded.data_unit[0].data, prod.data_unit[0].data)


def test_lightcurve_data_product_write_file_roundtrip(tmp_path):
    times = ['2022-02-20T13:45:34', '2022-02-20T14:45:34']
    values = [2, 3]
    errors = [0.1, 0.1]
    lc = LightCurveDataProduct.from_arrays(times=times, fluxes=values, errors=errors)

    out_fn = tmp_path / 'lightcurve.fits'
    lc.write_file(str(out_fn))

    loaded = NumpyDataProduct.from_file(str(out_fn))
    assert np.array_equal(loaded.data_unit[1].data['FLUX'], np.array(values))
    assert np.array_equal(loaded.data_unit[1].data['ERROR'], np.array(errors))


def test_save_all_data_mixed_collection(tmp_path):
    table = Table({'a': [1, 2], 'b': [3, 4]})
    astable = ODAAstropyTable(table, name='table')
    bin_prod = BinaryProduct.from_file('tests/test_data/lc.fits', name='binprd')

    plot_fn = tmp_path / 'plot.png'
    plt.plot([1, 2], [1, 0])
    plt.savefig(str(plot_fn))
    plt.close()
    picture = PictureProduct.from_file(str(plot_fn), name='pic')
    text = TextLikeProduct('hello', name='text')
    lc = LightCurveDataProduct.from_arrays(['2022-02-20T13:45:34', '2022-02-20T14:45:34'], fluxes=[2, 3], errors=[0.1, 0.2])
    dc = DataCollection([astable, bin_prod, picture, text, lc])

    out_dir = tmp_path / 'saved'
    os.makedirs(out_dir, exist_ok=True)
    dc.save_all_data(prenpend_name=str(out_dir / 'mixed'))

    expected_files = [
        out_dir / 'mixed_table_0.fits',
        out_dir / 'mixed_binprd_1.fits',
        out_dir / 'mixed_pic_2.png',
        out_dir / 'mixed_text_3.txt',
        out_dir / 'mixed_prod_4.fits',
    ]

    for expected in expected_files:
        assert expected.exists()


def test_save_all_data_empty_collection(tmp_path):
    dc = DataCollection([])
    dc.save_all_data(prenpend_name=str(tmp_path / 'empty'))
    assert not any(tmp_path.iterdir())


def test_save_all_data_skips_unsupported_product(caplog, tmp_path):
    caplog.set_level(logging.WARNING)
    text = TextLikeProduct('hello', name='text')
    unsupported = object()
    dc = DataCollection([text, unsupported])

    dc.save_all_data(prenpend_name=str(tmp_path / 'skipped'))

    assert 'Writing on disk is not implemented for' in caplog.text
    assert (tmp_path / 'skipped_text_0.txt').exists()