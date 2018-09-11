
from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)


__author__ = "Andrea Tramacere"

import requests
import ast
import json

class Request(object):
    def __init__(self,):
        pass



class DispatcherAPI(object):

    def __init__(self,instrument,host='10.194.169.161',port=32784):

        self.host=host
        self.port=port

        self.set_instr(instrument)

        self.url= "http://%s:%d"%(host,port)


    def set_instr(self,instrument):
        self.instrument=instrument

    def set_prod(self):
        pass


    def get_description(self):
        res=requests.get("%s:/api/meta-data"%self.url,params=dict(instrument=self.instrument))
        _js = json.loads(res.content)
        a = ast.literal_eval(str(_js).replace('null', 'None'))

        def dig_list(b):
            if isinstance(b, (set, tuple, list)):
                for c in b:
                    dig_list(c)
            else:
                # print type(b)
                c = ast.literal_eval(str(b))
                if isinstance(c, (set, tuple, list)):
                    dig_list(c)
                else:
                    print
                    type(c), c

        dig_list(a)



    def get_prod_descriton(self):
        pass
