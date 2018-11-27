
from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)


__author__ = "Andrea Tramacere"

import requests
import ast
import json
import  random
import string
import time
from itertools import cycle

from .data_products import NumpyDataProduct,BinaryData

class Request(object):
    def __init__(self,):
        pass


class RemoteException(Exception):

    def __init__(self, message='Remote analysis exception', debug_message=''):
        super(RemoteException, self).__init__(message)
        self.message=message
        self.debug_message=debug_message



class DispatcherAPI(object):

    def __init__(self,instrument='mock',host='10.194.169.161',port=None,cookies=None,protocol='http'):

        self.host=host
        self.port=port
        self.cookies=cookies
        self.set_instr(instrument)

        if protocol=='http':
            self.url= "http://%s"%(host)
        elif protocol=='https':
            self.url = "https://%s" % (host)
        else:
            raise  RuntimeError('protocol must be either http or https')

        if port is not None:
            self.url += ":%d" % (port)

        self._progress_iter = cycle(['|', '/', '-', '\\'])




    def generate_session_id(self,size=16):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    def set_instr(self,instrument):
        self.instrument=instrument



    def _progess_bar(self,info=''):
        print("\r %s the job is working remotely, please wait %s"%(next(self._progress_iter),info),end='')


    def request(self,parameters_dict,handle='run_analysis',url=None):

        if url is None:
            url=self.url
        parameters_dict['api']='True'
        print('waiting for remote response, please wait',handle,url)
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





    def _decode_res_json(self,res):
        if hasattr(res,'content'):
            _js = json.loads(res.content)
            res = ast.literal_eval(str(_js).replace('null', 'None'))
        else:
            res = ast.literal_eval(str(res).replace('null', 'None'))

        self.dig_list(res)
        return res

    def get_instrument_description(self,instrument=None):
        if instrument is None:
            instrument=self.instrument

        res=requests.get("%s/api/meta-data"%self.url,params=dict(instrument=instrument),cookies=self.cookies)
        self._decode_res_json(res)




    def get_product_description(self,instrument,product_name):
        res = requests.get("%s/api/meta-data" % self.url, params=dict(instrument=instrument,product_type=product_name),cookies=self.cookies)

        print('--------------')
        print ('parameters for  product',product_name,'and instrument',instrument)
        self._decode_res_json(res)



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

        res = self.request(kwargs)
        data = None

        js=json.loads(res.content)
        #print('js-->',type(js))
        if dry_run  ==False:
            #print ('-->npd', 'numpy_data_product' in res.json()['products'].keys())
            #print ('-->ndpl',    'numpy_data_product_list'  in res.json()['products'].keys())

            if  'numpy_data_product'  in res.json()['products'].keys():
                #data= NumpyDataProduct.from_json(res.json()['products']['numpy_data_product'])
                data = NumpyDataProduct.decode(js['products']['numpy_data_product'])
            elif  'numpy_data_product_list'  in res.json()['products'].keys():

                #data= [NumpyDataProduct.from_json(d) for d in res.json()['products']['numpy_data_product_list']]
                data = [NumpyDataProduct.decode(d) for d in js['products']['numpy_data_product_list']]

            if 'binary_data_product_list' in res.json()['products'].keys():
                data.extend([BinaryData().decode(d) for d in js['products']['binary_data_product_list']])
        else:
            self._decode_res_json(res.json()['products']['instrumet_parameters'])

        del(res)

        return data