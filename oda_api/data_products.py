__author__ = "Andrea Tramacere"

import mimetypes
import typing
import traceback
import warnings

from json_tricks import numpy_encode,dumps
from astropy.io import fits as pf
from astropy.io import ascii as astropy_io_ascii
import json
from astropy.utils.misc import JsonCustomEncoder

from astropy.table import Table
from astropy.coordinates import Angle
from astropy.time import Time as aTime
from astropy.wcs import WCS
from astropy import units as u
from astropy.io.fits import FITS_rec, FitsHDU, Header

import  numpy
import numpy as np
import  base64
import  pickle
import gzip
import  hashlib

from io import StringIO, BytesIO
import pandas as pd
import puremagic
import os
import logging
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

from abc import ABC, abstractmethod

logger = logging.getLogger('oda_api.data_products')



def _chekc_enc_data(data):
    if isinstance(data, list):
        _l=data
    else:
        _l=[data]

    return _l


class DataProduct(ABC):
    name: str | None
    meta_data: dict

    @abstractmethod
    def encode(self, *args, **kwargs) -> str | dict[str, typing.Any]: ...

    @classmethod
    @abstractmethod
    def decode(cls, *args, **kwargs) -> "DataProduct": ...

    @abstractmethod
    def write_file(self, file_path, overwrite=True): ...

    @classmethod
    @abstractmethod
    def from_file(cls, *args, **kwargs) -> "DataProduct": ...

    @abstractmethod
    def suggest_fn_extension(self) -> str: ...


class ODAAstropyTable(DataProduct):
    def __init__(self,table_object: Table, name: str | None = None, meta_data: dict | None = None):
        if meta_data is None:
            meta_data = {}
        self.name=name
        self.meta_data=meta_data
        self._table=table_object

    def suggest_fn_extension(self) -> str:
        return 'fits'

    @property
    def table(self):
        return self._table
    
    def write(self,file_name,format='fits',overwrite=True):
        self._table.write(file_name,format=format,overwrite=overwrite)

    def write_fits_file(self,file_name,overwrite=True):
        self.write(file_name,overwrite=overwrite,format='fits')

    def write_file(self, file_path, overwrite=True):
        if file_path.endswith('.fits'):
            self.write_fits_file(file_path, overwrite=overwrite)
        else:
            # determine the format from the file extension
            self._table.write(file_path, overwrite=overwrite)

    
    @classmethod
    def from_file(cls, file_path, name=None, delimiter=None, format=None):
        _allowed_formats_=['ascii','ascii.ecsv','fits']
        if format == 'fits':
            # print('==>',file_name)
            table = Table.read(file_path, format=format)
        elif format == 'ascii.ecsv' or format=='ascii':
            table = Table.read(file_path, format=format, delimiter=delimiter)
        else:
            raise RuntimeError('table format not understood, allowed',_allowed_formats_)

        meta = None

        if hasattr(table, 'meta'):
            meta = table.meta

        return cls(table, meta_data=meta, name=name)

    def encode(self,use_binary=False,to_json = False):

        _o_dict = {}
        _o_dict['binary']=None
        _o_dict['ascii']=None

        if use_binary is True:
            _binarys = base64.b64encode(pickle.dumps(self.table, protocol=2)).decode('utf-8')
            _o_dict['binary'] = _binarys
        else:
            #with StringIO() as fh:
            fh=StringIO()
            self.table.write(fh, format='ascii.ecsv')
            _text = fh.getvalue()
            fh.close()
            _o_dict['ascii'] = _text

        _o_dict['name']=self.name
        _o_dict['meta_data']=dumps(self.meta_data)

        if to_json:
            _o_dict=json.dumps(_o_dict)
        return   _o_dict

    @classmethod
    def decode(cls, o_dict: dict[str, typing.Any], use_binary=False):
        if isinstance(o_dict, dict):
            _o_dict = o_dict
        elif isinstance(o_dict, str):
            _o_dict = json.loads(o_dict)
        else:
            raise RuntimeError('Wrong table structure')
        encoded_name = _o_dict['name']
        encoded_meta_data = _o_dict['meta_data']
        if use_binary is True:
            t_rec = base64.b64decode(_o_dict['binary'])
            try:
                t_rec = pickle.loads(t_rec)
            except Exception:
                t_rec = pickle.loads(t_rec, encoding='latin')

        else:
            t_rec = astropy_io_ascii.read(_o_dict['ascii'])

        return cls(typing.cast(Table, t_rec),name=encoded_name,meta_data=encoded_meta_data)


