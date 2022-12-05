from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)

__author__ = "Andrea Tramacere"

# Standard library
# eg copy
# absolute import rg:from copy import deepcopy

# Dependencies
# eg numpy
# absolute import eg: import numpy as np

# Project
# relative import eg: from .mod import f

import typing

from json_tricks import numpy_encode,dumps,loads,numeric_types_hook,hashodict,json_numpy_obj_hook
from astropy.io import fits as pf
from astropy.io import ascii as astropy_io_ascii
import json
from astropy.utils.misc import JsonCustomEncoder

from astropy.table import Table
from astropy.coordinates import Angle
from astropy.wcs import WCS

import  numpy
import numpy as np
import  base64
import  pickle
import gzip
import  hashlib
from numpy import nan,inf
from sys import path_importer_cache, version_info

from io import StringIO, BytesIO
import imghdr
import os
import logging
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

logger = logging.getLogger('oda_api.data_products')

__all__=['sanitize_encoded','_chekc_enc_data','BinaryData','NumpyDataUnit','NumpyDataProduct','ApiCatalog','ODAAstropyTable']

import astropy.io.fits.fitsrec


# these 3 functions are remnants of misusing repr() to serialize data instead of json
def sanitize_encoded(d):
    d = d.replace('null', 'None')
    d = d.replace('true', 'True')
    d = d.replace('false', 'False')
    d = d.replace('NaN', 'nan')
    d = d.replace('Infinity', 'inf')
    return d

def json_to_literal(d):
    d = d.replace('null', 'None')
    d = d.replace('true', 'True')
    d = d.replace('false', 'False')
    d = d.replace('NaN', 'nan')
    d = d.replace('Infinity', 'inf')
    return d

def literal_to_json(d):
    d = d.replace('None', 'null')
    d = d.replace('True', 'true')
    d = d.replace('False', 'false')
    d = d.replace('nan', 'NaN')
    d = d.replace('inf', 'Infinity')
    return d


def _chekc_enc_data(data):
    if type(data)==list:
        _l=data
    else:
        _l=[data]

    return _l

# not used?
class ODAAstropyTable(object):

    def __init__(self,table_object,name='astropy table', meta_data={}):
        self.name=name
        self.meta_data=meta_data
        self._table=table_object

    @property
    def table(self):
        return self._table

    def write(self,file_name,format='fits',overwrite=True):
        self._table.write(file_name,format=format,overwrite=overwrite)

    def write_fits_file(self,file_name,overwrite=True):
        self.write(file_name,overwrite=overwrite,format='fits')

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

        return cls(table, meta_data=meta)

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

        if to_json == True:
            _o_dict=json.dumps(_o_dict)
        return   _o_dict

    @classmethod
    def decode(cls,o_dict,use_binary=False):
        if isinstance(o_dict, dict):
            _o_dict = o_dict
        elif isinstance(o_dict, str):
            _o_dict = json.loads(literal_to_json(o_dict))
        encoded_name = _o_dict['name']
        encoded_meta_data = _o_dict['meta_data']
        if use_binary is True:
            t_rec = base64.b64decode(_o_dict['binary'])
            try:
                t_rec = pickle.loads(t_rec)
            except:
                t_rec= pickle.loads(t_rec,encoding='latin')

        else:
            t_rec = astropy_io_ascii.read(_o_dict['ascii'])

        return cls(t_rec,name=encoded_name,meta_data=encoded_meta_data)


class BinaryData(object):

    def __init__(self,file_path=None):
        self.file_path=file_path

    def encode(self,file_path=None):
        if file_path==None:
            file_path=self.file_path
        _file_binary = open(file_path, 'rb').read()
        _file_b64 = base64.urlsafe_b64encode(_file_binary)
        _file_b64_md5 = hashlib.md5(_file_binary).hexdigest()

        return _file_b64,_file_b64_md5

    def decode(self,encoded_obj):
        return base64.urlsafe_b64decode(encoded_obj.encode('ascii', 'ignore'))


