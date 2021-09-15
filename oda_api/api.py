
from __future__ import absolute_import, division, print_function
from json.decoder import JSONDecodeError
from astropy.table import Table
from .data_products import NumpyDataProduct, BinaryData, ApiCatalog

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)


__author__ = "Andrea Tramacere, Volodymyr Savchenko"

import warnings
import requests
import ast
import json

try:
    #compatibility in some remaining environments
    import simplejson # type: ignore
except ImportError:
    import json as simplejson # type: ignore

import random
import string
import time
import os
import inspect
import sys
from astropy.io import ascii
import copy
import pickle
from . import __version__
from . import custom_formatters
from . import colors as C
from itertools import cycle
import numpy as np
import traceback
from jsonschema import validate as validate_json

import oda_api.token
import oda_api.misc_helpers

import logging

logger = logging.getLogger("oda_api.api")


__all__ = ['Request', 'NoTraceBackWithLineNumber',
           'NoTraceBackWithLineNumber', 'RemoteException', 'DispatcherAPI']


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
        # sys.exit(self)


class UserError(Exception):
    pass


class RemoteException(NoTraceBackWithLineNumber):

    def __init__(self, message='Remote analysis exception', debug_message=''):
        super(RemoteException, self).__init__(message)
        self.message = message
        self.debug_message = debug_message

    def __repr__(self):
        return f"RemoteException: {self.message}, {self.debug_message}"


class FailedToFindAnyUsefulResults(RemoteException):
    pass


class UnexpectedDispatcherStatusCode(RemoteException):
    pass

class RequestNotUnderstood(Exception):
    def __init__(self, details_json) -> None:
        self.details_json = details_json

    def __repr__(self) -> str:
        return f"[ RequestNotUnderstood: {self.details_json['error']} ]"

    def __str__(self) -> str:
        return repr(self)

class Unauthorized(RemoteException):
    pass

class URLRedirected(Exception):
    pass


exception_by_message = {
    'failed: get dataserver products ': FailedToFindAnyUsefulResults
}


