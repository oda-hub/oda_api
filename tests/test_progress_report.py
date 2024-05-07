from oda_api.api import ProgressReporter
import os
import json

context_file = ".oda_api_context"
request_params = dict(stage='simulation', progress=50., progress_max=100., substage='spectra', subprogress=30., subprogress_max=100., message='some message')

def test_progress_reporter_disabled():
    if os.path.isfile(context_file):
        os.remove(context_file)
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
        context = {
            "callback": f'file://{os.getcwd()}/{dump_file}'
        }
        with open(context_file, 'w') as output:
            json.dump(context, output)

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
        if os.path.isfile(context_file):
            os.remove(context_file)
        if os.path.isfile(dump_file):
            os.remove(dump_file)

