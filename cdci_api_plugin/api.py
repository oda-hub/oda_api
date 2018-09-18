
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

class Request(object):
    def __init__(self,):
        pass



class DispatcherAPI(object):

    def __init__(self,instrument='mock',host='10.194.169.161',port=32784):

        self.host=host
        self.port=port

        self.set_instr(instrument)


        self.url= "http://%s"%(host)

        if port is not None:
            self.url += ":%d" % (port)





    def generate_session_id(self,size=16):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    def set_instr(self,instrument):
        self.instrument=instrument





    def request(self,parameters_dict,handle='run_analysis',url=None):
        if url is None:
            url=self.url


        res= requests.get("%s/%s" %(url, handle), params=parameters_dict)
        query_status = res.json()['query_status']
        job_id = res.json()['job_monitor']['job_id']
        print ('working remotely, please wait')
        while query_status != 'done' and query_status != 'failed':
            parameters_dict['query_status']=query_status
            parameters_dict['job_id'] = job_id
            res = requests.get("%s/%s" % (url,handle), params=parameters_dict)
            query_status =res.json()['query_status']
            job_id = res.json()['job_monitor']['job_id']
            #print ('query status',query_status)
            #print ('job_id', job_id)

            time.sleep(5)

        if query_status != 'failed':
            pass
        else:
            self.failure_report(res)
            raise Exception('query failed',)

        print('exit_status, status', res.json()['exit_status']['status'])
        print('exit_status, message', res.json()['exit_status']['message'])
        print('exit_status, error_message', res.json()['exit_status']['error_message'])
        print('exit_status, debug_message', res.json()['exit_status']['debug_message'])
        print('job_monitor', res.json()['job_monitor'])
        print('query_status', res.json()['query_status'])
        print('products', res.json()['products'].keys())

        return res


    def failure_report(self,res):
        print('exit_status, status', res.json()['exit_status']['status'])
        print('exit_status, message', res.json()['exit_status']['message'])
        print('exit_status, error_message', res.json()['exit_status']['error_message'])
        print('exit_status, debug_message', res.json()['exit_status']['debug_message'])

    def dig_list(self,b,only_prod=False):
        from astropy.table import Table
        if isinstance(b, (set, tuple, list)):
            for c in b:
                self.dig_list(c)
        else:
            #print('not list',type(b))
            try:
                b = ast.literal_eval(str(b))
                #print(type(b))
            except:
                #print ('except')
                return str(b)
            if isinstance(b, dict):
                #print('dict')
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
                self.dig_list(b)







    def get_instrument_description(self,instrument=None):
        if instrument is None:
            instrument=self.instrument

        res=requests.get("%s/api/meta-data"%self.url,params=dict(instrument=instrument))
        _js = json.loads(res.content)
        a = ast.literal_eval(str(_js).replace('null', 'None'))
        self.dig_list(a)
        #for _d in a[0]:
        #    if isinstance(_d,list):
         #       for _d1 in _d:
          #          print('a',_d1)
          #  else:
          #      print ('b',_d,type(_d))


    def get_product_description(self,instrument,product_name):
        res = requests.get("%s/api/meta-data" % self.url, params=dict(instrument=instrument,product_type=product_name))
        _js = json.loads(res.content)
        a = ast.literal_eval(str(_js).replace('null', 'None'))
        print('--------------')
        print ('parameters for  product',product_name,'and instrument',instrument)
        self.dig_list(a)

    def get_instruments_list(self):
        #print ('instr',self.instrument)
        res = requests.get("%s/api/instr-list" % self.url,params=dict(instrument=self.instrument))
        _js = json.loads(res.content)
        a = ast.literal_eval(str(_js).replace('null', 'None'))
        self.dig_list(a)
        return a


    def get_product(self,product,instrument ,asynch=True, **kwargs):
        kwargs['instrument'] = instrument
        kwargs['product_type'] = product
        kwargs['query_type'] = 'Real'
        kwargs['off_line'] = False,
        kwargs['run_asynch'] = asynch,
        kwargs['query_status'] = 'new',
        kwargs['session_id'] = self.generate_session_id()
        res = self.request(kwargs)

        return res.json()['products']['data']

