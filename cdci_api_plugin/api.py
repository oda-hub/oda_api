
from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)


__author__ = "Andrea Tramacere"

import requests
import ast
import json
import  random
import string

class Request(object):
    def __init__(self,):
        pass



class DispatcherAPI(object):

    def __init__(self,instrument,host='10.194.169.161',port=32784):

        self.host=host
        self.port=port

        self.set_instr(instrument)

        self.url= "http://%s:%d"%(host,port)


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


        return requests.get("%s/run_analysis" %(handle, url), params=parameters_dict)

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


