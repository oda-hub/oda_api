
from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)


__author__ = "Andrea Tramacere"

import  warnings
import requests
import ast
import json
import random
import string
import time
import os
import inspect
import sys
from astropy.io import ascii
import base64
import  copy
import pickle

from itertools import cycle

from .data_products import NumpyDataProduct,BinaryData,ApiCatalog

__all__=['Request','NoTraceBackWithLineNumber','NoTraceBackWithLineNumber','RemoteException','DispatcherAPI']

class Request(object):
    def __init__(self,):
        pass


class NoTraceBackWithLineNumber(Exception):
    def __init__(self, msg):
        try:
            ln = sys.exc_info()[-1].tb_lineno
        except AttributeError:
            ln = inspect.currentframe().f_back.f_lineno
        self.args = "{0.__name__} (line {1}): {2}".format(type(self), ln, msg),
        sys.exit(self)


class NoTraceBackWithLineNumber(NoTraceBackWithLineNumber):
    pass


class RemoteException(NoTraceBackWithLineNumber):

    def __init__(self, message='Remote analysis exception', debug_message=''):
        super(RemoteException, self).__init__(message)
        self.message=message
        self.debug_message=debug_message


def safe_run(func):

    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
           message =  'the remote server response is not valid\n'
           message += 'possible causes: \n'
           message += '- connection error\n'
           message += '- wrong credentials\n'
           message += '- error on the remote server\n'
           message += '\n exception message: '
           message += '%s'%e
           raise RemoteException(message=message)

    return func_wrapper