class NumpyDataUnit(object):

    def __init__(self, data, data_header={}, meta_data={}, hdu_type=None, name='table', units_dict=None):
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


    def _check_data(self,data):
        if isinstance(data, numpy.ndarray) or data is None:
            pass
        else:
            raise RuntimeError('data is not numpy ndarray object')

    def _check_hdu_type(self,hdu_type):
        if hdu_type is None:
            pass
        elif hdu_type in self._hdu_type_list_:
            pass
        else:
            raise RuntimeError('hdu type ', hdu_type, 'not in allowed', self._hdu_type_list_)
    
    def _check_dict(self,_kw):

        if isinstance(_kw, dict):
            pass
        else:
            raise RuntimeError('object is not not dict')


    @classmethod
    def from_fits_hdu(cls,hdu,name=''):

        if name=='':
            name=hdu.name

        return cls(data=hdu.data,
                   data_header={k:v for k, v in hdu.header.items()},
                   hdu_type=cls._map_hdu_type(hdu),name=name)


    def to_fits_hdu(self):
        try:
            for k,v in self.header.items():
                if isinstance(v, list):
                    s=''
                    for l in v:
                        s+='%s,'%str(l)
                    
                    self.header[k] = s
                    #unicode(",".join(map(str,v)))

            return  self.new_hdu_from_data(self.data,
                                    header=pf.header.Header(self.header),
                                    hdu_type=self.hdu_type,units_dict=self.units_dict)
        except Exception as e:
            raise Exception("the platfrom encourntered a bug which happens when ScW list is sent as a file; we are working on it! raw message: "+repr(e))



    @staticmethod
    def _map_hdu_type(hdu):
        _t=''
        if isinstance(hdu,pf.PrimaryHDU):
            _t= 'primary'
        elif isinstance(hdu,pf.ImageHDU):
            _t = 'image'
        elif isinstance(hdu, pf.BinTableHDU):
            _t = 'bintable'
        elif isinstance(hdu, pf.TableHDU):
            _t = 'table'
        else:
            raise RuntimeError('hdu type not understood')
        #print('_t',_t)
        return _t

    def new_hdu_from_data(self,data,hdu_type, header=None,units_dict=None):

        self._chekc_hdu_type(hdu_type)

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


        _h=h(data=data, header=header)
        _h.name=self.name
        if units_dict is not None:

            for k in units_dict.keys():
                _h.columns.change_unit(k,units_dict[k])
            self.header=dict(_h.header)
        return _h

    @staticmethod
    def _eval_dt(dt):
        #print('dt', type(dt), dt)
        try:
            dt = numpy.dtype(dt)

        except:

            dt = eval(dt)
        #print('dt', type(dt), dt)
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

            if use_pickle is True:

                if isinstance(self.data, astropy.io.fits.fitsrec.FITS_rec):
                    pickled_data = pickle.dumps(self.data)
                else:
                    pickled_data = pickle.dumps(numpy.array(self.data))

                if use_gzip==True:
                    out_file = StringIO(pickled_data)
                    gzip_file = gzip.GzipFile(fileobj=out_file, mode='wb')

                    gzip_file.write(pickled_data)
                    _binarys = base64.b64encode(out_file.getvalue())
                    gzip_file.close()
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
    def decode(cls,encoded_obj,use_gzip=False,from_json=False):
        #encoded_obj=eval(encoded_obj)
        #encoded_obj=json.loads(encoded_obj)
        #print('-->encoded_obj',type(encoded_obj))

        if from_json == False:
            try:
                encoded_obj = json.loads(encoded_obj)
            except:
                pass

        encoded_data = encoded_obj['data']
        encoded_dt=encoded_obj['dt']
        encoded_header = encoded_obj['header']
        encoded_meta_data=encoded_obj['meta_data']
        _name=encoded_obj['name']
        _hdu_type=encoded_obj['hdu_type']
        _binarys=encoded_obj['binarys']
        _units_dict = encoded_obj.get('units_dict')

        if _binarys is not None:
            #print('dec ->', type(_binarys))
            in_file = StringIO()
            _binarys = base64.b64decode(_binarys)

            if use_gzip ==True:
                in_file.write(_binarys)
                in_file.seek(0)

                gzip_file = gzip.GzipFile(fileobj=in_file, mode='rb')
                _data = gzip_file.read()
                _data = _data.decode('utf-8')
                _data = pickle.loads(_data)
                gzip_file.close()
            else:
                if version_info[0] > 2:
                    _data = pickle.loads(_binarys,encoding='bytes')
                else:
                    _data = pickle.loads(_binarys)

        elif encoded_data is not None:
            encoded_data=eval(encoded_data) # !!

            for ID,c in enumerate(encoded_data):
                encoded_data[ID]=tuple(c)

            _data=numpy.asanyarray(encoded_data,dtype=cls._eval_dt(encoded_dt))

        else:
            _data=None



        return cls(data=_data, data_header=encoded_header, meta_data=encoded_meta_data,name=_name,hdu_type=_hdu_type, units_dict=_units_dict)

    @classmethod
    def from_pandas(cls, 
                    pandas_dataframe, 
                    name = 'table', 
                    column_names=[], 
                    units_dict={}, 
                    meta_data = {},
                    data_header = {}):
        if column_names and type(column_names) == list:
            pandas_dataframe = pandas_dataframe.loc[:, column_names]
        elif column_names and type(column_names) == dict:
            pandas_dataframe = pandas_dataframe.loc[:, column_names.keys()]
            pandas_dataframe.rename(columns=column_names, inplace=True)
        rec_array = pandas_dataframe.to_records(index=False)
        return cls(data = rec_array, 
                   name=name, 
                   units_dict = units_dict, 
                   meta_data = meta_data,
                   data_header = data_header,
                   hdu_type = 'bintable')
        