class BinaryData(object):

    def __init__(self,file_path=None):
        warnings.warn('BinaryData class is deprecated, please use BinaryProduct instead', DeprecationWarning, stacklevel=2)
        self.file_path=file_path

    def encode(self,file_path=None):
        if file_path is None:
            file_path=self.file_path
        _file_binary = open(file_path, 'rb').read() # type: ignore
        _file_b64 = base64.urlsafe_b64encode(_file_binary)
        _file_b64_md5 = hashlib.md5(_file_binary).hexdigest()

        return _file_b64,_file_b64_md5
    
    def decode(self,encoded_obj):
        return base64.urlsafe_b64decode(encoded_obj.encode('ascii', 'ignore'))
         

class BinaryProduct(DataProduct):
    # New implementation of binary data product. 
    # The meaning of the methods is more in-line with the rest of the products
    def __init__(self, bin_data: bytes, name: str | None = None):
        self.bin_data = bin_data
        if name == 'None': 
            name = None
        self.name = name

    def suggest_fn_extension(self) -> str:
        suggested_extension = puremagic.from_string(self.bin_data)
        if suggested_extension:
            return suggested_extension.strip('.')
        return 'bin'
        
    def encode(self):
        return {
            'name': self.name,
            'data': base64.urlsafe_b64encode(self.bin_data).decode(),
            'md5': hashlib.md5(self.bin_data).hexdigest()
        }
    
    @classmethod
    def decode(cls, encoded_obj: dict | str):
        if isinstance(encoded_obj, str):
            _encoded_obj: dict = json.loads(encoded_obj)
        else:
            _encoded_obj = encoded_obj
            
        name = _encoded_obj['name']
        bin_data = base64.urlsafe_b64decode(_encoded_obj['data'].encode('ascii', 'ignore'))
        decoded_md5 = hashlib.md5(bin_data).hexdigest()
        assert decoded_md5 == _encoded_obj['md5']
        
        return cls(bin_data, name)
    
    def write_file(self, file_path, overwrite = True):
        if os.path.exists(file_path) and not overwrite:
            raise FileExistsError(f'File {file_path} already exists')
        with open(file_path, 'wb') as fd:
            fd.write(self.bin_data)
    
    @classmethod        
    def from_file(cls, file_path, name=None):
        with open(file_path, 'rb') as fd:
            bin_data = fd.read()
        return cls(bin_data, name)



