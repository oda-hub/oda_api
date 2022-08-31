import pytest

def test_site_discovery():
    from oda_api.api import DispatcherAPI

    disp = DispatcherAPI()
    
    assert len(disp.known_sites_dict) == 5
    assert disp.url == "https://www.astro.unige.ch/mmoda/dispatch-data"

    for alias in ["unige-production", "production", "prod"]:
        disp = DispatcherAPI(url=alias)
        assert disp.url == "https://www.astro.unige.ch/mmoda/dispatch-data"
        
    for alias in ["unige-staging", "staging"]:
        disp = DispatcherAPI(url=alias)
        assert disp.url == "https://dispatcher-staging.obsuks1.unige.ch"
