import astroquery.heasarc
import astroquery.simbad
from astropy import units as u
from astropy.table import Table
from astropy.coordinates import SkyCoord
import logging

logger = logging.getLogger(__name__)

def object_scw_list(object_name,
                    **kwargs):

    R = astroquery.simbad.Simbad().query_object(object_name) # type: Table

    if len(R) > 1:
        raise RuntimeError(f'object name {object_name} resolves to multiple different coordinates: {R}')
    elif len(R) == 0:
        raise RuntimeError(f'object name {object_name} can not be resolved with Simbad')
    else:
        source_coord = SkyCoord(R['RA'][0], R['DEC'][0], unit=(u.hourangle, u.deg)) # pylint: disable=no-member
        return position_scw_list(source_coord, **kwargs)


def position_scw_list(source_coord,
                      radius_deg=5.,
                      time_range="2001-01-01 .. 2029-01-01",
                      min_good_isgri=1000,
                      resultmax=int(1e6)):

    with astroquery.heasarc.Conf.server.set_temp('https://www.isdc.unige.ch/browse/w3query.pl'):
        R = astroquery.heasarc.Heasarc().query_region( # pylint: disable=no-member
                        position=source_coord, 
                        mission='integral_rev3_scw', resultmax=resultmax, radius=radius_deg*u.deg, cache=False, # pylint: disable=no-member
                        time=time_range,
                        fields='All',
                        good_isgri=f">{min_good_isgri}",
                        scw_type="POINTING"

        )

    logger.debug('found %s SCWs', len(R))

    return R