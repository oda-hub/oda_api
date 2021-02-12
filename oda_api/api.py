
from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)


__author__ = "Andrea Tramacere, Volodymyr Savchenko"

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
from . import __version__
from . import custom_formatters
from . import colors as C
from itertools import cycle
import re
import traceback
from jsonschema import validate as validate_json

import logging

from .data_products import NumpyDataProduct,BinaryData,ApiCatalog

__all__ = ['Request', 'NoTraceBackWithLineNumber', 'NoTraceBackWithLineNumber', 'RemoteException', 'DispatcherAPI']

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



class RemoteException(NoTraceBackWithLineNumber):

    def __init__(self, message='Remote analysis exception', debug_message=''):
        super(RemoteException, self).__init__(message)
        self.message=message
        self.debug_message=debug_message


def safe_run(func):

    def func_wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__name__)

        self = args[0] # because it really is

        n_tries_left = self.n_max_tries
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                message = ''
                message += '\nunable to complete API call'
                message += '\nin ' + str(func) + ' called with:'
                message += '\n... ' + ", ".join([str(arg) for arg in args])
                message += '\n... ' + ", ".join([k+": "+str(v) for k,v in kwargs])
                message += '\npossible causes:'
                message += '\n- connection error'
                message += '\n- wrong credentials'
                message += '\n- error on the remote server'
                message += '\n exception message: '
                message += '\n\n%s\n'%e
                message += traceback.format_exc()

                n_tries_left -= 1 

                if n_tries_left > 0:
                    logger.warning("problem in API call, %i tries left:\n%s\n sleeping %i seconds until retry", n_tries_left, message, self.retry_sleep_s)
                else:
                    raise RemoteException(message=message)

    return func_wrapper

