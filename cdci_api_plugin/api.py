
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

    def __init__(self,instrument,host='10.194.169.161',port=32784):

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

    def set_prod(self):
        pass


    def get_lc(self):
        raise RuntimeError('method to implement in the derived ')

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

    def dig_list(self,b):
            if isinstance(b, (set, tuple, list)):
                for c in b:
                    self.dig_list(c)
            else:
                # print type(b)
                c = ast.literal_eval(str(b))
                if isinstance(c, (set, tuple, list)):
                    self.dig_list(c)
                else:
                    print(type(c), c)

    def get_description(self):
        res=requests.get("%s/api/meta-data"%self.url,params=dict(instrument=self.instrument))
        _js = json.loads(res.content)
        a = ast.literal_eval(str(_js).replace('null', 'None'))



        self.dig_list(a)



    def get_prod_descriton(self):
        pass