class NumpyDataProduct(object):

    def __init__(self, data_unit, name='', meta_data={}):

        self.name=name

        self.data_unit=self._seta_data(data_unit)
        self._chekc_dict(meta_data)
        self.meta_data=meta_data


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
            raise RuntimeError(f"problem get_data_unit ID:{ID} in self.data_unit:{self.data_unit}")

    def get_data_unit_by_name(self, name: str) -> typing.Union[NumpyDataUnit, None]:
        _du = None

        for du in self.data_unit:
            if du.name == name:
                if _du is not None:
                    print(f"\033[31mWARNING: get_data_unit_by_name found multiple du for name {name}\033[0m")
                _du = du
            print('--> NAME',du.name)

        if _du is None:
            found_names = '; '.join([ str(_du.name) + ":" + repr(du) for _du in self.data_unit ])
            print(f"\033[31mWARNING: get_data_unit_by_name found no du for name {name}, have {found_names}\033[0m")

        return _du

    def _seta_data(self,data):
        if type(data) == list:
            _dl = data
        else:
            _dl = [data]

        for ID, _d  in enumerate(_dl):
            if isinstance(_d, NumpyDataUnit):
                pass
            else:
                raise RuntimeError ('DataUnit not valid')


        return _dl

    def _chekc_enc_data(self,data):
        return _chekc_enc_data(data)

    def _chekc_dict(self,_kw):

        if isinstance(_kw, dict):
            pass
        else:
            raise RuntimeError('object is not not dict')




    def encode(self, use_pickle=True, use_gzip=False, to_json=False):
        _enc = []

        for ID, data_unit in enumerate(self.data_unit):
            _enc.append(
                data_unit.encode(
                        use_pickle=use_pickle,
                        use_gzip=use_gzip
                    )
                )

        _o_dict={'data_unit_list':_enc,'name':self.name,'meta_data':dumps(self.meta_data)}

        if to_json==True:
            return json.dumps(_o_dict)

        return _o_dict




    def to_fits_hdu_list(self):
        _hdul=pf.HDUList()
        for ID,_d in enumerate(self.data_unit):
            _hdul.append(_d.to_fits_hdu())
        return _hdul


    def write_fits_file(self,filename,overwrite=True):

        self.to_fits_hdu_list().writeto(filename,overwrite=overwrite)



    @classmethod
    def from_fits_file(cls,filename,ext=None,hdu_name=None,meta_data={},name=''):
        hdul=pf.open(filename)
        if ext is not None:
            hdul=[hdul[ext]]

        if hdu_name is not None:
            _hdul=[]
            for hdu in hdul:
                if hdu.name == hdu_name:
                    _hdul.append(hdu)
            hdul=_hdul

        return cls(data_unit=[NumpyDataUnit.from_fits_hdu(h) for h in  hdul],meta_data=meta_data,name=name)

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
                        obj_dict = json.loads(literal_to_json(encoded_obj))
                    except Exception as e:
                        logger.debug('unable to decode json object: %s', e)                    
                        # why not raise here?                

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

        return cls(data_unit=_data_unit_list,name=encoded_name,meta_data=eval(encoded_meta_data))