class DispatcherAPI(object):
    def __init__(self,instrument='mock',host='www.astro.unige.ch/cdci/astrooda/dispatch-data',port=None,cookies=None,protocol='https'):

        self.host=host
        self.port=port
        self.cookies=cookies
        self.set_instr(instrument)

        self.n_max_tries = 20
        self.retry_sleep_s = 5


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

        # TODO this should really be just swagger/bravado
        self.dispatcher_response_schema = {
                    'type': 'object',
                    'properties': {
                        'exit_status': { 
                                'type': 'object' ,
                                'properties': {
                                        'status': { 'type': 'number' },
                                    },
                                },
                        'query_status': { 'type': 'string' },
                        'job_monitor': { 
                                'type': 'object' ,
                                'properties': {
                                        'job_id': { 'type': 'string' },
                                    },
                                },
                    }
                }

    def set_custom_progress_formatter(self, F):
        self.custom_progress_formatter = F

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
        self.custom_progress_formatter = custom_formatters.find_custom_formatter(instrument)

    def _progress_bar(self,info=''):
        print("\r %s the job is working remotely, please wait %s"%(next(self._progress_iter),info),end='')

    def format_custom_progress(self, full_report_dict_list):
        F = getattr(self, 'custom_progress_formatter', None)

        if F is not None:
            return F(full_report_dict_list)

        return ""


    @safe_run
    def request(self,parameters_dict,handle='run_analysis',url=None):
        if 'scw_list' in parameters_dict.keys():
            print (parameters_dict['scw_list'])

        self.set_instr(parameters_dict.get('instrument', self.instrument))


        if url is None:
            url=self.url

        parameters_dict['api']='True'
        parameters_dict['oda_api_version'] = __version__

        for k in parameters_dict.keys():
            print(f"- {C.BLUE}{k}: {parameters_dict[k]}{C.NC}")


        def get_res_json(verbose=False):
            if verbose:
                print(f'- waiting for remote response (since {time.strftime("%Y-%m-%d %H:%M:%S")}), please wait for {url}/{handle}')

            try:
                timeout = getattr(self, 'timeout', 120)

                response = requests.get(
                                "%s/%s" % (url, handle), 
                                params=parameters_dict,
                                cookies=self.cookies, 
                                headers={
                                          'Request-Timeout': str(timeout),
                                          'Connection-Timeout': str(timeout),
                                        },
                                timeout=timeout,
                           )

                response_json = self._decode_res_json(response)

                validate_json(response_json, self.dispatcher_response_schema)

                return response_json
            except json.decoder.JSONDecodeError as e:
                print(f"{C.RED}{C.BOLD}unable to decode json from response:{C.NC}")
                print(f"{C.RED}{res.text}{C.NC}")
                raise

        res_json = get_res_json(True)


        query_status = res_json['query_status']

        job_id = res_json['job_monitor']['job_id']

        if query_status != 'done' and query_status != 'failed':
            print ('the job has been submitted on the remote server')

        t0 = time.time()

        while query_status != 'done' and query_status != 'failed':
            parameters_dict['query_status']=query_status
            parameters_dict['job_id'] = job_id

            res_json = get_res_json()

            query_status =res_json['query_status']
            job_id = res_json['job_monitor']['job_id']

            full_report_dict_list = res_json['job_monitor'].get('full_report_dict_list', [])

            info = 'status=%s job_id=%s in %d messages since %d seconds'%(
                        query_status, 
                        str(job_id)[:8], 
                        len(full_report_dict_list),
                        time.time() - t0,
                    )

            custom_info = self.format_custom_progress(full_report_dict_list)
            if custom_info != "":
                info += "; " + custom_info


            self._progress_bar(info=info)

            time.sleep(2)

        print("\r", end="")
        print('')
        print('')

        if res_json['exit_status']['status']!=0:
            self.failure_report(res_json)

        #print('job_monitor', res.json()['job_monitor'])
        #print('query_status', res.json()['query_status'])
        #print('products', res.json()['products'].keys())

        if query_status != 'failed':

            print('query done succesfully!')
        else:

            raise RemoteException(debug_message=res_json['exit_status']['error_message'])

        return res_json


    def failure_report(self, res_json):
        print('query failed!')
        #print('status code:-> %s'%res.status_code)
        #print('server message:-> %s'%res.text)
        print('Remote server message:->', res_json['exit_status']['message'])
        print('Remote server error_message->', res_json['exit_status']['error_message'])
        print('Remote server debug_message->', res_json['exit_status']['debug_message'])

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
            if hasattr(res, 'content'):
                #_js = json.loads(res.content)
                #fixed issue with python 3.5
                _js = res.json()
                res = ast.literal_eval(str(_js).replace('null', 'None'))
            else:
                res = ast.literal_eval(str(res).replace('null', 'None'))

            self.dig_list(res)
            return res
        except Exception as e:
            #print (json.loads(res.text))

            msg='remote/connection error, server response is not valid \n'
            msg += 'possible causes: \n'
            msg += '- connection error\n'
            msg += '- wrong credentials\n'
            msg += '- wrong remote address\n'
            msg += '- error on the remote server\n'
            msg+="--------------------------------------------------------------\n"
            if hasattr(res,'status_code'):

                msg += '--- status code:-> %s\n' % res.status_code
            if hasattr(res,'text'):

                msg +='--- response text ---\n %s\n' % res.text
            if hasattr(res,'content'):

                msg += '--- res content ---\n %s\n' % res.content
            msg += "--------------------------------------------------------------"

            raise RemoteException(message=msg)

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

        res = requests.get("%s/api/par-names" % self.url, params=dict(instrument=instrument,product_type=product), cookies=self.cookies)

        #print('1-.>',res.status_code,res.text)
        if res.status_code == 200:

            _ignore_list=['instrument','product_type','query_type','off_line','query_status','verbose','session_id','dry_run']
            validation_dict=copy.deepcopy(kwargs)

            for _i in _ignore_list:
                del validation_dict[_i]

            #res = requests.get("%s/api/par-names" % self.url, params=dict(instrument=instrument,product_type=product), cookies=self.cookies)

            valid_names=self._decode_res_json(res)
            for n in validation_dict.keys():
                if n not in valid_names:
                    #raise RuntimeError('the parameter: %s'%n, 'is not among the valid ones:',valid_names)
                    msg = '\n'
                    msg+= '----------------------------------------------------------------------------\n'
                    msg+='the parameter: %s '%n
                    msg+='  is not among valid ones:'
                    msg+= '\n'
                    msg+='%s'%valid_names
                    msg+= '\n'
                    msg+='this will throw an error in a future version \n'
                    msg+='and might breack the current request!\n '
                    msg+= '----------------------------------------------------------------------------\n'
                    warnings.warn(msg)
                    #print('is not among valid ones:',valid_names)
                    #print('this will throw an error in a future version')
        else:
            warnings.warn('parameter check not available on remote server, check carefully parameters name')

        res_json = self.request(kwargs)

        data = None
        #js=json.loads(res.content)

        if dry_run == False:
            #print ('-->npd', 'numpy_data_product' in res.json()['products'].keys())
            #print ('-->ndpl',    'numpy_data_product_list'  in res.json()['products'].keys())

            data=[]
            if  'numpy_data_product'  in res_json['products'].keys():
                data.append(NumpyDataProduct.decode(res_json['products']['numpy_data_product']))
            elif  'numpy_data_product_list'  in res_json['products'].keys():

                data.extend([NumpyDataProduct.decode(d) for d in res_json['products']['numpy_data_product_list']])

            if 'binary_data_product_list' in res_json['products'].keys():
                data.extend([BinaryData().decode(d) for d in res_json['products']['binary_data_product_list']])

            if 'catalog' in res_json['products'].keys():
                data.append(ApiCatalog(res_json['products']['catalog'],name='dispatcher_catalog'))

            if 'astropy_table_product_ascii_list' in res_json['products'].keys():
                #print()
                data.extend([ascii.read(table_text['ascii']) for table_text in res_json['products']['astropy_table_product_ascii_list']])

            if 'astropy_table_product_binary_list' in res_json['products'].keys():
                #for  table_binary in js['products']['astropy_table_product_binary_list']:
                #    t_rec = base64.b64decode(_o_dict['binary'])
                #    try:
                #        t=data.extend([])
                #    except:
                #        t=data.extend([])
                data.extend([ascii.read(table_binary) for table_binary in res_json['products']['astropy_table_product_binary_list']])

            d=DataCollection(data,instrument=instrument,product=product)
            for p in d._p_list:
                if hasattr(p,'meta_data') is False and hasattr(p,'meta') is True:
                    p.meta_data = p.meta
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


    def __init__(self,data_list,add_meta_to_name=['src_name','product'],instrument=None,product=None):
        self._p_list = []
        self._n_list = []
        for ID,data in enumerate(data_list):

            name=''
            if hasattr(data,'name'):
                name=data.name

            if name.strip()=='':
                if product is not None:
                    name = '%s'%product
                elif instrument is not None:
                    name = '%s' % instrument
                else:
                    name = 'prod'

            name='%s_%d'%(name,ID)

            name,var_name = self._build_prod_name(data, name, add_meta_to_name)
            setattr(self, var_name, data)

            self._p_list.append(data)
            self._n_list.append(name)

    def show(self):
        for ID, prod_name in enumerate(self._n_list):
            if hasattr(self._p_list[ID], 'meta_data'):
                meta_data=self._p_list[ID].meta_data
            else:
                meta_data=''
            print('ID=%s prod_name=%s'%(ID,prod_name),' meta_data:',meta_data)
            print()

    def _build_prod_name(self,prod,name,add_meta_to_name):

        for kw in add_meta_to_name:
            if hasattr(prod,'meta_data'):
                if kw in prod.meta_data:
                    s = prod.meta_data[kw].replace(' ', '')
                    if s.strip() !='':
                        name += '_'+s.strip()
        return name,clean_var_name(name)

    def save_all_data(self,prenpend_name=None):
        for pname,prod in zip(self._n_list,self._p_list):
            if prenpend_name is not  None:
                file_name=prenpend_name+'_'+pname
            else:
                file_name=pname

            file_name= file_name +'.fits'
            prod.write_fits_file(file_name)


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


def clean_var_name(s):
    s = s.replace('-', 'm')
    s = s.replace('+', 'p')
    s = s.replace(' ', '_')

    # Remove invalid characters
    s = re.sub('[^0-9a-zA-Z_]', '', s)

     # Remove leading characters until we find a letter or underscore
    s = re.sub('^[^a-zA-Z_]+', '', s)

    return s