class NumpyDataUnit:

    def __init__(self, 
                 data: numpy.ndarray | None, 
                 data_header: dict | None =None, 
                 meta_data: dict | None = None, 
                 hdu_type: str | None = None, 
                 name: str | None = None, 
                 units_dict: dict | None = None):

        if meta_data is None:
            meta_data = {}
        if data_header is None:
            data_header = {}

        self._hdu_type_list_ = ['primary', 'image', 'table', 'bintable']

        self.name=name
        self._check_data(data)
        self._check_hdu_type(hdu_type)
        self._check_dict(data_header)
        self._check_dict(meta_data)

        self.data=data
        self.header=data_header
        self.meta_data=meta_data
        self.hdu_type=hdu_type
        self.units_dict=units_dict

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name_value):
        if name_value is None:
            self._name = 'table'
        else:
            self._name = name_value

    # interface with a typo, preserving with a warning
    def _warn_chekc_typo(self):
        logger.debug('please _check_* instead of _chekc_* functions, they will be removed')
    
    def _chekc_data(self, data):
        self._warn_chekc_typo()
        return self._check_data(data)        

    def _chekc_hdu_type(self,hdu_type):
        return self._check_hdu_type(hdu_type)

    def _chekc_dict(self, _kw):
        self._warn_chekc_typo()
        return self._check_dict(_kw)

    def _check_data(self, data: numpy.ndarray | None):
        if not (isinstance(data, numpy.ndarray) or data is None):
            raise RuntimeError('data is not numpy ndarray object')

    def _check_hdu_type(self, hdu_type: str | None):
        if not (hdu_type is None or hdu_type in self._hdu_type_list_):
            raise RuntimeError(f"hdu type {hdu_type} not in allowed {self._hdu_type_list_}")
    
    def _check_dict(self, d: dict):
        if not isinstance(d, dict):
            raise RuntimeError('object is not dict')


    @classmethod
    def from_fits_hdu(cls, hdu: FitsHDU, name=None):

        if name is None or name == '':
            name = hdu.name

        r = cls(data=hdu.data,
                data_header={k:v for k, v in hdu.header.items()},
                hdu_type=cls._map_hdu_type(hdu),name=name)
        # this is needed to re-read the file due to variable length file
        r.to_fits_hdu()
        return r


    def to_fits_hdu(self):
        try:

            logger.debug('------------------------------')
            logger.debug('inside to_fits_hdu methods')
            logger.debug(f'name: {self.name}')
            logger.debug(f'header: {self.header}')
            logger.debug(f'data: {repr(self.data)}')
            logger.debug(f'units_dict: {self.units_dict}')
            logger.debug(f'hdu_type: {self.hdu_type}')
            logger.debug('------------------------------')

            for k,v in self.header.items():
                if isinstance(v, list):
                    s=''
                    for el in v:
                        s+='%s,'%str(el)
                    
                    self.header[k] = s
                    #unicode(",".join(map(str,v)))

            return  self.new_hdu_from_data(
                self.data,
                header=pf.header.Header(self.header),
                hdu_type=self.hdu_type,
                units_dict=self.units_dict)
        
        except Exception as e:
            error_message = 'an exception occurred in oda_api when binary products are formatted to fits header: ' + repr(e)
            logger.error(error_message)
            logger.error('traceback: %s', traceback.format_exc())
            raise Exception("an exception occurred in oda_api when binary products are formatted to fits header") from e



    @staticmethod
    def _map_hdu_type(hdu: FitsHDU):
        _t=''
        if isinstance(hdu, pf.PrimaryHDU):
            _t= 'primary'
        elif isinstance(hdu, pf.ImageHDU):
            _t = 'image'
        elif isinstance(hdu, pf.BinTableHDU):
            _t = 'bintable'
        elif isinstance(hdu, pf.TableHDU):
            _t = 'table'
        else:
            raise RuntimeError('hdu type not understood')
        return _t

    def new_hdu_from_data(self, 
                          data: numpy.ndarray | None, 
                          hdu_type: str | None, 
                          header: Header | None = None, units_dict: dict | None = None):

        self._check_hdu_type(hdu_type)

        if hdu_type=='primary':
            h = pf.PrimaryHDU
        elif hdu_type=='image':
            h = pf.ImageHDU
        elif hdu_type == 'bintable':
            h = pf.BinTableHDU
        elif hdu_type == 'table':
            h = pf.TableHDU
        else:
            raise RuntimeError('hdu type ', hdu_type, 'not in allowed', self._hdu_type_list_)


        _h = h(data=data, header=header)
        _h.name = self.name
        if units_dict is not None:
            if isinstance(_h, pf.ImageHDU) or isinstance(_h, pf.PrimaryHDU):
                raise RuntimeError('units_dict is not None but hdu is not a table')

            for k in units_dict.keys():
                _h.columns.change_unit(k, units_dict[k]) # pyright: ignore[reportOptionalMemberAccess]

            self.header=dict(_h.header)
        return _h

    @staticmethod
    def _eval_dt(dt):
        try:
            dt = numpy.dtype(dt)
        except Exception:
            dt = eval(dt)
        return dt


    def encode(self,use_pickle=False,use_gzip=False,to_json=False):
        _data = []
        _meata_d=[]
        _kw_d = []
        _d = None
        _dt = None
        _binarys = None
        if self.data is not None:
            _dt= numpy_encode(numpy.array(self.data))['dtype']

            if use_pickle:
                if isinstance(self.data, FITS_rec):
                    pickled_data = pickle.dumps(self.data)
                else:
                    pickled_data = pickle.dumps(numpy.array(self.data))

                if use_gzip:
                    with BytesIO(pickled_data) as out_file:
                        with gzip.GzipFile(fileobj=out_file, mode='wb') as gzip_file:
                            gzip_file.write(pickled_data)
                            _binarys = base64.b64encode(out_file.getvalue())
                        
                else:
                    _binarys= base64.b64encode(
                        pickled_data
                    )

                _binarys = _binarys.decode()

            else:
                _d= json.dumps(self.data, cls=JsonCustomEncoder)


        _o_dict = {'data': _d,
                   'dt': _dt,
                   'name': self.name,
                   'header': self.header,
                   'binarys': _binarys,
                   'meta_data': self.meta_data,
                   'hdu_type': self.hdu_type,
                   'units_dict': self.units_dict}

        if to_json:
            _o_dict_json = json.dumps(_o_dict)
            return  _o_dict_json
        
        return _o_dict


    @classmethod
    def decode(cls, encoded_obj: str | dict, use_gzip=False, from_json=False):

        if not from_json:
            try:
                encoded_obj = json.loads(encoded_obj) # type: ignore
            except (json.JSONDecodeError, TypeError):
                pass
        
        encoded_obj = typing.cast(dict, encoded_obj) 

        encoded_data = encoded_obj['data']
        encoded_dt=encoded_obj['dt']
        encoded_header = encoded_obj['header']
        encoded_meta_data=encoded_obj['meta_data']
        _name=encoded_obj['name']
        _hdu_type=encoded_obj['hdu_type']
        _binarys=encoded_obj['binarys']
        _units_dict = encoded_obj.get('units_dict')

        if _binarys is not None:
            with BytesIO() as in_file:
                _binarys = base64.b64decode(_binarys)

                if use_gzip:
                    in_file.write(_binarys)
                    in_file.seek(0)

                    with gzip.GzipFile(fileobj=in_file, mode='rb') as gzip_file:
                        _data = gzip_file.read().decode('utf-8')
                        _data = pickle.loads(_data) # type: ignore
                        
                else:
                    _data = pickle.loads(_binarys, encoding='bytes')
            
        elif encoded_data is not None:
            encoded_data=eval(encoded_data) # !!

            for ID,c in enumerate(encoded_data):
                encoded_data[ID]=tuple(c)

            _data=numpy.asanyarray(encoded_data,dtype=cls._eval_dt(encoded_dt))

        else:
            _data=None

        if (isinstance(_data, FITS_rec) 
            and _hdu_type in ["table", "bintable"] 
            and getattr(_data, "_tbsize", None) is None):

            _data._tbsize = int(np.prod([encoded_header[f"NAXIS{i}"] for i in range(1, encoded_header['NAXIS']+1)]))

        return cls(data=_data, data_header=encoded_header, meta_data=encoded_meta_data,name=_name,hdu_type=_hdu_type, units_dict=_units_dict)

    @classmethod
    def from_pandas(cls, 
                    pandas_dataframe: pd.DataFrame, 
                    name: str | None = None, 
                    column_names: list | None = None, 
                    units_dict: dict | None = None, 
                    meta_data: dict | None = None,
                    data_header: dict | None = None):
        if data_header is None:
            data_header = {}
        if meta_data is None:
            meta_data = {}
        if units_dict is None:
            units_dict = {}
        if column_names is None:
            column_names = []
        if column_names and isinstance(column_names, list):
            pandas_dataframe = pandas_dataframe.loc[:, column_names]
        elif column_names and isinstance(column_names, dict):
            pandas_dataframe = pandas_dataframe.loc[:, column_names.keys()]
            pandas_dataframe.rename(columns=column_names, inplace=True)
        rec_array = pandas_dataframe.to_records(index=False)
        return cls(data = rec_array, 
                   name=name, 
                   units_dict = units_dict, 
                   meta_data = meta_data,
                   data_header = data_header,
                   hdu_type = 'bintable')
        


