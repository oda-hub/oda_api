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

from json_tricks import numpy_encode,dumps,loads,numeric_types_hook,hashodict,json_numpy_obj_hook
from astropy.io import fits as pf
import json
from astropy.utils.misc import JsonCustomEncoder

import  numpy
import  base64
import  pickle
import gzip
import  hashlib
from numpy import nan,inf
from sys import version_info
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

def sanitize_encoded(d):
    d = d.replace('null', 'None')
    d = d.replace('true', 'True')
    d = d.replace('false', 'False')
    d = d.replace('NaN', 'nan')
    d = d.replace('Infinity', 'inf')
    return d



def _chekc_enc_data(data):
    if type(data)==list:
        _l=data
    else:
        _l=[data]

    return _l







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

    def __init__(self,data,data_header={},meta_data={},hdu_type=None,name='table'):
        self._hdu_type_list_ = ['primary', 'image', 'table', 'bintable']

        self.name=name
        self._chekc_data(data)
        self._chekc_hdu_type(hdu_type)
        self._chekc_dict(data_header)
        self._chekc_dict(meta_data)

        self.data=data
        self.header=data_header
        self.meta_data=meta_data
        self.hdu_type=hdu_type


    def _chekc_data(self,data):


        if isinstance(data, numpy.ndarray) or data is None:
            pass
        else:
            raise RuntimeError('data is not numpy ndarray object')

    def _chekc_hdu_type(self,hdu_type):
        if hdu_type is None:
            pass
        elif hdu_type in self._hdu_type_list_:
            pass
        else:
            raise RuntimeError('hdu type ', hdu_type, 'not in allowed', self._hdu_type_list_)



    def _chekc_dict(self,_kw):

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


         return  self.new_hdu_from_data(self.data,
                                header=pf.header.Header(self.header),
                                hdu_type=self.hdu_type)



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

    def new_hdu_from_data(self,data,hdu_type, header=None):

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

        return h(data=data, header=header)

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

                if use_gzip==True:
                    print ('gizziping')
                    out_file = StringIO()
                    gzip_file = gzip.GzipFile(fileobj=out_file, mode='wb')


                    gzip_file.write(pickle.dumps(numpy.array(self.data)))
                    _binarys = base64.b64encode(out_file.getvalue())
                    gzip_file.close()
                else:
                    _binarys= base64.b64encode(pickle.dumps(numpy.array(self.data),2))


            else:
                _d= json.dumps(self.data, cls=JsonCustomEncoder)


        _o_dict = {'data': _d,
                   'dt': _dt,
                   'name': self.name,
                   'header': self.header,
                   'binarys': _binarys,
                   'meta_data': self.meta_data,
                   'hdu_type': self.hdu_type}

        if to_json == True:
            _o_dict=json.dump(_o_dict)

        return   _o_dict


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

        if _binarys is not None:
            #print('dec ->', type(_binarys))
            in_file = StringIO()
            if version_info[0] > 2:
                _binarys=base64.b64decode(_binarys)

            else:
                _binarys = base64.decodestring(_binarys)

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
                    _data=pickle.loads(_binarys,encoding='bytes')
                else:
                    _data = pickle.loads(_binarys)

        elif encoded_data is not None:
            #print('using JsonCustomEncoder')
            encoded_data=eval(encoded_data)

            for ID,c in enumerate(encoded_data):
                encoded_data[ID]=tuple(c)

            _data=numpy.asanyarray(encoded_data,dtype=cls._eval_dt(encoded_dt))

        else:
            _data=None



        return cls(data=_data, data_header=encoded_header, meta_data=encoded_meta_data,name=_name,hdu_type=_hdu_type)



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


    def get_data_unit(self,ID   ):
        return self.data_unit[ID]

    def get_data_unit_by_name(self,name):
        _du=None
        for du in self.data_unit:
            if du.name == name:

                _du=du
            print('--> NAME',du.name)

        #TODO raise RuntimeError if _du is None

        return _du

    def _seta_data(self,data):
        if type(data) == list:
            _dl = data
        else:
            _dl = [data]

        for ID,_d  in enumerate(_dl):
            if isinstance(_d,NumpyDataUnit):
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




    def encode(self,use_pickle=True,use_gzip=False,to_json=False):
        _enc=[]
        #print('use_gzip',use_gzip)
        for ID, ed in enumerate(self.data_unit):
            #print('data_unit',ID)
            _enc.append(self.data_unit[ID].encode(use_pickle=use_pickle,use_gzip=use_gzip))
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
    def decode(cls,encoded_obj,from_json=False):
        if encoded_obj is not None:
            if from_json==False:
                try:
                    encoded_obj = json.loads(sanitize_encoded(encoded_obj))
                except:
                    pass

            encoded_data_unit_list = encoded_obj['data_unit_list']
            encoded_name = encoded_obj['name']
            encoded_meta_data = encoded_obj['meta_data']

            _data_unit_list=[]
            #print('encoded_data_unit_list',encoded_data_unit_list)
            for enc_data_unit in encoded_data_unit_list:
                _data_unit_list.append(NumpyDataUnit.decode(enc_data_unit,from_json=False))
        else:
            _data_unit_list=[]
            encoded_name=None
            encoded_meta_data={}



        return cls(data_unit=_data_unit_list,name=encoded_name,meta_data=eval(encoded_meta_data))


