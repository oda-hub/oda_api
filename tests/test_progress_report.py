from oda_api.api import ProgressReporter
import os
import json

callback_file = ".oda_api_callback"
request_params = dict(stage='simulation', progress=50, substage='spectra', subprogress=30, message='some message')

def test_progress_reporter_disabled():
    if os.path.isfile(callback_file):
        os.remove(callback_file)
    # if callback is not available
    pr = ProgressReporter()
    assert not pr.enabled
    # the call below should not produce exception
    try:
        pr.report_progress(**request_params)
    except:
        assert False, 'report_progress raises exception in case of disabled ProgressReporter'

def test_progress_reporter_enabled():
    # if callback is available
    try:
        dump_file = 'callback'
        with open(callback_file, 'w') as file:
            print(f'file://{os.getcwd()}/{dump_file}', file=file)

        pr = ProgressReporter()
        assert pr.enabled

        pr.report_progress(**request_params)

        # verify that params passed to report_progress were saved to dump_file
        with open(dump_file) as json_file:
            saved_params = json.load(json_file)
            # append extra param befor check
            request_params['action'] = 'progress'  # this key is added by report_progress
            assert saved_params == request_params
    finally:
        if os.path.isfile(callback_file):
            os.remove(callback_file)
        if os.path.isfile(dump_file):
            os.remove(dump_file)