class NumpyDataProduct(DataProduct):
    def __init__(
        self,
        data_unit: NumpyDataUnit | list[NumpyDataUnit],
        name: str | None = None,
        meta_data: dict | None = None,
    ):

        if meta_data is None:
            meta_data = {}
        
        self.name=name

        self.data_unit=self._set_data(data_unit)
        self._check_dict(meta_data)
        self.meta_data=meta_data

    def suggest_fn_extension(self) -> str:
        return 'fits'

    def show(self):
        print('------------------------------')
        print('name:',self.name)
        print('meta_data',self.meta_data.keys())
        print ('number of data units',len(self.data_unit))
        print ('------------------------------')
        for ID,du in enumerate(self.data_unit):
            print('data uniti',ID,',name:',du.name)

    def show_meta(self):
        print('------------------------------')
        for k,v in self.meta_data.items():
            print(k,':',v)
        print ('------------------------------')


    def get_data_unit(self, ID: int) -> NumpyDataUnit:
        try:
            return self.data_unit[ID]
        except IndexError as e:
            raise RuntimeError(f"problem get_data_unit ID:{ID} in self.data_unit:{self.data_unit}") from e

    def get_data_unit_by_name(self, name: str) -> typing.Union[NumpyDataUnit, None]:
        _du = None

        du = None
        for du in self.data_unit:
            if du.name == name:
                if _du is not None:
                    logger.warning(f"get_data_unit_by_name found multiple du for name {name}")
                _du = du
            logger.info(f'--> NAME {du.name}')

        if _du is None:
            found_names = '; '.join([ str(_du.name) + ":" + repr(du) for _du in self.data_unit ])
            logger.warning(f"get_data_unit_by_name found no du for name {name}, have {found_names}")

        return _du

    def _set_data(self, data: NumpyDataUnit | list[NumpyDataUnit]):
        if isinstance(data, list):
            _dl = data
        else:
            _dl = [data]

        for _ID, _d  in enumerate(_dl):
            if not isinstance(_d, NumpyDataUnit):
                raise RuntimeError ('DataUnit not valid')
            
        return _dl

    def _chekc_enc_data(self, data):
        return _chekc_enc_data(data)

    def _check_dict(self, _kw: dict):
        if not isinstance(_kw, dict):
            raise RuntimeError('object is not not dict')

    def encode(self, use_pickle=True, use_gzip=False, to_json=False):
        _enc = []

        for _ID, data_unit in enumerate(self.data_unit):
            _enc.append(
                data_unit.encode(
                        use_pickle=use_pickle,
                        use_gzip=use_gzip
                    )
                )

        _o_dict={'data_unit_list':_enc,'name':self.name,'meta_data':dumps(self.meta_data)}

        if to_json:
            return json.dumps(_o_dict)

        return _o_dict

    def to_fits_hdu_list(self):
        _hdul=pf.HDUList()
        for _ID,_d in enumerate(self.data_unit):
            _hdul.append(_d.to_fits_hdu())
        return _hdul

    def write_fits_file(self, filename: str, overwrite=True):
        self.to_fits_hdu_list().writeto(filename, overwrite=overwrite)

    @classmethod
    def from_fits_file(
        cls,
        filename: str,
        ext: int | str | None = None,
        hdu_name: str | None = None,
        meta_data: dict | None = None,
        name: str = "",
    ):
        if meta_data is None:
            meta_data = {}

        hdul=pf.open(filename)
        if ext is not None:
            hdul = [hdul[ext]]

        if hdu_name is not None:
            _hdul = []
            for hdu in hdul:
                if hdu.name == hdu_name: # type: ignore
                    _hdul.append(hdu)

            hdul=_hdul

        return cls(data_unit=[NumpyDataUnit.from_fits_hdu(h) for h in  hdul],meta_data=meta_data,name=name) # pyright: ignore[reportArgumentType]
        

    @classmethod
    def decode(cls, encoded_obj: typing.Union[str, dict], from_json=False):
        
        if encoded_obj is not None:
            # from_json has the opposite meaning of what the name implies
            obj_dict: dict 
            if from_json:
                if isinstance(encoded_obj, dict):
                    obj_dict = encoded_obj
                else:
                    logger.warning('decoding from unexpected object')
                    obj_dict = encoded_obj # type: ignore
            else:
                if isinstance(encoded_obj, dict):
                    obj_dict = encoded_obj
                else:
                    logger.warning('decoding from unexpected object')
                    try:
                        obj_dict = json.loads(encoded_obj)
                    except Exception as e:
                        raise RuntimeError('unable to decode json object') from e 

            encoded_data_unit_list = obj_dict['data_unit_list']
            encoded_name = obj_dict['name']
            encoded_meta_data = obj_dict['meta_data']

            _data_unit_list=[]
            #print('encoded_data_unit_list',encoded_data_unit_list)
            for enc_data_unit in encoded_data_unit_list:
                _data_unit_list.append(NumpyDataUnit.decode(enc_data_unit,from_json=False))
        else:
            _data_unit_list=[]
            encoded_name=None
            encoded_meta_data={}

        if isinstance(encoded_meta_data, str):
            try:
                encoded_meta_data = json.loads(encoded_meta_data)
            except Exception:  # fallback if was not properly encoded, backward compatibility
                encoded_meta_data = eval(encoded_meta_data)

        return cls(data_unit=_data_unit_list,name=encoded_name,meta_data=encoded_meta_data)

    @classmethod
    def from_file(
        cls,
        filename: str,
        ext: int | str | None = None,
        hdu_name: str | None = None,
        meta_data: dict | None = None,
        name: str = "",
    ):
        return cls.from_fits_file(
            filename=filename,
            ext=ext, 
            hdu_name=hdu_name, 
            meta_data=meta_data, 
            name=name)
    
    def write_file(self, file_path, overwrite=True):
        self.write_fits_file(file_path, overwrite=overwrite)

