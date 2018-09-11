
from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)



__author__ = "Andrea Tramacere"

import requests


from .api import DispatcherAPI


class PolarDispatcher(DispatcherAPI):

    def __init__(self):
        super(PolarDispatcher,self).__init__(instrument='polar')



    def get_lc(self,src_name='polar_test_src',
                     time_bin=0.2   ,
                     time_bin_format='sec',
                     T1_iso='2016-12-18T08:32:21.000',
                     T2_iso='2016-12-18T08:34:01.000',
                     E1_keV=10.,
                     E2_keV=100.):

        parameters_dic = dict(E1_keV=E1_keV, E2_keV=E2_keV, T1=T1_iso, T2=T2_iso,
                              query_type='Real', product_type='polar_lc',
                              src_name=src_name, time_bin=time_bin,
                              time_bin_format=time_bin_format, instrument=self.instrument, query_status='new',
                              off_line=False,
                              run_asynch=False,
                              session_id=self.generate_session_id())


        res = requests.get("%s/run_analysis" % self.url, params=parameters_dic)

        lc_data = res.json()['products']['data']

        rate = lc_data['rate']
        time = lc_data['time']
        rate_err = lc_data['rate_err']


        return rate,time,rate_err

