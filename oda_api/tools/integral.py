import astroquery.heasarc
from astropy import units as u

def get_scw_list(source_coord,
                 radius_deg=5.,
                 time_range="2001-01-01 .. 2029-01-01",
                 min_good_isgri=1000,
                 resultmax=int(1e6)):

    with astroquery.heasarc.Conf.server.set_temp('https://www.isdc.unige.ch/browse/w3query.pl'):
        R = astroquery.heasarc.Heasarc().query_region(
                        position=source_coord, 
                        mission='integral_rev3_scw', resultmax=resultmax, radius=radius_deg*u.deg, cache=False,
                        time=time_range,
                        fields='All',
                        good_isgri=f">{min_good_isgri}",
                        scw_type="POINTING"

        )