class ApiCatalog(object):


    def __init__(self,cat_dict,name=None):
        self.name=name
        _skip_list=['meta_ID']
        meta = {}
        
        lon_name = None
        if 'cat_lon_name' in cat_dict.keys():
            lon_name =  cat_dict['cat_lon_name']

        lat_name = None
        if 'cat_lat_name' in cat_dict.keys():
            lat_name = cat_dict['cat_lat_name']

        frame = None
        if 'cat_frame' in cat_dict.keys():
            frame = cat_dict['cat_frame']

        coord_units = None
        if 'cat_coord_units' in cat_dict.keys():
            coord_units = cat_dict['cat_coord_units']

        if 'cat_meta' in cat_dict.keys():
            cat_meta_entry = cat_dict['cat_meta']
            meta.update(cat_meta_entry)
        
        meta['FRAME'] = frame
        meta['COORD_UNIT'] = coord_units
        meta['LON_NAME'] = lon_name
        meta['LAT_NAME'] = lat_name

        self.table =Table(cat_dict['cat_column_list'], names=cat_dict['cat_column_names'],meta=meta)

        if coord_units is not None:
            self.table[lon_name]=Angle(self.table[lon_name],unit=coord_units)
            self.table[lat_name]=Angle(self.table[lat_name],unit=coord_units)

        self.lat_name=lat_name
        self.lon_name=lon_name

    def get_api_dictionary(self ):
        column_lists = []
        for colname in self.table.colnames:
            column_lists.append([x if str(x) != 'nan' else None for x in self.table[colname]])
                                

        return json.dumps(dict(cat_frame=self.table.meta['FRAME'], # pyright: ignore[reportOptionalSubscript]
                    cat_coord_units=self.table.meta['COORD_UNIT'], # pyright: ignore[reportOptionalSubscript]
                    cat_column_list=column_lists,
                    cat_column_names=self.table.colnames,
                    cat_column_descr=self.table.dtype.descr,
                    cat_lat_name=self.lat_name,
                    cat_lon_name=self.lon_name))

