import hashlib

from .api import DispatcherAPI, UserError
from . import plot_tools

from datetime import datetime
from astropy import units as u
from astropy.coordinates import Angle, SkyCoord
import numpy as np

import logging
import typing
import requests
import os
import tempfile
import shutil
import json
import inspect

logger = logging.getLogger("oda_api.gallery_api")


__all__ = ['GalleryDispatcherAPI']

class GalleryDispatcherAPI(DispatcherAPI):

    def get_list_terms_gallery(self,
                               group: typing.Optional[str] = None,
                               parent: typing.Optional[str] = None,
                               parent_id: typing.Optional[str] = None,
                               token: typing.Optional[str] = None
                               ):
        logger.debug("Getting the list of available instruments on the gallery")
        params = {
            'group': group,
            'parent': parent,
            'parent_id': parent_id,
            'token': token
        }

        res = requests.get("%s/get_list_terms" % self.url,
                           params={**params}
                           )
        response_json = self._decode_res_json(res)

        if res.status_code != 200:
            logger.warning(f"An issue occurred while getting the list of terms from the group {group}, "
                           f"from the product gallery : {res.text}")
        else:
            logger.info(f"List of terms from the group {group} successfully returned")

        return response_json

    def parse_observation_time_arg_product_gallery(self,
                                                   t1=None,
                                                   t2=None,
                                                   observation_time_format: str = 'ISOT'
                                                   ):

        if t1 is not None:
            if observation_time_format is not None and observation_time_format.upper() == 'MJD':
                try:
                    logger.info("The value of T1 has been provided in a difference format from UTC, "
                                "this will be attempted to be converted to UTC before being uploaded over the gallery")
                    t1 = self.convert_mjd_to_utc(float(t1))
                except Exception as e:
                    logger.warning(f'Error during the time conversion: {e}\n'
                                   'please check the time arguments you provided and the relative format')
                    raise UserError('Error during the time conversion, '
                                    'please check the time arguments you provided and the relative format')
            elif observation_time_format is None or observation_time_format.upper() == 'ISOT':
                try:
                    datetime.strptime(t1, '%Y-%m-%dT%H:%M:%S')
                except Exception as e:
                    logger.warning(f'Error during the time conversion: {e}\n'
                                   'please check the time arguments you provided and the relative format')
                    raise UserError(f'Error during the time conversion: {e}\n'
                                    'please check the time arguments you provided and the relative format')

        if t2 is not None:
            if observation_time_format is not None and observation_time_format.upper() == 'MJD':
                try:
                    logger.info("The value of T2 has been provided in a difference format from UTC, "
                                "this will be attempted to be converted to UTC before being uploaded over the gallery")
                    t2 = self.convert_mjd_to_utc(float(t2))
                except Exception as e:
                    logger.warning(f'Error during the time conversion: {e}\n'
                                   'please check the time arguments you provided and the relative format')
                    raise UserError('Error during the time conversion, '
                                    'please check the time arguments you provided and the relative format')
            elif observation_time_format is None or observation_time_format.upper() == 'ISOT':
                try:
                    datetime.strptime(t2, '%Y-%m-%dT%H:%M:%S')
                except Exception as e:
                    logger.warning(f'Error during the time conversion: {e}\n'
                                   'please check the time arguments you provided and the relative format')
                    raise UserError(f'Error during the time conversion: {e}\n'
                                    'please check the time arguments you provided and the relative format')

        return t1, t2

    def get_yaml_files_observation_with_title(self,
                                              observation_title: str = None,
                                              token: str = None):
        params = {
            'title': observation_title,
            'token': token
        }

        res = requests.get(os.path.join(self.url, "get_observation_attachments"),
                           params={**params},
                           )

        if res.status_code != 200:
            response_json = res.json()
            error_message = (f"An issue occurred while performing a request on the product gallery, "
                             f"the following error was returned:\n")
            if 'error_message' in response_json:
                error_message += '\n' + response_json['error_message']
                if 'drupal_helper_error_message' in response_json:
                    error_message += '-' + response_json['drupal_helper_error_message']
            else:
                error_message += res.text
            logger.warning(error_message)
        else:
            response_json = res.json()
            msg = f"Observation with title {observation_title}"
            if 'file_content' in response_json:
                msg += " contains a yaml file\n"

            logger.info(msg)


        return response_json

    def get_list_images_angular_distance(self,
                                         token: str = None,
                                         instrument=None,
                                         e1_kev=None, e2_kev=None,
                                         t1=None, t2=None,
                                         ra_ref=None, dec_ref=None,
                                         r=None
                                         ):

        product_list = self.get_list_images_with_conditions(token=token,
                                                            instrument=instrument,
                                                            e1_kev=e1_kev, e2_kev=e2_kev,
                                                            t1=t1, t2=t2)

        if isinstance(product_list, list) and ra_ref is not None and dec_ref is not None and r is not None:
            source_coord_ref = SkyCoord(ra_ref, dec_ref, unit=(u.deg, u.deg))

            ra_values_prod_list = list(map(lambda x: x['ra'], filter(lambda x: 'ra' in x, product_list)))
            dec_values_prod_list = list(map(lambda x: x['dec'], filter(lambda x: 'dec' in x, product_list)))
            coords_prod_list = SkyCoord(ra_values_prod_list, dec_values_prod_list, unit=(u.deg, u.deg))

            separation = source_coord_ref.separation(coords_prod_list).deg

            ind = (separation <= r)

            product_list = list(np.array(product_list)[ind])

        return product_list

    def get_list_images_with_conditions(self,
                                        token: str = None,
                                        instrument=None,
                                        e1_kev=None, e2_kev=None,
                                        t1=None, t2=None,
                                        min_span_rev=None,
                                        max_span_rev=None):

        return self.get_list_products_with_conditions_generic(token=token,
                                                              instrument=instrument,
                                                              e1_kev=e1_kev, e2_kev=e2_kev,
                                                              t1=t1, t2=t2,
                                                              min_span_rev=min_span_rev,
                                                              max_span_rev=max_span_rev,
                                                              product_type='image')

    def get_list_lightcurve_with_conditions(self,
                                            token: str = None,
                                            instrument=None,
                                            source_name=None,
                                            e1_kev=None, e2_kev=None,
                                            t1=None, t2=None,
                                            min_span_rev=None,
                                            max_span_rev=None):

        return self.get_list_products_with_conditions_generic(token=token,
                                                              instrument=instrument,
                                                              source_name=source_name,
                                                              e1_kev=e1_kev, e2_kev=e2_kev,
                                                              t1=t1, t2=t2,
                                                              min_span_rev=min_span_rev,
                                                              max_span_rev=max_span_rev,
                                                              product_type='lightcurve')

    def get_list_spectra_with_conditions(self,
                                         token: str = None,
                                         instrument=None,
                                         source_name=None,
                                         t1=None, t2=None,
                                         min_span_rev=None,
                                         max_span_rev=None):

        return self.get_list_products_with_conditions_generic(token=token,
                                                              instrument=instrument,
                                                              source_name=source_name,
                                                              t1=t1, t2=t2,
                                                              min_span_rev=min_span_rev,
                                                              max_span_rev=max_span_rev,
                                                              product_type='spectrum')

    def get_revnum(self, time_to_convert, token):
        rev1_value = None
        params = {'time_to_convert': time_to_convert,
                  'token': token}

        res = requests.get(os.path.join(self.url, "get_revnum"),
                           params={**params}
                           )

        if res.status_code != 200:
            response_json = res.json()
            error_message = (f"An issue occurred while performing a request on the product gallery, "
                             f"the following error was returned:\n")
            if 'error_message' in response_json:
                error_message += '\n' + response_json['error_message']
                if 'drupal_helper_error_message' in response_json:
                    error_message += '-' + response_json['drupal_helper_error_message']
            else:
                error_message += res.text
            logger.warning(error_message)
        else:
            response_json = res.json()
            rev1_value = response_json['revnum']

        return rev1_value

    def get_list_products_with_conditions_generic(self,
                                                  token: str = None,
                                                  instrument=None,
                                                  source_name=None,
                                                  e1_kev=None, e2_kev=None,
                                                  t1=None, t2=None,
                                                  min_span_rev=None,
                                                  max_span_rev=None,
                                                  product_type=None):

        if min_span_rev is not None and min_span_rev < 0:
            raise UserError("min_span_rev must be non-negative")
        if max_span_rev is not None and max_span_rev < 0:
            raise UserError("max_span_rev must be non-negative")
        if min_span_rev is not None and max_span_rev is not None and min_span_rev > max_span_rev:
            raise UserError("min_span_rev must be less than or equal to max_span_rev")

        rev1_value = None
        if t1 is not None:
            rev1_value = self.get_revnum(t1, token)
        rev2_value = None
        if t2 is not None:
            rev2_value = self.get_revnum(t2, token)

        product_list = []

        # query call optimization: if min_span_rev is None or 0, or if max_span_rev is 0, we split the query in smaller,
        # more manageable queries (that should not fail) because we want to include those products that have a span_rev
        # of 0, and it's risky to do that with a single query
        if min_span_rev is None or min_span_rev == 0 or (max_span_rev is not None and max_span_rev == 0):
            list_rev_range = list(np.arange(rev1_value, rev2_value, 250))
            for rev in list_rev_range:
                rev1 = rev
                if rev == list_rev_range[-1]:
                    rev2 = rev2_value
                else:
                    rev2 = rev + 249
                product_list += self.get_list_products_with_conditions(token=token,
                                                                       instrument_name=instrument,
                                                                       product_type=product_type,
                                                                       src_name=source_name,
                                                                       e1_kev_value=e1_kev,
                                                                       e2_kev_value=e2_kev,
                                                                       rev1_value=rev1,
                                                                       rev2_value=rev2,
                                                                       max_span_rev_value=0)
            # if we have to include also the products with span_rev > 0, we do it with a single, not-split, query
            if max_span_rev is None or max_span_rev > 0:
                product_list += self.get_list_products_with_conditions(token=token,
                                                                       instrument_name=instrument,
                                                                       product_type=product_type,
                                                                       src_name=source_name,
                                                                       e1_kev_value=e1_kev,
                                                                       e2_kev_value=e2_kev,
                                                                       rev1_value=rev1_value,
                                                                       rev2_value=rev2_value,
                                                                       min_span_rev_value=1,
                                                                       max_span_rev_value=max_span_rev)

        else:
            product_list = self.get_list_products_with_conditions(token=token,
                                                                  instrument_name=instrument,
                                                                  product_type=product_type,
                                                                  src_name=source_name,
                                                                  e1_kev_value=e1_kev,
                                                                  e2_kev_value=e2_kev,
                                                                  rev1_value=rev1_value,
                                                                  rev2_value=rev2_value,
                                                                  min_span_rev_value=min_span_rev,
                                                                  max_span_rev_value=max_span_rev)
        return product_list


    def get_list_products_with_conditions(self,
                                          token: str = None,
                                          **kwargs):

        """
        :param token: user token
        :param kwargs: keyword arguments representing the main parameters values used to generate the product. Amongst them,
               it is important to mention the following ones:
            * instrument_name: name of the instrument used for the generated product (e.g. isgri, jemx1)
            * product_type: type of product generated (e.g. lightcurve, image)
            * src_name: name of a single, or a list of, known sources (eg Crab, Cyg X-1)
            * others: other parameters used for the product. Not all the parameters are currently supported,
                but the list of the supported ones will be extended. E1_kev=25
        """

        params = {
            'token': token,
            **kwargs
        }

        res = requests.get(os.path.join(self.url, "get_data_product_list_with_conditions"),
                           params=params
                           )

        if res.status_code != 200:
            response_json = res.json()
            error_message = (f"An issue occurred while performing a request on the product gallery, "
                             f"the following error was returned:\n")
            if 'error_message' in response_json:
                error_message += '\n' + response_json['error_message']
                if 'drupal_helper_error_message' in response_json:
                    error_message += '-' + response_json['drupal_helper_error_message']
            else:
                error_message += res.text
            logger.warning(error_message)
        else:
            response_json = self._decode_res_json(res)

        return response_json


    def get_list_products_by_source_name(self,
                                         source_name: str = None,
                                         token: str = None):

        params = {
            'token': token,
            'src_name': source_name
        }

        res = requests.get(os.path.join(self.url, "get_data_product_list_by_source_name"),
                         params=params
                         )

        if res.status_code != 200:
            response_json = res.json()
            error_message = (f"An issue occurred while performing a request on the product gallery, "
                             f"the following error was returned:\n")
            if 'error_message' in response_json:
                error_message += '\n' + response_json['error_message']
                if 'drupal_helper_error_message' in response_json:
                    error_message += '-' + response_json['drupal_helper_error_message']
            else:
                error_message += res.text
            logger.warning(error_message)
        else:
            response_json = self._decode_res_json(res)

        return response_json

    def update_source_with_name(self,
                                 source_name: str = None,
                                 auto_update: bool = False,
                                 token: str = None,
                                 **kwargs):
        copied_kwargs = kwargs.copy()

        copied_kwargs['src_name'] = source_name

        params = {
            'token': token,
            'update_astro_entity': True,
            'auto_update': auto_update,
            **copied_kwargs
        }

        posting_msg = f'Updating an astro entity with title {source_name} on the gallery'

        logger.info(posting_msg)

        res = requests.post(os.path.join(self.url, "post_astro_entity_to_gallery"),
                            data=params,
                            )
        response_json = self._decode_res_json(res)

        if res.status_code != 200:
            res_obj = res.json()
            error_message = (f"An issue occurred while performing a request on the product gallery, "
                             f"the following error was returned:\n")
            if 'error_message' in res_obj:
                error_message += '\n' + res_obj['error_message']
                if 'drupal_helper_error_message' in res_obj:
                    error_message += ' - ' + res_obj['drupal_helper_error_message']
            else:
                error_message += res.text
            logger.warning(error_message)
        else:
            source_link = response_json['_links']['self']['href'].split("?")[0]
            returned_source_name = response_json['title'][0]['value']
            logger.info(
                f"Source with title {returned_source_name} successfully posted on the gallery, at the link {source_link}\n"
                f"Using the above link you can modify the newly created source in the future.\n")

        return response_json

    def update_observation_with_title(self,
                                      observation_title: str = None,
                                      yaml_file_path=None,
                                      token: str = None,
                                      observation_time_format: str = 'ISOT',
                                      create_new=False,
                                      **kwargs):
        copied_kwargs = kwargs.copy()

        # generate file obj
        files_obj = {}
        if yaml_file_path is not None:
            if isinstance(yaml_file_path, list):
                for yaml_path in yaml_file_path:
                    files_obj['yaml_file_' + str(yaml_file_path.index(yaml_path))] = open(yaml_path, 'rb')
            elif isinstance(yaml_file_path, str):
                files_obj['yaml_file'] = open(yaml_file_path, 'rb')

        copied_kwargs['T1'], copied_kwargs['T2'] = self.parse_observation_time_arg_product_gallery(
            t1=kwargs.get('T1', None), t2=kwargs.get('T2', None),
            observation_time_format=observation_time_format
        )

        obsid_arg = kwargs.get('obsid', None)
        if obsid_arg is not None:
            if isinstance(obsid_arg, list):
                obsid_list = ','.join(map(str, obsid_arg))
            else:
                obsid_list = obsid_arg

            copied_kwargs['obsid'] = obsid_list

        params = {
            'title': observation_title,
            'token': token,
            'update_observation': True,
            'create_new': create_new,
            **copied_kwargs
        }

        posting_msg = f'Posting an observation with title {observation_title} on the gallery'

        logger.info(posting_msg)

        res = requests.post(os.path.join(self.url, "post_observation_to_gallery"),
                            data=params,
                            files=files_obj
                            )
        response_json = self._decode_res_json(res)

        if res.status_code != 200:
            res_obj = res.json()
            error_message = (f"An issue occurred while performing a request on the product gallery, "
                             f"the following error was returned:\n")
            if 'error_message' in res_obj:
                error_message += '\n' + res_obj['error_message']
                if 'drupal_helper_error_message' in res_obj:
                    error_message += '-' + res_obj['drupal_helper_error_message']
            else:
                error_message += res.text
            logger.warning(error_message)
        else:
            observation_link = response_json['_links']['self']['href'].split("?")[0]
            observation_title = response_json['title'][0]['value']
            logger.info(
                f"Observation with title {observation_title} successfully posted on the gallery, at the link {observation_link}\n"
                f"Using the above link you can modify the newly created observation in the future.\n")

        return response_json

    def post_observation_to_gallery(self,
                                    observation_title: str = None,
                                    yaml_file_path=None,
                                    token: str = None,
                                    observation_time_format: str = 'ISOT',
                                    **kwargs):
        copied_kwargs = kwargs.copy()

        # generate file obj
        files_obj = {}
        if yaml_file_path is not None:
            if isinstance(yaml_file_path, list):
                for yaml_path in yaml_file_path:
                    files_obj['yaml_file_' + str(yaml_file_path.index(yaml_path))] = open(yaml_path, 'rb')
            elif isinstance(yaml_file_path, str):
                files_obj['yaml_file'] = open(yaml_file_path, 'rb')

        copied_kwargs['T1'], copied_kwargs['T2'] = self.parse_observation_time_arg_product_gallery(
            t1=kwargs.get('T1', None), t2=kwargs.get('T2', None),
            observation_time_format=observation_time_format
        )

        obsid_arg = kwargs.get('obsid', None)
        if obsid_arg is not None:
            if isinstance(obsid_arg, list):
                obsid_list = ','.join(map(str, obsid_arg))
            else:
                obsid_list = obsid_arg

            copied_kwargs['obsid'] = obsid_list

        params = {
            'title': observation_title,
            'token': token,
            **copied_kwargs
        }

        posting_msg = f'Posting an observation with title {observation_title} on the gallery'

        logger.info(posting_msg)

        res = requests.post(os.path.join(self.url, "post_observation_to_gallery"),
                            data=params,
                            files=files_obj
                            )

        if res.status_code != 200:
            error_message = (f"An issue occurred while performing a request on the product gallery, "
                             f"the following error was returned:\n")
            try:
                response_json = res.json()
            except json.decoder.JSONDecodeError:
                error_msg = res.text
                response_json = {'error_message': error_msg}
                logger.debug(response_json)

            if 'error_message' in response_json:
                error_message += '\n' + response_json['error_message']
                if 'drupal_helper_error_message' in response_json:
                    error_message += '-' + response_json['drupal_helper_error_message']
            else:
                error_message += res.text
            logger.warning(error_message)
        else:
            response_json = self._decode_res_json(res)
            observation_link = response_json['_links']['self']['href'].split("?")[0]
            observation_title = response_json['title'][0]['value']
            logger.info(f"Observation with title {observation_title} successfully posted on the gallery, at the link {observation_link}\n"
                        f"Using the above link you can modify the newly created observation in the future.\n")

        return response_json

    def delete_data_product_from_gallery_via_product_id(self,
                                                        product_id: str,
                                                        token: typing.Optional[str] = None):
        """

        :param product_id: identifier of a data product assigned by the user, this can be used during the creation of a new data-product,
               as well as to identify an already existing one and update it with the arguments provided by the user
        :param token: user token
        """
        if token is None:
            token = self.token

        params = {
            'content_type': 'data_product',
            'token': token,
            'product_id': product_id,
        }

        posting_msg = f'Deleting from the gallery a product with product_id {product_id}'
        logger.info(posting_msg)

        res = requests.post("%s/delete_product_to_gallery" % self.url,
                            data=params
                            )

        if res.status_code != 200:
            error_message = (f"An issue occurred while performing a request on the product gallery, "
                             f"the following error was returned:\n")
            try:
                response_json = res.json()
            except json.decoder.JSONDecodeError:
                error_msg = res.text
                response_json = {'error_message': error_msg}
                logger.debug(response_json)

            if 'error_message' in response_json:
                error_message += '\n' + response_json['error_message']
                if 'drupal_helper_error_message' in response_json:
                    error_message += '-' + response_json['drupal_helper_error_message']

            logger.warning(error_message)
        else:
            response_json = self._decode_res_json(res)
            logger.info(f"Product successfully deleted from the gallery")

        return response_json


    def post_data_product_to_gallery(self,
                                     product_title: typing.Optional[str] = None,
                                     product_id: str = None,
                                     observation_id: typing.Optional[str] = None,
                                     gallery_image_path: typing.Optional[str] = None,
                                     fits_file_path=None,
                                     yaml_file_path=None,
                                     token: typing.Optional[str] = None,
                                     insert_new_source: bool = False,
                                     validate_source: bool = False,
                                     force_insert_not_valid_new_source: bool = False,
                                     apply_fields_source_resolution: bool = False,
                                     html_image: str = None,
                                     in_evidence: bool = False,
                                     observation_time_format: str = 'ISOT',
                                     **kwargs):
        """

        :param product_title: title to assign to the product, in case this is not provided, then a title is
               automatically built using the name of the source and the type of product
        :param product_id: identifier of a data product assigned by the user, this can be used during the creation of a new data-product,
               as well as to identify an already existing one and update it with the arguments provided by the user
        :param observation_id: this can be indicated in two different ways
            * by specifying the id of an already present observation (eg 'test observation')
            * by specifying the time range, in particular the value of T1 and T2
        :param observation_time_format: format of the time values for an observation (i.e. T1 and T2), default to ISOT,
               (e.g. '2003-03-15T23:27:40.0'), also the MJD format is supported
        :param in_evidence: a boolean value specifying if the product will be in evidence over thew page of the correspondent
            source
        :param gallery_image_path: path of the generated image and to be uploaded over the gallery
        :param fits_file_path: a list of fits file links used for the generation of the product to upload over the gallery
        :param yaml_file_path: a list of yaml file links to be attached to the observation of the product to upload over the gallery
        :param token: user token
        :param insert_new_source: a boolean value specifying if, in case the sources that are passed as parameters and
               are not available on the product gallery, will be created and then used for the new data product
        :param validate_source: a boolean value to specify if, in case the sources that are passed as parameters
               will be validated against an online service. In case the validation fails the source won't be inserted as
               a parameter for the data product and a warning for the user will be generated (unless this is intentionally
               specified setting to `True` the boolean parameter **force_insert_not_valid_new_sources** described below)
        :param force_insert_not_valid_new_source: a boolean value to specify if, in case the validation of the sources passed as
               parameters fails, those should be in any case provided as a parameter for the data product
        :param apply_fields_source_resolution: a boolean value to specify if, in case only a single source is passed within the
                parameters and then successfully validated, to apply the parameters values returned from the validation
                (an example of these parameters are RA and DEC), default to False
        :param html_image: field used to upload an image encapsulated within an html block generated using external
               tools (e.g. bokeh)
        :param kwargs: keyword arguments representing the main parameters values used to generate the product. Amongst them,
               it is important to mention the following ones:
            * instrument: name of the instrument used for the generated product (e.g. isgri, jemx1)
            * product_type: type of product generated (e.g. isgri_lc, jemx_image)
            * src_name: name of a single, or a list of, known sources (eg Crab, Cyg X-1)
            * others: other parameters used for the product. Not all the parameters are currently supported,
                but the list of the supported ones will be extended. RA=25

        """

        # apply policy for the specific data product
        # use the product_type, if provided, and apply the policy, if applicable
        self.check_gallery_data_product_policy(token=token, **kwargs)

        copied_kwargs = kwargs.copy()

        # generate file obj
        files_obj = {}
        tmp_path_html_folder_path = None
        if gallery_image_path is not None:
            files_obj['img'] = open(gallery_image_path, 'rb')
        if fits_file_path is not None:
            if isinstance(fits_file_path, list):
                for fits_path in fits_file_path:
                    files_obj['fits_file_' + str(fits_file_path.index(fits_path))] = open(fits_path, 'rb')
            elif isinstance(fits_file_path, str):
                files_obj['fits_file'] = open(fits_file_path, 'rb')
        if yaml_file_path is not None:
            if isinstance(yaml_file_path, list):
                for yaml_path in yaml_file_path:
                    files_obj['yaml_file_' + str(yaml_file_path.index(yaml_path))] = open(yaml_path, 'rb')
            elif isinstance(yaml_file_path, str):
                files_obj['yaml_file'] = open(yaml_file_path, 'rb')
        if html_image is not None:
            html_image_hash = hashlib.md5(html_image.encode()).hexdigest()[:8]
            tmp_path_html_folder_path = tempfile.mkdtemp(suffix="gallery_temp_files")
            tmp_path_html_file_path = os.path.join(tmp_path_html_folder_path, f'additional_html_file_{html_image_hash}.html')
            with open(tmp_path_html_file_path, "w") as f_html:
                f_html.write(html_image)

            files_obj['html_file'] = open(tmp_path_html_file_path, 'rb')

        copied_kwargs['T1'], copied_kwargs['T2'] = self.parse_observation_time_arg_product_gallery(
            t1=kwargs.get('T1', None), t2=kwargs.get('T2', None),
            observation_time_format=observation_time_format
        )

        # validate source
        src_name_arg = kwargs.get('src_name', None)
        copied_src_name_arg = None
        entities_portal_link_list = None
        object_ids_list = None
        object_type_list = None
        source_coord_list = None
        if src_name_arg is not None and validate_source:

            if isinstance(src_name_arg, str):
                src_name_list = src_name_arg.split(',')
            else:
                src_name_list = src_name_arg

            for src_name in src_name_list:
                resolved_source = True
                entity_portal_link = None
                object_ids = None
                object_type = None
                source_coord = {}
                # remove any underscore (following the logic of the resolver) and use the edited one
                src_name_edited = src_name.replace('_', ' ')
                resolved_obj = self.resolve_source(src_name=src_name_edited, token=token)
                if resolved_obj is not None:
                    msg = ''
                    if 'message' in resolved_obj:
                        if 'could not be resolved' in resolved_obj['message']:
                            resolved_source = False
                            msg = f'\nSource {src_name} could not be validated'
                        elif 'successfully resolved' in resolved_obj['message']:
                            resolved_source = True
                            msg = f'\nSource {src_name} was successfully validated'
                    msg += '\n'
                    logger.info(msg)
                    if 'RA' in resolved_obj:
                        RA = Angle(resolved_obj["RA"], unit='degree')
                        source_coord['source_ra'] = RA.deg
                        if apply_fields_source_resolution:
                            # TODO to be discussed
                            if len(src_name_list) == 1:
                                copied_kwargs['RA'] = RA.deg
                    if 'DEC' in resolved_obj:
                        DEC = Angle(resolved_obj["DEC"], unit='degree')
                        source_coord['source_dec'] = DEC.deg
                        if apply_fields_source_resolution:
                            # TODO to be discussed
                            if len(src_name_list) == 1:
                                copied_kwargs['DEC'] = DEC.deg
                    if 'entity_portal_link' in resolved_obj:
                        entity_portal_link = resolved_obj['entity_portal_link']
                        # copied_kwargs['entity_portal_link'] = resolved_obj['entity_portal_link']
                    if 'object_type' in resolved_obj:
                        object_type = resolved_obj['object_type']
                    if 'object_ids' in resolved_obj:
                        object_ids = resolved_obj['object_ids']
                else:
                    logger.warning(f"{src_name} could not be validated")
                    resolved_source = False

                if not resolved_source and not force_insert_not_valid_new_source:
                    # a source won't be added
                    logger.warning(f"the specified source will not be added")
                else:
                    if copied_src_name_arg is None:
                        copied_src_name_arg = []
                    copied_src_name_arg.append(src_name)

                    if entities_portal_link_list is None:
                        entities_portal_link_list = []
                    if entity_portal_link is None:
                        entity_portal_link = ''
                    entities_portal_link_list.append(entity_portal_link)

                    if object_ids_list is None:
                        object_ids_list = []
                    if object_ids is None:
                        object_ids = []
                    object_ids_list.append(object_ids)

                    if object_type_list is None:
                        object_type_list = []
                    if object_type is None:
                        object_type = ''
                    object_type_list.append(object_type)

                    if source_coord_list is None:
                        source_coord_list = []
                    source_coord_list.append(source_coord)

        else:
            copied_src_name_arg = src_name_arg

        if copied_src_name_arg is not None:
            if isinstance(copied_src_name_arg, list):
                copied_kwargs['src_name'] = ','.join(copied_src_name_arg)
            else:
                copied_kwargs['src_name'] = copied_src_name_arg
        else:
            copied_kwargs.pop('src_name', None)

        if entities_portal_link_list is not None:
            if isinstance(entities_portal_link_list, list):
                copied_kwargs['entity_portal_link_list'] = ','.join(entities_portal_link_list)
            else:
                copied_kwargs['entity_portal_link_list'] = entities_portal_link_list

        if source_coord_list is not None:
            copied_kwargs['source_coord_list'] = json.dumps(source_coord_list)

        if object_ids_list is not None:
            copied_kwargs['object_ids_list'] = json.dumps(object_ids_list)

        if object_type_list is not None:
            copied_kwargs['object_type_list'] = json.dumps(object_type_list)

        copied_kwargs['in_evidence'] = 0 if not in_evidence else 1

        params = {
            'content_type': 'data_product',
            'product_title': product_title,
            'observation_id': observation_id,
            'token': token,
            'insert_new_source': insert_new_source,
            'product_id': product_id,
            **copied_kwargs
        }

        posting_msg = 'Posting a product'
        if product_id is not None:
            posting_msg += f' with product_id {product_id}'
        posting_msg += ' on the gallery'

        logger.info(posting_msg)

        res = requests.post("%s/post_product_to_gallery" % self.url,
                            data=params,
                            files=files_obj
                            )

        if res.status_code != 200:
            error_message = (f"An issue occurred while performing a request on the product gallery, "
                             f"the following error was returned:\n")
            try:
                response_json = res.json()
            except json.decoder.JSONDecodeError:
                error_msg = res.text
                response_json = {'error_message': error_msg}
                logger.debug(response_json)

            if 'error_message' in response_json:
                error_message += '\n' + response_json['error_message']
                if 'drupal_helper_error_message' in response_json:
                    error_message += '-' + response_json['drupal_helper_error_message']

            logger.warning(error_message)
        else:
            response_json = self._decode_res_json(res)
            action = 'posted'
            if product_id is not None and response_json['created'][0]['value'] != response_json['changed'][0]['value']:
                action = 'updated'

            self.check_missing_parameters_data_product(response_json, token=token, **kwargs)

            product_posted_link = response_json['_links']['self']['href'].split("?")[0]
            logger.info(f"Product successfully {action} on the gallery, at the link {product_posted_link}\n"
                        f"Using the above link you can modify the newly created product in the future.\n"
                        f"For example, you will be able to change the instrument as well as the product type.\n")

        if tmp_path_html_folder_path is not None and os.path.exists(tmp_path_html_folder_path):
            logger.info(f'removing tmp_path_html_folder_path={tmp_path_html_folder_path} created for temporary files')
            try:
                shutil.rmtree(tmp_path_html_folder_path)
            except OSError as e:
                logger.error(f'unable to remove temporary directory {tmp_path_html_folder_path} !')

        return response_json

    def resolve_source(self,
                       src_name: typing.Optional[str] = None,
                       token: typing.Optional[str] = None):
        resolved_obj = None
        if src_name is not None and src_name != '':
            params = {
                'name': src_name,
                'token': token
            }

            logger.info(f"Searching the object {src_name}\n")

            res = requests.get("%s/resolve_name" % self.url,
                               params={**params}
                               )
            resolved_obj = self._decode_res_json(res)

            if resolved_obj is not None and 'message' in resolved_obj:
                logger.info(f'{resolved_obj["message"]}')
        else:
            logger.info("Please provide the name of the source\n")

        return resolved_obj

    def convert_ijd_to_utc(self, t_ijd):
        # TODO to reply on a dedicated service in the dispatcher
        res = requests.get(f"https://www.astro.unige.ch/mmoda/dispatch-data/gw/timesystem/api/v1.0/converttime/IJD/{t_ijd}/UTC")
        if res.status_code == 200:
            t_utc = res.text
            return t_utc
        else:
            return None

    def convert_mjd_to_utc(self, t_mjd):
        # TODO to reply on a dedicated service in the dispatcher
        t_utc = self.convert_ijd_to_utc(t_mjd - 51544)
        return t_utc

    def check_gallery_data_product_policy(self,
                                          token: typing.Optional[str] = None,
                                          **kwargs):
        product_type = kwargs.get('product_type', None)
        if product_type is not None and product_type != '':
            params = {
                'term': product_type,
                'group': 'products',
                'token': token
            }

            logger.info(f"Applying the policy for the product {product_type}\n")

            res = requests.get("%s/get_parents_term" % self.url,
                               params={**params}
                               )
            parents_term_list = self._decode_res_json(res)

            if parents_term_list is not None and isinstance(parents_term_list, list):
                # loop over the available ODAProduct from the plot_tools and find the correspondent one
                for name, c in inspect.getmembers(plot_tools, inspect.isclass):
                    if issubclass(c, plot_tools.OdaProduct) \
                            and hasattr(c, 'name') and c.name is not None and c.name in parents_term_list \
                            and hasattr(c, 'check_product_for_gallery'):
                        return c.check_product_for_gallery(**kwargs)
            logger.info(f"A policy for the product_type {product_type} could not be applied\n")
        else:
            logger.info("A product_type has not been provided for the given data product, "
                        "therefore no policy will be verified\n")

        return True

    def check_missing_parameters_data_product(self, response, token: typing.Optional[str] = None, **kwargs):
        missing_instrument = True
        instrument_used = None
        missing_product_type = True
        if '_links' in response:
            for field_link in response['_links']:
                field = field_link.split('/')[-1]
                if field == 'field_instrumentused':
                    missing_instrument = False
                    instrument_used = kwargs.get('instrument', None)
                elif field == 'field_data_product_type':
                    missing_product_type = False

        if missing_instrument:
            list_instruments = self.get_list_terms_gallery(group='instruments', token=token)
            logger.info(f'\nWe noticed no instrument has been specified, the following are available:\n'
                        f'{list_instruments}\n'
                        'Please remember that this can be set at a later stage by editing the newly created data product.\n')

        if missing_product_type:
            if not missing_instrument and instrument_used is not None:
                list_instrument_data_products = self.get_list_terms_gallery(group='products', parent=instrument_used,
                                                                            token=token)
                if list_instrument_data_products is not None:
                    logger.info(f'\nWe noticed no product type has been specified,\n'
                                f'for the instrument {instrument_used}, the following products are available:\n'
                                f'{list_instrument_data_products}\n'
                                'Please remember that this can be set at a later stage by editing the newly created data product.\n')