def safe_run(func):

    def func_wrapper(*args, **kwargs):
        logger = logging.getLogger("oda_api.api." + func.__name__)

        self = args[0]  # because it really is

        n_tries_left = self.n_max_tries
        retry_sleep_s = self.retry_sleep_s
        while True:
            try:
                return func(*args, **kwargs)
            except UserError as e:
                logger.exception("user error: %s", e)
                raise
            except Unauthorized:
                raise
            except RequestNotUnderstood:
                raise
            except UnexpectedDispatcherStatusCode as e:
                message = f'unexpected status code: {e}'
                raise
            except (ConnectionError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                message = ''
                message += '\nunable to complete API call'
                message += '\nin ' + str(func) + ' called with:'
                message += '\n... ' + ", ".join([str(arg) for arg in args])
                message += '\n... ' + \
                    ", ".join([k+": "+str(v) for k, v in kwargs])
                message += '\npossible causes:'
                message += '\n- connection error'
                message += '\n- error on the remote server'
                message += '\n exception message: '
                message += '\n\n%s\n' % e
                message += traceback.format_exc()

                n_tries_left -= 1

                if n_tries_left > 0:
                    logger.warning("problem in API call, %i tries left:\n%s\n sleeping %i seconds until retry",
                                   n_tries_left, message, retry_sleep_s)
                    time.sleep(retry_sleep_s)
            
            raise RemoteException(
                message=message
            )

    return func_wrapper


class DispatcherAPI:

    # allowing token discovery by default changes the user interface in some cases, 
    # but in desirable way
    token_discovery_methods = None

    def __init__(self,
                 instrument='mock',
                 url=None,
                 run_analysis_handle='run_analysis',
                 host=None,
                 port=None,
                 cookies=None,
                 protocol="https",
                 wait=True,
                 n_max_tries=20,
                 session_id=None,
                 ):

        if url is None:
            url = "https://www.astro.unige.ch/mmoda/dispatch-data"

        if host is not None:
            msg = '\n'
            msg += '----------------------------------------------------------------------------\n'
            msg += 'support for the parameter host will end soon \n'
            msg += 'please use "url" instead of "host" while providing dispatcher URL \n'
            msg += '----------------------------------------------------------------------------\n'
            warnings.warn(msg, DeprecationWarning)
            self.url = host

            #TODO: disregard this, but leave parameter for compatibility
            if host.startswith('http'):
                self.url = host
            else:
                if protocol != 'http' and protocol != 'https':
                    raise UserError('protocol must be either http or https')
                else:
                    self.url = protocol + "://" + host
        else:
            if not oda_api.misc_helpers.validate_url(url):
                raise UserError(f'{url} is not a valid url. \n'
                                'A valid url should be like `https://www.astro.unige.ch/mmoda/dispatch-data`, '
                                'you might verify if, for example, a valid schema is provided, '
                                'i.e. url should start with http:// or https:// .\n'
                                'Please check it and try to issue again the request')

            self.url = url

        if session_id is not None:
            self._session_id = session_id

        self.logger = logger.getChild(self.__class__.__name__.lower())
        self.progress_logger = self.logger.getChild("progress")

        self._carriage_return_progress = False

        self.run_analysis_handle = run_analysis_handle

        self.wait = wait

        self.strict_parameter_check = False

        self.cookies = cookies
        self.set_instr(instrument)

        self.n_max_tries = n_max_tries
        self.retry_sleep_s = 5

        if port is not None:
            self.logger.warning(
                "please use 'url' to specify entire URL, no need to provide port separately")

        self._progress_iter = cycle(['|', '/', '-', '\\'])

        # TODO this should really be just swagger/bravado; or at least derived from resources
        self.dispatcher_response_schema = {
            'type': 'object',
                    'properties': {
                        'exit_status': {
                            'type': 'object',
                            'properties': {
                                    'status': {'type': 'number'},
                            },
                        },
                        'query_status': {'type': 'string'},
                        'job_monitor': {
                            'type': 'object',
                            'properties': {
                                    'job_id': {'type': 'string'},
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

    def generate_session_id(self, size=16):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size))

    @property
    def session_id(self):
        if not hasattr(self, '_session_id'):
            self._session_id = self.generate_session_id()

        return self._session_id

    def set_instr(self, instrument):
        self.instrument = instrument
        self.custom_progress_formatter = custom_formatters.find_custom_formatter(
            instrument)

    def _progress_bar(self, info=''):
        if self._carriage_return_progress:
            c_r = '\x1b[80D' + '\x1b[K'  # TODO: this does not really work now
        else:
            c_r = ''

        self.progress_logger.info(
            f"{c_r}{C.GREY}\r {next(self._progress_iter)} the job is working remotely, please wait {info}{C.NC}")

    def format_custom_progress(self, full_report_dict_list):
        F = getattr(self, 'custom_progress_formatter', None)

        if F is not None:
            return F(full_report_dict_list)

        return ""

    def note_request_time(self):
        self.request_stats = getattr(self, 'request_stats', [])
        self.request_stats.append(
            self.last_request_t_complete-self.last_request_t0)

    @property
    def preferred_request_method(self):
        return getattr(self, '_preferred_request_method', 'GET')

    @preferred_request_method.setter
    def preferred_request_method(self, v):
        allowed_request_methods = ['POST', 'GET']
        if v in allowed_request_methods:
            self._preferred_request_method = v
        else:
            raise RuntimeError(f'unable to set preferred request method to {v}, allowed {allowed_request_methods}')

    @property
    def selected_request_method(self):
        if self.parameters_dict_payload is not None:
            request_size = len(json.dumps(self.parameters_dict_payload))
            max_get_method_size = getattr(self, 'max_get_method_size', 1000)

            self.logger.debug('payload size %s, max for GET is %s', request_size, max_get_method_size)

            if request_size > max_get_method_size:
                self.logger.debug(
                    'switching to POST request due to large payload: %s > %s', request_size, max_get_method_size)
                return 'POST'

        return self.preferred_request_method

    def request_to_json(self, verbose=False):
        self.progress_logger.info(
            f'- waiting for remote response (since {time.strftime("%Y-%m-%d %H:%M:%S")}), please wait for {self.url}/{self.run_analysis_handle}')

        try:
            timeout = getattr(self, 'timeout', 120)

            self.last_request_t0 = time.time()

            url = "%s/%s" % (self.url, self.run_analysis_handle)

            if self.selected_request_method == 'GET':
                response = requests.get(
                    url,
                    params=self.parameters_dict_payload,
                    cookies=self.cookies,
                    headers={
                        'Request-Timeout': str(timeout),
                        'Connection-Timeout': str(timeout),
                    },
                    timeout=timeout,
                    allow_redirects=False
                )
            elif self.selected_request_method == 'POST':
                response = requests.post(
                    url,
                    data=self.parameters_dict_payload,
                    cookies=self.cookies,
                    headers={
                        'Request-Timeout': str(timeout),
                        'Connection-Timeout': str(timeout),
                    },
                    timeout=timeout,
                    allow_redirects=False
                )                
            else:
                NotImplementedError

            if response.status_code in (301, 302):
                # we can not automatically redirect with POST due to unexpected behavior of requests module
                # there is a very strange and mysterious story about this:
                # * https://github.com/psf/requests/blob/1e5fad7433772b648fcbc921e2a79de5c4c6be8b/requests/sessions.py#L329-L332
                # * https://github.com/psf/requests/issues/1704
                # to avoid confusion, we will instruct the user to change the code:
                raise URLRedirected(f"the service was moved{' permanently' if response.status_code == 301 else ''}, "
                                    f"please reinitialize DispatcherAPI with \"{response.headers['Location']}\" (you asked for \"{url}\")")

            if response.status_code == 403:
                try:
                    response_json = response.json()                                    
                except (json.decoder.JSONDecodeError, simplejson.errors.JSONDecodeError):
                    raise Unauthorized(f"undecodable: {response.text}")

                try:
                    raise Unauthorized(response_json['exit_status']['message'])
                except KeyError:
                    raise Unauthorized(response_json['error'])
            
            if response.status_code == 400:
                raise RequestNotUnderstood(
                    response.json())

            if response.status_code != 200:
                raise UnexpectedDispatcherStatusCode(
                    f"status: {response.status_code}, raw: {response.text}")

            self.last_request_t_complete = time.time()

            self.note_request_time()

            response_json = self._decode_res_json(response)

            validate_json(response_json, self.dispatcher_response_schema)
            
            self.returned_analysis_parameters = response_json['products'].get('analysis_parameters', None)

            return response_json
        except json.decoder.JSONDecodeError as e:
            self.logger.error(
                f"{C.RED}{C.BOLD}unable to decode json from response:{C.NC}")
            self.logger.error(f"{C.RED}{response.text}{C.NC}")
            raise

    def returned_analysis_parameters_consistency(self):    
        mismatching_parameters = []
        for k in self.parameters_dict.keys():
            # these do not correspond to meaning
            ''' 
            The dry_run parameter is not actually considered within the oda_api,
            but we keep it here for  consistency.
            As discussed in: 
            * https://github.com/oda-hub/oda_api/pull/85
            * https://github.com/oda-hub/oda_api/issues/84
            '''
            if k in ['query_status', 'off_line', 'verbose', 'dry_run']:
                continue

            returned = self.returned_analysis_parameters.get(k, None)
            requested = self.parameters_dict.get(k, None)
            if str(returned) != str(requested):
                mismatching_parameters.append(f"{k}: returned {returned} != requested {requested}")

        if mismatching_parameters != []:
            raise RuntimeError(f"dispatcher return different parameters: {'; '.join(mismatching_parameters)}")
    
    @property
    def parameters_dict(self):
        """
        as provided in request, not modified by state changes
        """
        return getattr(self, '_parameters_dict', None)

    @parameters_dict.setter
    def parameters_dict(self, value):
        self._parameters_dict = value
        self.query_status = 'prepared'

    @property
    def parameters_dict_payload(self):
        if self.parameters_dict is None:
            return None

        p = {
            **self.parameters_dict,
            'api': 'True',
            'oda_api_version': __version__,
        }

        if self.is_submitted:
             return {
                 **p,
                'job_id': self.job_id,
                'query_status': self.query_status,
             }
        else:
             return p

    @parameters_dict_payload.setter
    def parameters_dict_payload(self, value):
        raise UserError(
            "please set parameters_dict and not parameters_dict_payload")

    @property
    def job_id(self):
        return getattr(self, '_job_id', None)

    @job_id.setter
    def job_id(self, new_job_id):
        self._job_id = new_job_id

    @property
    def query_status(self):
        return getattr(self, '_query_status', 'not-prepared')

    @query_status.setter
    def query_status(self, new_status):
        possible_status = [
            "not-prepared",
            "prepared",
            "submitted",
            "progress",
            "done",
            "ready",
            "failed",
        ]

        if new_status in possible_status:
            self._query_status = new_status
        else:
            raise RuntimeError(
                f"unable to set status to {new_status}, possible values are {possible_status}")

    @property
    def is_submitted(self):
        return self.query_status not in ['prepared', 'not-prepared']

    @property
    def is_prepared(self):
        return self.query_status not in ['not-prepared']

    @property
    def is_done(self):
        return self.query_status in ['done']

    @property
    def is_complete(self):
        return self.query_status in ['done', 'failed']

    @property
    def is_failed(self):
        return self.query_status in ['failed']

    @safe_run
    def poll(self, verbose=None, silent=None):
        """
        Updates status of query at the remote server

        Relies on self.parameters_dict to set parameters for request

        Relies on self.query_status and self.job_id, which is created as necessary and submitted in paylad
        """

        if verbose is not None or silent is not None:
            self.logger.warning(
                "please set verbosity with standard python \"logging\" module")
            self.logger.warning("these option will be removed in the future")
            if verbose:
                if silent:
                    self.logger.error(
                        "can not be verbose and silent at once! ignoring verbose and silent options")
                else:
                    self.logger.warning(
                        "legacy verbose option: setting oda_api logging level to DEBUG and one stream handler")
                    logging.getLogger('oda_api').setLevel(logging.DEBUG)
                    logging.getLogger('oda_api').addHandler(
                        logging.StreamHandler())
            else:
                if silent:
                    self.logger.warning(
                        "legacy silent option, no special logging config - silent by default")
                else:
                    self.logger.warning(
                        "legacy verbose but not silet option: setting oda_api logging level to INFO and one stream handler")
                    logging.getLogger('oda_api').setLevel(logging.INFO)
                    logging.getLogger('oda_api').addHandler(
                        logging.StreamHandler())

        if not self.is_prepared:
            raise UserError(
                f"can not poll query before parameters are set with {self}.request")

        # >
        self.response_json = self.request_to_json()
        # <
            
        logger.info("session: %s job: %s", self.response_json['job_monitor']['session_id'], self.response_json['job_monitor']['job_id'])

        if 'query_status' not in self.response_json:
            logger.error(json.dumps(self.response_json, indent=4))
            raise RuntimeError(
                f"request json does not contain query_status: {self.response_json}")

        if self.response_json.get('query_status') != self.query_status:
            self.logger.info(
                f"\n... query status {C.PURPLE}{self.query_status}{C.NC} => {C.PURPLE}{self.response_json.get('query_status')}{C.NC}")

            self.query_status = self.response_json.get('query_status')

        returned_job_id = self.response_json['job_monitor']['job_id']

        if self.job_id is None:
            self.job_id = returned_job_id

            self.logger.info(
                f"... assigned job id: {C.BROWN}{self.job_id}{C.NC}")
        else:
            if self.response_json['query_status'] != self.query_status:
                raise RuntimeError(f"request returns query_status {self.response_json['query_status']} != recorded query_status {self.query_status}"
                                   f"this should not happen! Server must be misbehaving, or client forgot correct query_status")

            if self.job_id != returned_job_id:
                raise RuntimeError(f"request returns job_id {returned_job_id} != recorded job_id {self.job_id}"
                                   f"this should not happen! Server must be misbehaving, or client forgot correct job id")


        if self.query_status == 'done':
            self.logger.info(
                f"\033[32mquery COMPLETED SUCCESSFULLY (state {self.query_status})\033[0m")

        elif self.query_status == 'failed':
            self.logger.info(
                f"\033[31mquery COMPLETED with FAILURE (state {self.query_status})\033[0m")

        else:
            self.show_progress()

        if self.is_complete:
            # TODO: something raising here does not help
            self.logger.debug("poll returing data: complete")
            return DataCollection.from_response_json(self.response_json, self.instrument, self.product)

    def show_progress(self):
        full_report_dict_list = self.response_json['job_monitor'].get(
            'full_report_dict_list', [])

        info = 'status=%s job_id=%s in %d messages since %d seconds (%.2g/%.2g)' % (
            self.query_status,
            str(self.job_id)[:8],
            len(full_report_dict_list),
            time.time() - self.t0,
            np.mean(self.request_stats),
            np.max(self.request_stats),
        )

        custom_info = self.format_custom_progress(full_report_dict_list)
        if custom_info != "":
            info += "; " + custom_info

        self._progress_bar(info=info)

    def print_parameters(self):
        for k, v in self.parameters_dict.items():
            self.logger.info(f"- {C.BLUE}{k}: {v}{C.NC}")

    @safe_run
    def request(self, parameters_dict, handle=None, url=None, wait=None, quiet=True):
        """
        sets request parameters, optionally polls them in a loop
        """

        if wait is not None:
            self.logger.warning("overriding wait mode from request")
            self.wait = wait

        if url is not None:
            self.logger.warning("overriding dispatcher URL from request!")
            self.url = url

        if handle is not None:
            self.logger.warning(
                "overriding dispatcher handle from request not allowed, ignored!")

        self.parameters_dict = parameters_dict

        if 'scw_list' in self.parameters_dict.keys():
            self.logger.debug(self.parameters_dict['scw_list'])

        self.set_instr(self.parameters_dict.get('instrument', self.instrument))

        if not quiet:
            self.print_parameters()

        self.t0 = time.time()

        while True:
            self.poll()

            if not self.wait:
                self.logger.info("non-waiting dispatcher: terminating")
                return

            if self.is_complete:
                self.logger.info("query complete: terminating")
                return

            time.sleep(1)

    def process_failure(self):
        if self.response_json['exit_status']['status'] != 0:
            self.failure_report(self.response_json)

        if self.query_status != 'failed':
            self.logger('query done succesfully!')
        else:
            logger.error("exception, message: \"%s\"",
                         self.response_json['exit_status']['message'])
            logger.error("have exception message: keys \"%s\"",
                         exception_by_message.keys())
            raise exception_by_message.get(self.response_json['exit_status']['message'], RemoteException)(
                message=self.response_json['exit_status']['message'],
                debug_message=self.response_json['exit_status']['error_message']
            )

    def failure_report(self, res_json):
        self.logger.error('query failed!')
        self.logger.error('Remote server message:-> %s',
                          res_json['exit_status']['message'])
        self.logger.error('Remote server error_message-> %s',
                          res_json['exit_status']['error_message'])
        self.logger.error('Remote server debug_message-> %s',
                          res_json['exit_status']['debug_message'])

    def dig_list(self, b, only_prod=False):
        if isinstance(b, (set, tuple, list)):
            for c in b:
                self.dig_list(c)
        else:
            try:
                original_b = b
                b = ast.literal_eval(str(b))  # uh
            except Exception as e:
                logger.debug(
                    "dig_list unable to literal_eval %s; problem %s", b, e)
                return str(b)

            if isinstance(b, dict):
                _s = ''
                for k, v in b.items():

                    if 'query_name' == k or 'instrument' == k and only_prod == False:
                        self.logger.info('')
                        self.logger.info('--------------')
                        _s += '%s' % k + ': ' + v
                    if 'product_name' == k:
                        _s += ' %s' % k + ': ' + v

                for k in ['name', 'value', 'units']:
                    if k in b.keys():
                        _s += ' %s' % k + ': '
                        if b[k] is not None:
                            _s += '%s,' % str(b[k])
                        else:
                            _s += 'None,'
                        _s += ' '

                if _s != '':
                    self.logger.info(_s)
            else:
                self.logger.debug(
                    'unable to dig list, instance not a dict by %s; object was %s', type(b), b)

                if original_b != b:
                    self.dig_list(b)

    @safe_run
    def _decode_res_json(self, res):
        try:
            if hasattr(res, 'content'):
                #_js = json.loads(res.content)
                # fixed issue with python 3.5
                _js = res.json()
                res = ast.literal_eval(str(_js).replace('null', 'None'))
            else:
                res = ast.literal_eval(str(res).replace('null', 'None'))

            self.dig_list(res)
            return res
        except Exception as e:

            msg = 'remote/connection error, server response is not valid \n'
            msg += f'exception: {e}'
            msg += 'possible causes: \n'
            msg += '- connection error\n'
            msg += '- wrong credentials\n'
            msg += '- wrong remote address\n'
            msg += '- error on the remote server\n'
            msg += "--------------------------------------------------------------\n"
            if hasattr(res, 'status_code'):

                msg += '--- status code:-> %s\n' % res.status_code
            if hasattr(res, 'text'):

                msg += '--- response text ---\n %s\n' % res.text
            if hasattr(res, 'content'):

                msg += '--- res content ---\n %s\n' % res.content
            msg += "--------------------------------------------------------------"

            raise RemoteException(message=msg)

    @safe_run
    def get_instrument_description(self, instrument=None):
        if instrument is None:
            instrument = self.instrument

        res = requests.get("%s/api/meta-data" % self.url,
                           params=dict(instrument=instrument), cookies=self.cookies)

        if res.status_code != 200:
            raise UnexpectedDispatcherStatusCode(
                f"status: {res.status_code}, raw: {res.text}")

        return self._decode_res_json(res)

    @safe_run
    def get_product_description(self, instrument, product_name):
        res = requests.get("%s/api/meta-data" % self.url, params=dict(
            instrument=instrument, product_type=product_name), cookies=self.cookies)

        if res.status_code != 200:
            raise UnexpectedDispatcherStatusCode(
                f"status: {res.status_code}, raw: {res.text}")

        self.logger.info('--------------')
        self.logger.info(
            'parameters for product %s and instrument %s', product_name, instrument)
        return self._decode_res_json(res)

    @safe_run
    def get_instruments_list(self):
        #print ('instr',self.instrument)
        res = requests.get("%s/api/instr-list" % self.url,
                           params=dict(instrument=self.instrument), cookies=self.cookies)

        if res.status_code != 200:
            raise UnexpectedDispatcherStatusCode(
                f"status: {res.status_code}, raw: {res.text}")

        return self._decode_res_json(res)

    def report_last_request(self):
        self.logger.info(
            f"{C.GREY}last request completed in {self.last_request_t_complete - self.last_request_t0} seconds{C.NC}")

    def get_product(self,
                    product: str,
                    instrument: str,
                    verbose=None,
                    product_type: str = 'Real',
                    **kwargs):
        """
        submit query, wait (if allowed by self.wait), decode output when found
        """

        self.job_id = None

        # TODO: it's confusing when and where these are passed
        self.product = product
        self.instrument = instrument

        kwargs['instrument'] = instrument
        kwargs['product_type'] = product
        kwargs['query_type'] = product_type
        kwargs['off_line'] = False,
        kwargs['query_status'] = 'new',
        kwargs['verbose'] = verbose,
        kwargs['session_id'] = self.session_id

        if 'dry_run' in kwargs:
            warnings.warn('The dry_run parameter you included is not going to have any effect on the execution.\n'
                          'However the oda_api will perform a check of the list of valid parameters for your request.')
            del kwargs['dry_run']

        res = requests.get("%s/api/par-names" % self.url, params=dict(
            instrument=instrument, product_type=product), cookies=self.cookies)

        if res.status_code != 200:
            warnings.warn(
                'parameter check not available on remote server, check carefully parameters name')
        else:
            _ignore_list = ['instrument', 'product_type', 'query_type',
                            'off_line', 'query_status', 'verbose', 'session_id']
            validation_dict = copy.deepcopy(kwargs)

            for _i in _ignore_list:
                del validation_dict[_i]

            valid_names = self._decode_res_json(res)
            for n in validation_dict.keys():
                if n not in valid_names:
                    if self.strict_parameter_check:
                        raise UserError(f'the parameter: {n} is not among the valid ones: {valid_names}'
                                        f'(you can set {self}.strict_parameter_check=False, but beware!')
                    else:
                        msg = '\n'
                        msg += '----------------------------------------------------------------------------\n'
                        msg += 'the parameter: %s ' % n
                        msg += '  is not among valid ones:'
                        msg += '\n'
                        msg += '%s' % valid_names
                        msg += '\n'
                        msg += 'this will throw an error in a future version \n'
                        msg += 'and might break the current request!\n '
                        msg += '----------------------------------------------------------------------------\n'
                        warnings.warn(msg)

        if kwargs.get('token', None) is None and self.token_discovery_methods is not None:
            discovered_token = oda_api.token.discover_token(self.token_discovery_methods)
            if discovered_token is not None:
                logger.info("discovered token in environment")
                kwargs['token'] = discovered_token            

        # >
        self.request(kwargs)

        if self.is_failed:
            return self.process_failure()
        elif self.is_done:
            res_json = self.response_json
        elif not self.is_complete:
            if self.wait:
                raise RuntimeError(
                    "should have waited, but did not - programming error!")
            else:
                self.logger.info(
                    f"\n{C.BROWN}query not complete, please poll again later{C.NC}")
                return
        else:
            raise RuntimeError(
                "not failed, not, but complete? programming error for client!")

        d = DataCollection.from_response_json(
            res_json, instrument, product)

        del(res)

        return d

    @staticmethod
    def set_api_code(query_dict, url="www.astro.unige.ch/mmoda/dispatch-data"):

        _skip_list_ = ['job_id', 'query_status',
                       'session_id', 'use_resolver[local]', 'use_scws']

        _alias_dict = {}
        _alias_dict['product_type'] = 'product'
        _alias_dict['query_type'] = 'product_type'

        _header = f'''from oda_api.api import DispatcherAPI
disp=DispatcherAPI(url='{url}', instrument='mock')'''

        _api_dict = {}
        for k in query_dict.keys():
            if k not in _skip_list_:

                if k in _alias_dict.keys():
                    n = _alias_dict[k]

                else:
                    n = k

                if query_dict[k] is not None:
                    _api_dict[n] = query_dict[k]

        _cmd_ = f'''{_header}

par_dict={json.dumps(_api_dict, indent=4)}

data_collection = disp.get_product(**par_dict)
'''

        return _cmd_

    def __repr__(self):
        return f"[ {self.__class__.__name__}: {self.url} ]"


class DataCollection(object):

    def __init__(self, data_list, add_meta_to_name=['src_name', 'product'], instrument=None, product=None):
        self._p_list = []
        self._n_list = []
        for ID, data in enumerate(data_list):

            name = ''
            if hasattr(data, 'name'):
                name = data.name

            if name.strip() == '':
                if product is not None:
                    name = '%s' % product
                elif instrument is not None:
                    name = '%s' % instrument
                else:
                    name = 'prod'

            name = '%s_%d' % (name, ID)

            name, var_name = self._build_prod_name(
                data, name, add_meta_to_name)
            setattr(self, var_name, data)

            self._p_list.append(data)
            self._n_list.append(var_name)

    def show(self):
        for ID, prod_name in enumerate(self._n_list):
            if hasattr(self._p_list[ID], 'meta_data'):
                meta_data = self._p_list[ID].meta_data
            else:
                meta_data = ''
            print('ID=%s prod_name=%s' %
                  (ID, prod_name), ' meta_data:', meta_data)
            print()

    def as_list(self):
        L = []

        for ID, prod_name in enumerate(self._n_list):
            if hasattr(self._p_list[ID], 'meta_data'):
                meta_data = self._p_list[ID].meta_data
            else:
                meta_data = ''

            L.append({
                'ID': ID, 'prod_name': prod_name, 'meta_data:': meta_data
            })

        return L

    def _build_prod_name(self, prod, name, add_meta_to_name):

        for kw in add_meta_to_name:
            if hasattr(prod, 'meta_data'):
                if kw in prod.meta_data:
                    s = prod.meta_data[kw].replace(' ', '')
                    if s.strip() != '':
                        name += '_'+s.strip()
        return name, oda_api.misc_helpers.clean_var_name(name)

    def save_all_data(self, prenpend_name=None):
        for pname, prod in zip(self._n_list, self._p_list):
            if prenpend_name is not None:
                file_name = prenpend_name+'_'+pname
            else:
                file_name = pname

            file_name = file_name + '.fits'
            prod.write_fits_file(file_name)

    def save(self, file_name):
        pickle.dump(self, open(file_name, 'wb'),
                    protocol=pickle.HIGHEST_PROTOCOL)

    def new_from_metadata(self, key, val):
        dc = None
        _l = []
        for p in self._p_list:
            if p.meta_data[key] == val:
                _l.append(p)

        if _l != []:
            dc = DataCollection(_l)

        return dc

    @classmethod
    def from_response_json(cls, res_json, instrument, product):
        data = []
        if 'numpy_data_product' in res_json['products'].keys():
            data.append(NumpyDataProduct.decode(
                res_json['products']['numpy_data_product']))
        elif 'numpy_data_product_list' in res_json['products'].keys():

            data.extend([NumpyDataProduct.decode(d)
                         for d in res_json['products']['numpy_data_product_list']])

        if 'binary_data_product_list' in res_json['products'].keys():
            data.extend([BinaryData().decode(d)
                         for d in res_json['products']['binary_data_product_list']])

        if 'catalog' in res_json['products'].keys():
            data.append(ApiCatalog(
                res_json['products']['catalog'], name='dispatcher_catalog'))

        if 'astropy_table_product_ascii_list' in res_json['products'].keys():
            data.extend([ascii.read(table_text['ascii'])
                         for table_text in res_json['products']['astropy_table_product_ascii_list']])

        if 'astropy_table_product_binary_list' in res_json['products'].keys():
            data.extend([ascii.read(table_binary)
                         for table_binary in res_json['products']['astropy_table_product_binary_list']])

        d = cls(data, instrument=instrument, product=product)
        for p in d._p_list:
            if hasattr(p, 'meta_data') is False and hasattr(p, 'meta') is True:
                p.meta_data = p.meta

        return d

