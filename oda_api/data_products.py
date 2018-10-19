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
#import jsonpickle
# must
import  numpy






def sanitize_encoded(d):
    d = d.replace('null', 'None')
    d = d.replace('true', 'True')
    d = d.replace('false', 'False')
    return d



def _chekc_enc_data(data):
    if type(data)==list:
        _l=data
    else:
        _l=[data]

    return _l











class NumpyDataUnit(object):

    def __init__(self,data,data_header={},meta_data={},hdu_type='',name=''):
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


    def encode(self):

        _data = []
        _meata_d=[]
        _kw_d = []
        if self.data is not None:
            print(self.data[0])
            _dt= numpy_encode(numpy.array(self.data)  )['dtype']
            _d= json.dumps(self.data, cls=JsonCustomEncoder)
            #print(_d)
            print('enc dtype', _dt)
            #_d = numpy_encode(self.data)
            #print('encoded', _d['__ndarray__'])
            #print('encoded', dumps(_d['__ndarray__']))
        else:

          _d = None
          _dt=None
        return dumps({'data': _d,
                      'dt':_dt,
                      'name': self.name,
                      'header': self.header,
                      'meta_data': self.meta_data,
                      'hdu_type': self.hdu_type})


    @classmethod
    def from_json(cls,encoded_obj):
        print ('--- decoding')
        encoded_obj=eval(encoded_obj)
        #print(type(encoded_obj),encoded_obj.keys())
        encoded_data = encoded_obj['data']
        encoded_dt=encoded_obj['dt']
        encoded_header = encoded_obj['header']
        encoded_meta_data=encoded_obj['meta_data']
        _name=encoded_obj['name']
        _hdu_type=encoded_obj['hdu_type']


        if encoded_data is not None:
            #print('_name', encoded_data['dtype'])
            #_#data=pickle.loads(encoded_data)
            #print('encoded_data',type(encoded_data),c encoded_data['dtype'#)
            #encoded_data=eval(encoded_data)
            #print (type(encoded_data['__ndarray__']))
            encoded_data=eval(encoded_data)
            print('dec dtype', cls._eval_dt(encoded_dt))
            for ID,c in enumerate(encoded_data):
                encoded_data[ID]=tuple(c)
            ##print(encoded_dt)
            #print(encoded_data['__ndarray__'])
            _data=numpy.asanyarray(encoded_data,dtype=cls._eval_dt(encoded_dt))
            #_data=loads(encoded_data)

            #print('_data shape',encoded_data['__ndarray__'],cls._eval_dt(encoded_data['dtype']))
            #d1=json_numpy_obj_hook(encoded_data)
            #print(_data[0])
        else:
            _data=None



        return cls(data=_data, data_header=encoded_header, meta_data=encoded_meta_data,name=_name,hdu_type=_hdu_type)



class NumpyDataProduct(object):

    def __init__(self,data_uint,name='',meta_data={}):

        self.name=name

        self.data_uint=self._seta_data(data_uint)
        self._chekc_dict(meta_data)
        self.meta_data=meta_data


    def show(self):
        print('------------------------------')
        print('name:',self.name)
        print('meta_data',self.meta_data.keys())
        print ('number of data units',len(self.data_uint))
        print ('------------------------------')
        for ID,du in enumerate(self.data_uint):
            print('data uniti',ID,',name:',du.name)

    def show_meta(self):
        print('------------------------------')
        for k,v in self.meta_data.items():
            print(k,':',v)
        print ('------------------------------')


    def get_data_unit(self,ID   ):
        return self.data_uint[ID]

    def get_data_unit_by_name(self,name):
        for du in self.data_uint:
            if du.name == name:
               return (du)

        return None

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




    def encode(self):
        _enc=[]
        print('enc start')
        for ID, ed in enumerate(self.data_uint):
            print('data_uint',ID)
            _enc.append(self.data_uint[ID].encode())
        print ('enc done')
        return dumps({'data_unit_list':_enc,'name':self.name,'meta_data':dumps(self.meta_data)})




    def to_fits_hdu_list(self):
        _hdul=pf.HDUList()
        for ID,_d in enumerate(self.data_uint):
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

        return cls(data_uint=[NumpyDataUnit.from_fits_hdu(h) for h in  hdul],meta_data=meta_data,name=name)

    @classmethod
    def from_json(cls,encoded_obj):
        encoded_obj = eval(sanitize_encoded(encoded_obj))

        encoded_data_unit_list = encoded_obj['data_unit_list']
        encoded_name = encoded_obj['name']
        encoded_meta_data = encoded_obj['meta_data']

        _data_unit_list=[]
        #print('encoded_data_unit_list',encoded_data_unit_list)
        for enc_data_unit in encoded_data_unit_list:
            _data_unit_list.append(NumpyDataUnit.from_json(enc_data_unit))




        return cls(data_uint=_data_unit_list,name=encoded_name,meta_data=eval(encoded_meta_data))


