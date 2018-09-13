from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)

__author__ = "Andrea Tramacere"





from .api import DispatcherAPI


class IsgriDispatcher(DispatcherAPI):

    def __init__(self):
        super(IsgriDispatcher,self).__init__(instrument='polar')


    
    def get_lc(self,
                     src_name='4U 1700-377',
                     time_bin=500,
                     time_bin_format='sec',
                     scw_list=None,
                     query_type='Real',
                     upload_data=None,
                     T1_iso='2003-03-15T23:27:40.0',
                     T2_iso='2003-03-16T00:03:15.0',
                     RA_user_cat=[205.09872436523438],
                     Dec_user_cat=[83.6317138671875],
                     detection_threshold=5.0,
                     radius=25,
                     E1_keV=20.,
                     E2_keV=40.):

        """

        :param src_name:
        :param time_bin:
        :param time_bin_format:
        :param scw_list:
        :param query_type:
        :param upload_data:
        :param T1_iso:
        :param T2_iso:
        :param RA_user_cat:
        :param Dec_user_cat:
        :param detection_threshold:
        :param radius:
        :param E1_keV:
        :param E2_keV:
        :return:
        """




        parameters_dict=dict(E1_keV=E1_keV,
                            E2_keV=E2_keV,
                            T1=T1_iso,
                            T2=T2_iso,
                            RA=RA_user_cat[0],
                            DEC=Dec_user_cat[0],
                            radius=radius,scw_list=scw_list,
                            image_scale_min=1,
                            session_id=self.generate_session_id(),
                            query_type=query_type,
                            product_type='isgri_lc',
                            detection_threshold=detection_threshold,
                            src_name=src_name,
                            time_bin=time_bin,
                            time_bin_format=time_bin_format,
                            run_asynch=True,
                            user_catalog_dictionary=None)

        res = self.request(parameters_dict)

        lc_data = res.json()['products']['data']

        rate = lc_data['rate']
        time = lc_data['time']
        rate_err = lc_data['rate_err']


        return rate,time,rate_err