class GWEventContours:
    def __init__(self, event_contour_dict, name='') -> None:
        self._contour_dict = event_contour_dict
        self.name = name
        self.levels = event_contour_dict['levels']
        self.contours = event_contour_dict['contours']
        
class GWContoursDataProduct:
    def __init__(self, contours_dict: dict) -> None:
        self._cont_data = contours_dict
        self.event_list = list(self._cont_data.keys())
        self.contours = {}
        for key, val in self._cont_data.items():
            self.contours[key] = GWEventContours(val, name = key)
            setattr(self, key, self.contours[key])
            
class LightCurveDataProduct(NumpyDataProduct):
    
    @classmethod
    def from_arrays(cls,
                    times, 
                    timedel = None,
                    fluxes = None,
                    magnitudes = None,
                    rates = None,
                    counts = None,
                    errors = None,
                    units_spec = None, # TODO: not used yet
                    time_format = None,
                    name = None):
        
        if units_spec is None:
            units_spec = {}
        data_header = {}
        meta_data = {} # meta data could be attached to both NumpyDataUnit and NumpyDataProduct. Decide on this
        
        if (fluxes is not None) + (magnitudes is not None) + (rates is not None) + (counts is not None) != 1:
            raise ValueError('Only one type of values should be set')
        elif fluxes is not None:
            col_name = 'FLUX'
            values = fluxes
        elif magnitudes is not None:
            col_name = 'MAG' 
            values = magnitudes
        elif rates is not None:
            col_name = 'RATE'
            values = rates
        elif counts is not None:
            col_name = 'COUNTS'
            values = counts
        else:
            raise ValueError('One of fluxes/magnitudes/rates/counts arguments is required')
        
        if len(values) != len(times):
            raise ValueError(f'Value column length {len(values)} do not coincide with time {len(times)} column length')
        if errors is not None and len(errors) != len(times):
            raise ValueError('Error column length do not coincide with time column length')
        
        # TODO: possibility for other time units
        # TODO: add time-related keywords to header (OGIP)
        units_dict = {'TIME': 'd'}
        if any(isinstance(x, aTime) for x in times):
            times = aTime(times)
                        
        if isinstance(times, aTime):
            mjd = times.mjd
        elif time_format is not None:
            atimes = aTime(times, format=time_format) # NOTE: do we assume paticular scale?
            mjd = atimes.mjd 
        else:
            atimes = aTime(times)
            mjd = atimes.mjd 
        
        if any(isinstance(x, u.Quantity) for x in values):
            values = u.Quantity(values)
        if isinstance(values, u.Quantity):
            units_dict[col_name] = values.unit.to_string(format='OGIP') # pyright: ignore[reportOptionalMemberAccess]
            values = values.value
            
        if errors is not None and any(isinstance(x, u.Quantity) for x in errors):
            errors = u.Quantity(errors)
        if errors is not None and isinstance(errors, u.Quantity):
            units_dict['ERROR'] = errors.unit.to_string(format='OGIP') # pyright: ignore[reportOptionalMemberAccess]
            errors = errors.value

        timedel_is_array = False
        if timedel is not None:
            # Accept scalar numeric (int/float), numpy scalar, or astropy Quantity
            if isinstance(timedel, u.Quantity):
                # convert timedel to days (internal TIME unit is 'd')
                td_days = timedel.to(u.day).value
            else:
                td_days = timedel
                
            if np.isscalar(td_days):
                # treat numeric scalar as days by default
                td_days = float(td_days) # pyright: ignore[reportArgumentType]
                data_header['TIMEDEL'] = td_days
            else:
                # If it's array-like, ensure it matches times length
                try:
                    if len(td_days) != len(times):
                        raise ValueError('timedel length must match times length when providing an array')
                    units_dict['TIMEDEL'] = 'd'
                    timedel = np.asarray(timedel)
                except TypeError as e:
                    raise ValueError('timedel type not understood; expected scalar, Quantity, or array-like') from e
        
        if timedel is None or timedel_is_array is False:
            rec_array = np.rec.fromarrays([mjd, values, errors], names=("TIME", col_name, "ERROR"))  # type:ignore
        else:
            rec_array = np.rec.fromarrays([mjd, values, errors, timedel], names=("TIME", col_name, "ERROR", "TIMEDEL"))  # type:ignore
        
        return cls([NumpyDataUnit(data=np.array([]), name = 'PRIMARY', hdu_type = 'primary'),
                    NumpyDataUnit(data = rec_array,
                                 units_dict = units_dict,
                                 meta_data = meta_data,
                                 data_header = data_header,
                                 hdu_type = 'bintable',
                                 name = 'LC')],
                   name = name)            