class DispatcherAPI(object):
    def __init__(self,instrument='mock',host='www.astro.unige.ch/cdci/astrooda/dispatch-data',port=None,cookies=None,protocol='https'):

        self.host=host
        self.port=port
        self.cookies=cookies
        self.set_instr(instrument)

        if self.host.startswith('htt'):
            self.url=host
        else:
            if protocol=='http':
                self.url= "http://%s"%(host)
            elif protocol=='https':
                self.url = "https://%s" % (host)
            else:
                raise  RuntimeError('protocol must be either http or https')

        if port is not None:
            self.url += ":%d" % (port)

        self._progress_iter = cycle(['|', '/', '-', '\\'])

    @classmethod
    def build_from_envs(cls):
        cookies_path = os.environ.get('ODA_API_TOKEN')
        cookies = dict(_oauth2_proxy=open(cookies_path).read().strip())
        host_url = os.environ.get('DISP_URL')

        return cls(host=host_url, instrument='mock', cookies=cookies, protocol='http')

    def generate_session_id(self,size=16):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    def set_instr(self,instrument):
        self.instrument=instrument



    def _progess_bar(self,info=''):
        print("\r %s the job is working remotely, please wait %s"%(next(self._progress_iter),info),end='')

    @safe_run
    def request(self,parameters_dict,handle='run_analysis',url=None):
        if 'scw_list' in parameters_dict.keys():
            print (parameters_dict['scw_list'])

        if url is None:
            url=self.url
        parameters_dict['api']='True'
        print('- waiting for remote response, please wait',handle,url)
        for k in parameters_dict.keys():
            print(k,parameters_dict[k])

        res= requests.get("%s/%s" %(url, handle), params=parameters_dict,cookies=self.cookies)
        query_status = res.json()['query_status']
        job_id = res.json()['job_monitor']['job_id']

        if query_status != 'done' and query_status != 'failed':
            print ('the job has been submitted on the remote server')

        while query_status != 'done' and query_status != 'failed':
            parameters_dict['query_status']=query_status
            parameters_dict['job_id'] = job_id
            res = requests.get("%s/%s" % (url,handle), params=parameters_dict,cookies=self.cookies)
            query_status =res.json()['query_status']
            job_id = res.json()['job_monitor']['job_id']
            info='status=%s - job_id=%s '%(query_status,job_id)
            self._progess_bar(info=info)


            time.sleep(2)

        print("\r", end="")
        print('')
        print('')
        if  res.json()['exit_status']['status']!=0:
            self.failure_report(res)


        #print('job_monitor', res.json()['job_monitor'])
        #print('query_status', res.json()['query_status'])
        #print('products', res.json()['products'].keys())

        if query_status != 'failed':

            print('query done succesfully!')
        else:

            raise RemoteException(debug_message=res.json()['exit_status']['error_message'])



        return res


    def failure_report(self,res):
        print('query failed!')
        #print('exit_status, status', res.json()['exit_status']['status'])
        print('Remote server message:->', res.json()['exit_status']['message'])
        print('Remote server error_message->', res.json()['exit_status']['error_message'])
        print('Remote server debug_message->', res.json()['exit_status']['debug_message'])

    def dig_list(self,b,only_prod=False):
        from astropy.table import Table
        #print ('start',type(b))
        if isinstance(b, (set, tuple, list)):
            for c in b:
                self.dig_list(c)
        else:
            #print('not list',type(b))
            try:
                b = ast.literal_eval(str(b))
                #print('b literal eval',(type(b)))
            except:
                #print ('b exception' ,b,type(b))
                return str(b)
            if isinstance(b, dict):
                #print('dict',b)
                _s = ''
                for k, v in b.items():

                    if 'query_name' == k or 'instrumet' == k and only_prod==False:
                        print('')
                        print('--------------')
                        _s += '%s' % k + ': ' + v
                    if 'product_name' == k :
                        _s += ' %s' % k + ': ' + v

                for k in ['name', 'value', 'units']:
                    if k in b.keys():
                        _s += ' %s' % k + ': '
                        if b[k] is not None:
                            _s += '%s,' % str(b[k])
                        else:
                            _s += 'None,'
                        _s += ' '
                #if 'prod_dict' in b.keys():
                #    print ('product dict',b)

                if _s != '':
                    print(_s)
            else:
                #print('no dict', type(b))
                self.dig_list(b)

    @safe_run
    def _decode_res_json(self,res):
        try:
            if hasattr(res,'content'):
                #_js = json.loads(res.content)
                #fixed issue with python 3.5
                _js = res.json()
                res = ast.literal_eval(str(_js).replace('null', 'None'))
            else:
                res = ast.literal_eval(str(res).replace('null', 'None'))

            self.dig_list(res)
            return res
        except Exception as e:
            raise RemoteException(message='remote/connection error, server response is not valid, check your credentials and connection status')

    @safe_run
    def get_instrument_description(self,instrument=None):
        if instrument is None:
            instrument=self.instrument

        res=requests.get("%s/api/meta-data"%self.url,params=dict(instrument=instrument),cookies=self.cookies)
        self._decode_res_json(res)

    @safe_run
    def get_product_description(self,instrument,product_name):
        res = requests.get("%s/api/meta-data" % self.url, params=dict(instrument=instrument,product_type=product_name),cookies=self.cookies)

        print('--------------')
        print ('parameters for  product',product_name,'and instrument',instrument)
        self._decode_res_json(res)

    @safe_run
    def get_instruments_list(self):
        #print ('instr',self.instrument)
        res = requests.get("%s/api/instr-list" % self.url,params=dict(instrument=self.instrument),cookies=self.cookies)
        return self._decode_res_json(res)




    def get_product(self,product,instrument ,verbose=False,dry_run=False,product_type='Real', **kwargs):
        kwargs['instrument'] = instrument
        kwargs['product_type'] = product
        kwargs['query_type'] = product_type
        kwargs['off_line'] = False,
        kwargs['query_status'] = 'new',
        kwargs['verbose'] = verbose,
        kwargs['session_id'] = self.generate_session_id()
        kwargs['dry_run'] = dry_run,

        res = requests.get("%s/api/par-names" % self.url)

        if res.status_code == 200:

            _ignore_list=['instrument','product_type','query_type','off_line','query_status','verbose','session_id','dry_run']
            validation_dict=copy.deepcopy(kwargs)

            for _i in _ignore_list:
                del validation_dict[_i]

            res = requests.get("%s/api/par-names" % self.url, params=dict(instrument=instrument,product_type=product), cookies=self.cookies)

            valid_names=self._decode_res_json(res)
            for n in validation_dict.keys():
                if n not in valid_names:
                    raise RuntimeError('the parameter: %s'%n, 'is not among the valid ones:',valid_names)
        else:
            warnings.warn('paramter check not available on remote server, check carefully parameters name')

        res = self.request(kwargs)
        data = None

        js=json.loads(res.content)
        #print('js-->',type(js))
        if dry_run  ==False:
            #print ('-->npd', 'numpy_data_product' in res.json()['products'].keys())
            #print ('-->ndpl',    'numpy_data_product_list'  in res.json()['products'].keys())

            data=[]
            if  'numpy_data_product'  in res.json()['products'].keys():
                #data= NumpyDataProduct.from_json(res.json()['products']['numpy_data_product'])
                data.append(NumpyDataProduct.decode(js['products']['numpy_data_product']))
            elif  'numpy_data_product_list'  in res.json()['products'].keys():

                #data= [NumpyDataProduct.from_json(d) for d in res.json()['products']['numpy_data_product_list']]
                data.extend([NumpyDataProduct.decode(d) for d in js['products']['numpy_data_product_list']])

            if 'binary_data_product_list' in res.json()['products'].keys():
                data.extend([BinaryData().decode(d) for d in js['products']['binary_data_product_list']])

            if 'catalog' in res.json()['products'].keys():
                data.append(ApiCatalog(js['products']['catalog'],name='dispatcher_catalog'))

            if 'astropy_table_product_ascii_list' in res.json()['products'].keys():
                data.extend([ascii.read(table_text) for table_text in js['products']['astropy_table_product_ascii_list']])

            if 'astropy_table_product_binary_list' in res.json()['products'].keys():
                #for  table_binary in js['products']['astropy_table_product_binary_list']:
                #    t_rec = base64.b64decode(_o_dict['binary'])
                #    try:
                #        t=data.extend([])
                #    except:
                #        t=data.extend([])
                data.extend([ascii.read(table_binary) for table_binary in js['products']['astropy_table_product_binary_list']])

            d=DataCollection(data)

        else:
            self._decode_res_json(res.json()['products']['instrumet_parameters'])
            d=None

        del(res)

        return d



    @staticmethod
    def set_api_code(query_dict):

        _skip_list_ = ['job_id', 'query_status', 'session_id', 'use_resolver[local]', 'use_scws']

        _alias_dict = {}
        _alias_dict['product_type'] = 'product'
        _alias_dict['query_type'] = 'product_type'

        _header = '''
        from oda_api.api import DispatcherAPI\n
        disp=DispatcherAPI(host='www.astro.unige.ch/cdci/astrooda/dispatch-data',instrument='mock',cookies=cookies,protocol='https')'''

        _cmd_prod_ = 'disp.get_product(**par_dict)'

        _api_dict = {}
        for k in query_dict.keys():
            if k not in _skip_list_:

                if k in _alias_dict.keys():
                    n = _alias_dict[k]

                else:
                    n = k

                _api_dict[n] = query_dict[k]


        _cmd_ ='%s\n'%_header
        _cmd_ +='par_dict='
        _cmd_ += '%s'%_api_dict
        _cmd_ += '\n'
        _cmd_ +='%s'%_cmd_prod_


        return _cmd_



