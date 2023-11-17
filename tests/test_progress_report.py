from oda_api.api import ProgressReporter

def test_progress_reporter():
    pr = ProgressReporter()
    assert not pr.enabled
    pr.report_progress(stage='simulation', progress=50, substage='spectra', subprogress=30, message='some message')