class ApiCatalog(object):


    def __init__(self,cat_dict,name='catalog'):
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


        column_lists=[self.table[name].tolist() for name in self.table.colnames]
        for ID,_col in enumerate(column_lists):
            column_lists[ID] = [x if str(x)!='nan' else None for x in _col]

        return json.dumps(dict(cat_frame=self.table.meta['FRAME'],
                    cat_coord_units=self.table.meta['COORD_UNIT'],
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
                    fluxes = None,
                    magnitudes = None,
                    rates = None,
                    counts = None,
                    errors = None,
                    units_spec = {}, # TODO: not used yet
                    time_format = None,
                    name = 'lightcurve'):
        
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
        
        if len(values) != len(times):
            raise ValueError(f'Value column length {len(values)} do not coincide with time {len(times)} column length')
        if errors is not None and len(errors) != len(times):
            raise ValueError('Error column length do not coincide with time column length')
        
        # TODO: possibility for other time units
        # TODO: add time-related keywords to header (OGIP)
        units_dict = {'TIME': 'd'}
        if any(isinstance(x, astropy.time.Time) for x in times):
            times = astropy.time.Time(times)
                        
        if isinstance(times, astropy.time.Time):
            mjd = times.mjd
        elif time_format is not None:
            atimes = astropy.time.Time(times, format=time_format) # NOTE: do we assume paticular scale?
            mjd = atimes.mjd 
        else:
            atimes = astropy.time.Time(times)
            mjd = atimes.mjd 
        
        if any(isinstance(x, astropy.units.Quantity) for x in values):
            values = astropy.units.Quantity(values)
        if isinstance(values, astropy.units.Quantity):
            units_dict[col_name] = values.unit.to_string(format='OGIP')
            values = values.value
            
        if errors is not None and any(isinstance(x, astropy.units.Quantity) for x in errors):
            errors = astropy.units.Quantity(errors)
        if errors is not None and isinstance(errors, astropy.units.Quantity):
            units_dict['ERROR'] = errors.unit.to_string(format='OGIP')
            errors = errors.value
            
        rec_array = np.core.records.fromarrays([mjd, values, errors], names=('TIME', col_name, 'ERROR'))
        
        return cls([NumpyDataUnit(data=np.array([]), name = 'PRIMARY', hdu_type = 'primary'),
                    NumpyDataUnit(data = rec_array,
                                 units_dict = units_dict,
                                 meta_data = meta_data,
                                 data_header = data_header,
                                 hdu_type = 'bintable',
                                 name = 'LC')],
                   name = name)            

class PictureProduct:
    def __init__(self, binary_data, metadata={}, file_path=None, write_on_creation = False):
        self.binary_data = binary_data
        self.metadata = metadata
        if file_path is not None and os.path.isfile(file_path):
            self.file_path = file_path 
            logger.info(f'Image file {file_path} already exist. No automatical rewriting.')
        elif write_on_creation:
            self.write_file(file_path)
        else:
            self.file_path = None                        
        byte_stream = BytesIO(binary_data)
        tp = imghdr.what(byte_stream)
        if tp is None:
            raise ValueError('Provided data is not an image')
        self.img_type = tp
    
    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'rb') as fd:
            binary_data = fd.read()
        return cls(binary_data, file_path=file_path)
            
    def write_file(self, file_path):
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
                   write_on_creation = write_on_creation)
    
    def show(self):
        byte_stream = BytesIO(self.binary_data)
        image = mpimg.imread(byte_stream)
        plt.imshow(image)
        plt.axis('off')
        plt.show()
        
class ImageDataProduct(NumpyDataProduct):  
    @classmethod
    def from_fits_file(cls,filename,ext=None,hdu_name=None,meta_data={},name=''):
        npdp = super().from_fits_file(filename,ext=None,hdu_name=None,meta_data={},name='')

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
                    wcs = WCS(hdu.header)
                    return True
                except:
                    pass
        return False
        