class DataCollection(object):


    def __init__(self,data_list,add_meta_to_name=['src_name','product']):
        self._p_list = []
        self._n_list = []
        for ID,data in enumerate(data_list):

            if hasattr(data,'name'):
                name=data.name+'prod_%d_'%ID
            else:
                name='pord_%d_' % ID

            name = self._build_prod_name(data, name, add_meta_to_name)

            setattr(self, name, data)

            self._p_list.append(data)
            self._n_list.append(name        )

    def show(self):
        for ID, s in enumerate(self._p_list):
            print(ID, s.meta_data)

    def _build_prod_name(self,prod,name,add_meta_to_name):
        for kw in add_meta_to_name:
            if kw in prod.meta_data:
                s = prod.meta_data[kw].replace(' ', '')

                name += s.strip()

        return name

    def save_all_data(self,prenpend_name='',add_meta_to_name=['src_name','product']):
        for prod in self._p_list:
            name = prenpend_name
            name = self._build_prod_name(prod,name,add_meta_to_name)

            name= name +'.fits'
            prod.write_fits_file(name)


    def save(self,file_name):
        pickle.dump(self, open(file_name, 'wb'), protocol=pickle.HIGHEST_PROTOCOL)

    def new_from_metadata(self,key,val):
        dc=None
        _l=[]
        for p in self._p_list:
            if p.meta_data[key] == val:
                _l.append(p)

        if _l !=[]:
           dc = DataCollection(_l)

        return dc
