from oda_api.api import ProgressReporter
import os
import json

callback_file = ".oda_api_callback"

def test_progress_reporter_disabled():
    if os.path.isfile(callback_file):
        os.remove(callback_file)
    # if callback is not available
    pr = ProgressReporter()
    assert not pr.enabled
    pr.report_progress(stage='simulation', progress=50, substage='spectra', subprogress=30, message='some message')

def test_progress_reporter_enabled():
    # if callback is available
    try:
        dump_file = 'callback'
        with open(callback_file, 'w') as file:
            print(f'file://{os.getcwd()}/{dump_file}', file=file)

        pr = ProgressReporter()
        assert pr.enabled
        params = dict(stage='simulation', progress=50, substage='spectra', subprogress=30, message='some message')
        pr.report_progress(**params)
        with open(dump_file) as json_file:
            passed_params = json.load(json_file)
            assert len([k for k in passed_params.keys() if k not in params]) == 0
    finally:
        if os.path.isfile(callback_file):
            os.remove(callback_file)
        if os.path.isfile(dump_file):
            os.remove(dump_file)

