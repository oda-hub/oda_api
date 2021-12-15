
def test_scwlist():
    from astropy.coordinates import SkyCoord
    from oda_api.tools import integral
    integral.get_scw_list(SkyCoord(0, 0, unit='deg'), resultmax=10)