class PictureProduct(DataProduct):
    def __init__(self, binary_data, name=None, metadata=None, file_path=None, write_on_creation=False):
        if metadata is None:
            metadata = {}
        self.binary_data = binary_data
        self.metadata = metadata
        self.name = name
        if file_path is not None and os.path.isfile(file_path):
            self.file_path = file_path 
            logger.info(f'Image file {file_path} already exist. No automatical rewriting.')
        elif write_on_creation:
            self.write_file(file_path)
        else:
            self.file_path = None                        
        tp = puremagic.from_string(binary_data).lstrip('.')
        known_img = [t.lstrip('.') for t,v in mimetypes.types_map.items() if v.startswith('image')]
        if tp not in known_img:
            raise ValueError('Provided data is not an image')
        self.img_type = tp
    
    def suggest_fn_extension(self) -> str:
        return f'{self.img_type}'

    @classmethod
    def from_file(cls, file_path, name=None):
        with open(file_path, 'rb') as fd:
            binary_data = fd.read()
        return cls(binary_data, name=name, file_path=file_path)
            
    def write_file(self, file_path, overwrite=False):
        if os.path.isfile(file_path) and not overwrite:
            raise FileExistsError(f'File {file_path} already exists. Use overwrite=True')
        logger.info(f'Creating image file {file_path}.')
        with open(file_path, 'wb') as fd:
            fd.write(self.binary_data)
        self.file_path = file_path
    
    def encode(self):
        b64data = base64.urlsafe_b64encode(self.binary_data)
        output_dict = {}
        output_dict['img_type'] = self.img_type
        output_dict['b64data'] = b64data.decode()
        output_dict['metadata'] = self.metadata
        output_dict['name'] = self.name
        if self.file_path:
            output_dict['filename'] = os.path.basename(self.file_path)
        return output_dict
    
    @classmethod
    def decode(cls, encoded_data, write_on_creation = False):
        if isinstance(encoded_data, dict):
            _encoded_data = encoded_data
        else:
            _encoded_data = json.loads(encoded_data)
        binary_data = base64.urlsafe_b64decode(_encoded_data['b64data'].encode('ascii', 'ignore'))
        return cls(binary_data, 
                   metadata = _encoded_data['metadata'],
                   file_path = _encoded_data.get('filename'),
                   name = _encoded_data.get('name'),
                   write_on_creation = write_on_creation)
    
    def show(self):
        byte_stream = BytesIO(self.binary_data)
        image = mpimg.imread(byte_stream)
        plt.imshow(image)
        plt.axis('off')
        plt.show()
        
