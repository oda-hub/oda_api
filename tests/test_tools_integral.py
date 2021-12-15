
def test_scwlist():
    from astropy.coordinates import SkyCoord
    from oda_api.tools import integral
    R = integral.position_scw_list(SkyCoord(83, 22, unit='deg'), resultmax=10)
    assert len(R) == 10

def test_object_scwlist():
    from oda_api.tools import integral
    R = integral.object_scw_list('Crab', resultmax=10)
    assert len(R) == 10