class ImageDataProduct(NumpyDataProduct):  
    @classmethod
    def from_fits_file(cls,filename,ext=None,hdu_name=None,meta_data=None,name=None):
        if meta_data is None:
            meta_data = {}
        npdp = super().from_fits_file(filename,ext=ext,hdu_name=hdu_name,meta_data=meta_data,name=name)

        contains_image = cls.check_contains_image(npdp)
        if contains_image:
            return npdp
        else:
            raise ValueError(f'FITS file {filename} doesn\'t contain image data.')
            
    @staticmethod
    def check_contains_image(numpy_data_prod):
        for hdu in numpy_data_prod.data_unit:
            if hdu.hdu_type in ['primary', 'image']:
                try:
                    WCS(hdu.header)
                    return True
                except Exception:
                    pass
                    
        return False
        
class TextLikeProduct(DataProduct):
    def __init__(self, value, name=None, meta_data=None):
        if meta_data is None:
            meta_data = {}
        self.value = value
        self.name = name
        self.meta_data = meta_data
        
    def encode(self):
        return {'name': self.name,
                'value': self.value,
                'meta_data': self.meta_data}
        
    @classmethod
    def decode(cls, encoded):
        if not isinstance(encoded, dict):
            encoded = json.loads(encoded)
        return cls(name=encoded.get('name'), 
                   value=encoded['value'],
                   meta_data=encoded.get('meta_data', {}))
        
    def __repr__(self):
        return self.encode().__repr__()

    def write_file(self, file_path, overwrite=True):
        if os.path.isfile(file_path) and not overwrite:
            raise FileExistsError(f"File {file_path} already exists")
        with open(file_path, 'w') as fd:
            fd.write(self.value)
    
    @classmethod
    def from_file(cls, file_path: str, name: str | None = None, meta_data: dict | None = None) -> DataProduct:
        with open(file_path, 'r') as fd:
            value = fd.read()
        return cls(name=name, value=value, meta_data=meta_data)
    
    def suggest_fn_extension(self) -> str:
        return 'txt'

