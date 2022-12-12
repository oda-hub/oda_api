# mypy: ignore-errors
# pylint: skip-file
# pylint: disable-all

from __future__ import absolute_import, division, print_function

from builtins import (str, open, range,
                      zip, round, input, int, pow, object, zip)


__author__ = "Carlo Ferrigno"

import json
import numpy
import copy

from matplotlib import pylab as plt
from matplotlib.widgets import Slider
from matplotlib import cm

from astropy import table
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astroquery.simbad import Simbad

import oda_api.api as api

import time as _time
import astropy.wcs as wcs

# NOTE GW, optional
try:
    import ligo.skymap.plot
except ModuleNotFoundError:
    pass 

import logging

logger = logging.getLogger("oda_api.plot_tools")

__all__ = ['OdaImage', 'OdaLightCurve', 'OdaGWContours', 'OdaSpectrum']


class OdaProduct(object):

    def __init__(self, data):
        self.data = data
        self.meta = None
        self.logger = logger.getChild(self.__class__.__name__.lower())
        self.progress_logger = self.logger.getChild("progress")


class OdaImage(OdaProduct):

    name = 'image'

    def get_image_for_gallery(self, data=None, meta=None, header=None, sources=None,
             levels=None, cmap=cm.gist_earth, unit_ID=4, det_sigma=3):
        plt = self.build_fig(data=data, meta=meta, header=header, sources=sources,
                              levels=levels, cmap=cmap, unit_ID=unit_ID, det_sigma=det_sigma, sliders=False)

        request_time = _time.time()
        pic_name = str(request_time) + '_image.png'

        plt.savefig(pic_name)

        return pic_name

    def show(self, data=None, meta=None, header=None, sources=None,
             levels=None, cmap=cm.gist_earth, unit_ID=4, det_sigma=3, sliders=True):
      
        """
        OdaImage.show
        :param data: ODA data products, takes from class initialisation by default
        :param meta: ODA data products metadata, takes from class initialisation by default
        :param header: ODA data product image header, takes from class initialisation by default
        :param sources: ODA catalog table, takes from class initialisation by default
        :param levels: levels for contour plot, default is  numpy.linspace(1, 10, 10)
        :param cmap: colormap default is cm.gist_earth,
        :param unit_ID: the unit to plot image default is 4
        :param det_sigma: limit detection sigma to lot from catalog, note that
        :param sliders: plot sliders, set to false to upload images in gallery.
        :return: matplotlib figure instance
        """

        plt = self.build_fig(data=data, meta=meta, header=header, sources=sources,
                              levels=levels, cmap=cmap, unit_ID=unit_ID, det_sigma=det_sigma, sliders=sliders)

        plt.show()

    def build_fig(self, data=None, meta=None, header=None, sources=None,
             levels=None, cmap=cm.gist_earth,
             unit_ID=4, det_sigma=3, sliders=True):

        if levels is None:
            levels = numpy.linspace(1, 10, 10)

        if data is None:
            data = self.data.mosaic_image_0_mosaic.data_unit[unit_ID].data

        if meta is None:
            self.meta = self.data.mosaic_image_0_mosaic.meta_data

        if header is None:
            header = self.data.mosaic_image_0_mosaic.data_unit[unit_ID].header

        if sources is None:
            sources = self.data.dispatcher_catalog_1.table

        w = wcs.WCS(header)

        fig = plt.figure(figsize=(8, 8./1.62))
        ax = plt.subplot(projection=w)
        
        data = numpy.ma.masked_equal(data, numpy.NaN)

        self.cs = plt.contourf(data, cmap=cmap, levels=levels,
                               extend="both", zorder=0)
        self.cs.cmap.set_under('k')
        self.cs.set_clim(numpy.min(levels), numpy.max(levels))

        self.cb = plt.colorbar(self.cs)

        if len(sources) > 0:
            ras = numpy.array([x for x in sources['ra']])
            decs = numpy.array([x for x in sources['dec']])
            if 'src_names' in sources.columns:
                names = numpy.array([x for x in sources['src_names']])
                # Defines relevant indexes for plotting regions
                m_new = numpy.array(['NEW' in name for name in names])
            if 'significance' in sources.columns:
                sigmas = numpy.array([x for x in sources['significance']])


            # plot new sources as pink circles
            try:
                m = m_new & (sigmas > det_sigma)
                ra_coord = ras[m]
                dec_coord = decs[m]
                new_names = names[m]
            except:
                ra_coord = []
                dec_coord = []
                new_names = []

            plt.scatter(ra_coord, dec_coord, s=100, marker="o", facecolors='none',
                        edgecolors='pink',
                        lw=3, label="NEW any", zorder=5, transform=ax.get_transform('world'))

            for i in range(len(ra_coord)):
                plt.text(ra_coord[i],
                         dec_coord[i] + 0.5,
                         new_names[i], color="pink", size=15, transform=ax.get_transform('world'))

            try:
                m = ~m_new & (sigmas > det_sigma - 1)
                ra_coord = ras[m]
                dec_coord = decs[m]
                cat_names = names[m]
            except:
                ra_coord = []
                dec_coord = []
                cat_names = []

            plt.scatter(ra_coord, dec_coord, s=100, marker="o", facecolors='none',
                        edgecolors='magenta', lw=3, label="known", zorder=5, transform=ax.get_transform('world'))

            for i in range(len(ra_coord)):
                plt.text(ra_coord[i],
                         dec_coord[i] + 0.5,
                         cat_names[i], color="magenta", size=15, transform=ax.get_transform('world'))

        plt.grid(color="grey", zorder=10)

        plt.xlabel("RA")
        plt.ylabel("Dec")

        if sliders:
            # Nice to have : slider
            cmin = plt.axes([0.85, 0.05, 0.02, 0.4])
            cmax = plt.axes([0.85, 0.55, 0.02, 0.4])
            data_min = data[numpy.isfinite(data)].min()
            data_max = data[numpy.isfinite(data)].max()
            self.smin = Slider(cmin, 'Min', data_min, data_max, valinit=1., orientation='vertical')
            self.smax = Slider(cmax, 'Max', data_min, data_max, valinit=10., orientation='vertical')
            self.smin.on_changed(self.update)
            self.smax.on_changed(self.update)

        return fig


    def update(self, x):
        if self.smin.val < self.smax.val:
            self.cs.set_clim(self.smin.val, self.smax.val)


    def write_fits(self, file_prefix=''):
        file_fn = f'{file_prefix}mosaic.fits'

        self.data.mosaic_image_0_mosaic.write_fits_file(file_fn, overwrite=True)
        return file_fn
    
    
    def extract_catalog_from_image(self, include_new_sources=False, det_sigma=5, objects_of_interest=[],
                                   flag=1, isgri_flag=2, update_catalog=False):
        catalog_str = self.extract_catalog_string_from_image(include_new_sources, det_sigma, objects_of_interest,
                                              flag, isgri_flag, update_catalog)
        return json.loads(catalog_str)


    def extract_catalog_string_from_image(self, include_new_sources=False, det_sigma=5, 
                                          objects_of_interest=None,
                                          flag=1, isgri_flag=2, update_catalog=True) -> str:
        """
        Example: objects_of_interest=['Her X-1']
                 objects_of_interest=[('Her X-1', Simbad.query )]
                 objects_of_interest=[('Her X-1', Skycoord )]
                 objects_of_interest=[ Skycoord(....) ]
        """

        if objects_of_interest is None:
            objects_of_interest = []

        image = self.data
        
        if image.dispatcher_catalog_1.table is None:
            self.logger.warning("No sources in the catalog")
            if objects_of_interest != []:
                return OdaImage.add_objects_of_interest(None, objects_of_interest,
                                                        flag, isgri_flag)
            else:
                return 'none'

        sources = image.dispatcher_catalog_1.table[image.dispatcher_catalog_1.table['significance'] >= det_sigma]

        if len(sources) == 0:
            self.logger.warning('No sources in the catalog with det_sigma > %.1f' % det_sigma)
            if objects_of_interest != []:
                return self.add_objects_of_interest(None, objects_of_interest,
                                                    flag, isgri_flag)
            else:
                return 'none'

        if not include_new_sources:
            ind = [not 'NEW' in ss for ss in sources['src_names']]
            clean_sources = sources[ind]
            self.logger.debug(ind)
            self.logger.debug(sources)
            self.logger.debug(clean_sources)
        else:
            clean_sources = sources

        unique_sources = self.add_objects_of_interest(clean_sources, objects_of_interest,
                                                                 flag, isgri_flag)

        copied_image = copy.deepcopy(image)
        copied_image.dispatcher_catalog_1.table = unique_sources

        if update_catalog:
            image.dispatcher_catalog_1.table = unique_sources

        return copied_image.dispatcher_catalog_1.get_api_dictionary()

    @staticmethod
    def make_one_source_catalog_string(name, ra, dec, isgri_flag, flag):
        out_str_templ ='{"cat_frame": "fk5", "cat_coord_units": "deg", "cat_column_list": [[1], ["%s"], [0.0], [%f], [%f], [-32768], [%d], [%d], [0.001]], "cat_column_names": ["meta_ID", "src_names", "significance", "ra", "dec", "NEW_SOURCE", "ISGRI_FLAG", "FLAG", "ERR_RAD"], "cat_column_descr": [["meta_ID", "<i8"], ["src_names", "<U7"], ["significance", "<f8"], ["ra", "<f8"], ["dec", "<f8"], ["NEW_SOURCE", "<i8"], ["ISGRI_FLAG", "<i8"], ["FLAG", "<i8"], ["ERR_RAD", "<f8"]], "cat_lat_name": "dec", "cat_lon_name": "ra"}'
        return out_str_templ % (name, ra, dec, isgri_flag, flag)

    def add_objects_of_interest(self, clean_sources, objects_of_interest, flag=1, isgri_flag=2, tolerance = 1./60.):
        for ooi in objects_of_interest:
            if isinstance(ooi, tuple):
                ooi, t = ooi
                if isinstance(t, SkyCoord):
                    source_coord = t
            elif isinstance(ooi, str):
                t = Simbad.query_object(ooi)
            else:
                raise Exception("fail to elaborate object of interest")

            if isinstance(t, table.Table):
                source_coord = SkyCoord(t['RA'], t['DEC'], unit=(u.hourangle, u.deg), frame="fk5")

            self.logger.info("Elaborating object of interest: %s %f %f" %
                                       (ooi, source_coord.ra.deg, source_coord.dec.deg))
            ra = source_coord.ra.deg
            dec = source_coord.dec.deg
            self.logger.info("RA=%g Dec=%g" % (ra, dec))

            if clean_sources is not None:
                #Look for the source of interest in NEW sources by coordinates
                for ss in clean_sources:
                    if 'NEW' in ss['src_names']:
                        if numpy.abs(ra - ss['ra']) <= tolerance and numpy.abs(dec - ss['dec']) <= tolerance:
                            self.logger.info('Found ' + ooi + ' in catalog as ' + ss['src_names'])
                            ind = clean_sources['src_names'] == ss['src_names']
                            clean_sources['FLAG'][ind] = flag
                            clean_sources['ISGRI_FLAG'][ind] = isgri_flag
                            clean_sources['src_names'][ind] = ooi

                #Look for the source of interest in
                ind = clean_sources['src_names'] == ooi
                if numpy.count_nonzero(ind) > 0:
                    self.logger.info('Found ' + ooi + ' in catalog')
                    clean_sources['FLAG'][ind] = flag
                    if 'ISGRI_FLAG' in clean_sources.keys():
                       clean_sources['ISGRI_FLAG'][ind] = isgri_flag
                    if 'JEMX_FLAG' in clean_sources.keys():
                       clean_sources['JEMX_FLAG'][ind] = isgri_flag
                else:
                    self.logger.info('Adding ' + ooi + ' to catalog')
                    try:
                        self.logger.debug('Flux is present')
                        clean_sources.add_row((0, ooi, 0, ra, dec, 0, isgri_flag, flag, 1e-3, 0, 0))
                    except:
                        self.logger.debug('Flux is NOT present')
                        clean_sources.add_row((0, ooi, 0, ra, dec, 0, isgri_flag, flag, 1e-3))

                unique_sources = table.unique(clean_sources, keys=['src_names'])

                return unique_sources
            else:
                return self.make_one_source_catalog_string(ooi, ra, dec, isgri_flag, flag)


class OdaLightCurve(OdaProduct):

    name = 'lightcurve'

    def get_lc(self, source_name, systematic_fraction=0):

        combined_lc = self.data
        # In LC name has no "-" nor "+" ??????
        patched_source_name = source_name.replace('-', ' ').replace('+', ' ')

        hdu = None
        for j, dd in enumerate(combined_lc._p_list):
            self.logger.debug(dd.meta_data['src_name'])
            if dd.meta_data['src_name'] == source_name or dd.meta_data['src_name'] == patched_source_name:
                for ii, du in enumerate(dd.data_unit):
                    if 'LC' in du.name:
                        hdu = du.to_fits_hdu()

        if hdu is None:
            self.logger.info('Source ' + source_name + ' not found in the light curves')
            return None, None, None, None, None, None

        x = hdu.data['TIME']
        y = hdu.data['RATE']
        dy = hdu.data['ERROR']
        self.logger.debug("Original length of light curve %d" % len(x))
        ind = numpy.argsort(x)
        x = x[ind]
        y = y[ind]
        dy = dy[ind]
        dy = numpy.sqrt(dy ** 2 + (y * systematic_fraction) ** 2)
        ind = numpy.logical_and(numpy.isfinite(y), numpy.isfinite(dy))
        ind = numpy.logical_and(ind, dy > 0)
        self.logger.debug("Final length of light curve %d " % numpy.sum(ind))

        try:
            e_min = hdu.header['E_MIN']
        except:
            e_min = 0

        try:
            e_max = hdu.header['E_MAX']
        except:
            e_max = 0

        #This could only be valid for ISGRI
        try:
            dt_lc = hdu.data['XAX_E']
            self.logger.debug('Get time bin directly from light curve')
        except:
            timedel = hdu.header['TIMEDEL']
            timepix = hdu.header['TIMEPIXR']
            t_lc = hdu.data['TIME'] + (0.5 - timepix) * timedel
            dt_lc = t_lc.copy() * 0.0 + timedel / 2
            for i in range(len(t_lc) - 1):
                dt_lc[i + 1] = min(timedel / 2, t_lc[i + 1] - t_lc[i] - dt_lc[i])
            self.logger.debug('Computed time bin from TIMEDEL')

        return x[ind], dt_lc[ind], y[ind], dy[ind], e_min, e_max

    def get_image_for_gallery(self, in_source_name='', systematic_fraction=0, ng_sig_limit=0, find_excesses=False):
        plts = self.build_fig(in_source_name=in_source_name, systematic_fraction=systematic_fraction,
                             ng_sig_limit=ng_sig_limit, find_excesses=find_excesses)

        request_time = _time.time()
        pic_name = str(request_time) + '_image.png'

        if len(plts) == 1:
            plts[0].savefig(pic_name)

        return pic_name

    def show(self, in_source_name='', systematic_fraction=0, ng_sig_limit=0, find_excesses=False):

        plt = self.build_fig(in_source_name=in_source_name, systematic_fraction=systematic_fraction,
                             ng_sig_limit=ng_sig_limit, find_excesses=find_excesses)

        for p in plt:
            p.show()

    def build_fig(self,  in_source_name='', systematic_fraction=0, ng_sig_limit=0, find_excesses=False):
        #if ng_sig_limit <1 does not plot range
        combined_lc = self.data
        from scipy import stats

        if in_source_name == '':
            source_names = [dd.meta_data['src_name'] for dd in combined_lc._p_list]
        else:
            source_names = [in_source_name]

        figs = []

        for source_name in source_names:
            x, dx, y, dy, e_min, e_max = self.get_lc(source_name, systematic_fraction)
            if x is None:
                return

            meany = numpy.sum(y / dy ** 2) / numpy.sum(1. / dy ** 2)
            err_mean = numpy.sum(1 / dy ** 2)

            std_dev = numpy.std(y)

            figs.append(plt.figure())
            _ = plt.errorbar(x, y, xerr=dx, yerr=dy, marker='o', capsize=0, linestyle='', label='Lightcurve')
            _ = plt.axhline(meany, color='green', linewidth=3)
            _ = plt.xlabel('Time [IJD]')
            if e_min == 0 or e_max ==0:
                _ = plt.ylabel('Rate')
            else:
                _ = plt.ylabel('Rate %.1f-%.1f keV' % (e_min, e_max))

            if ng_sig_limit >= 1:
                ndof = len(y) - 1
                prob_limit = stats.norm().sf(ng_sig_limit)
                chi2_limit = stats.chi2(ndof).isf(prob_limit)
                band_width = numpy.sqrt(chi2_limit / err_mean)

                _ = plt.axhspan(meany - band_width, meany + band_width, color='green', alpha=0.3,
                                label=f'{ng_sig_limit} $\sigma_m$, {100 * systematic_fraction}% syst')

                _ = plt.axhspan(meany - std_dev*ng_sig_limit, meany + std_dev*ng_sig_limit,
                                color='cyan', alpha=0.3,
                                label=f'{ng_sig_limit} $\sigma_d$, {100 * systematic_fraction}% syst')

                _ = plt.legend()

            plot_title = source_name
            _ = plt.title(plot_title)
            if find_excesses:
                ind = (y - band_width)/dy > ng_sig_limit
                if numpy.sum(ind) > 0:
                    _ = plt.plot(x[ind], y[ind], marker='x', color='red', linestyle='', markersize=10)
                    self.logger.info('We found positive excesses on the lightcurve at times')
                    good_ind = numpy.where(ind)
                    #print(good_ind[0][0:-1], good_ind[0][1:])
                    old_time = -1
                    if len(good_ind[0]) == 1:
                        self.logger.info('%f' % (x[good_ind[0][0]]))
                    else:
                        for i,j in zip(good_ind[0][0:-1], good_ind[0][1:]):
                            #print(i,j)
                            if j-i > 2:
                                if x[i] != old_time :
                                    self.logger.info('%f' % x[i])
                                    _ = OdaLightCurve.plot_zoom(x,y,dy,i)
                                self.logger.info('%f' % (x[j]))
                                _ = OdaLightCurve.plot_zoom(x, y, dy, j)
                            # else:
                            #     self.logger.debug('%f' % ((x[i]+x[j])/2))

                            old_time = x[j]

        return figs


    @staticmethod
    def plot_zoom(x, y, dy, i, n_before=5, n_after=15, save_plot=True, name_base='burst_at_'):
        fig = plt.figure()
        _ = plt.errorbar(x[i-n_before:i+n_after], y[i-n_before:i+n_after], yerr=dy[i-n_before:i+n_after],
                         marker='o', capsize=0, linestyle='', label='Lightcurve')
        _ = plt.xlabel('Time [IJD]')
        _ = plt.ylabel('Rate')
        if save_plot:
            _ = plt.savefig(name_base+'%d.png' % i)
        return fig
    

    def write_fits(self, source_name, file_suffix='', output_dir='.'):
        # In LC name has no "-" nor "+" ??????
        lc = self.data
        patched_source_name = source_name.replace('-', ' ').replace('+', ' ')
        lcprod = [l for l in lc._p_list if l.meta_data['src_name'] == source_name or \
                  l.meta_data['src_name'] == patched_source_name]

        if (len(lcprod) < 1):
            self.logger.warning("source %s not found in light curve products" % source_name)
            return "none", 0, 0, 0

        if (len(lcprod) > 1):
            self.logger.warning(
                "source %s is found more than once light curve products, writing only the first one" % source_name)

        instrument = lcprod[0].data_unit[1].header['INSTRUME']
        if instrument == 'IBIS':
            ind_extension = 1
        else:
            ind_extension = 2

        lc_fn = output_dir + "/%s_lc_%s%s.fits" % (instrument, source_name.replace(' ', '_'), file_suffix)
        hdu = lcprod[0].data_unit[ind_extension].to_fits_hdu()
        timedel = hdu.header['TIMEDEL']
        timepixr = hdu.header['TIMEPIXR']

        dt = timedel * timepixr

        hdu.header['TSTART'] = hdu.data['TIME'][0] - dt
        hdu.header['TSTOP'] = hdu.data['TIME'][-1] + dt
        hdu.header['TFIRST'] = hdu.data['TIME'][0] - dt
        hdu.header['TLAST'] = hdu.data['TIME'][-1] + dt
        hdu.header['TELAPSE'] = hdu.header['TLAST'] - hdu.header['TFIRST']

        ontime=0
        for x in hdu.data['FRACEXP']:
            ontime += x * timedel

        hdu.header['ONTIME'] = ontime

        fits.writeto(lc_fn, hdu.data, header=hdu.header, overwrite=True)

        mjdref = float(hdu.header['MJDREF'])
        tstart = float(hdu.header['TSTART']) + mjdref
        tstop = float(hdu.header['TSTOP']) + mjdref
        try:
            exposure = float(hdu.header['EXPOSURE'])
        except:
            exposure = -1

        return lc_fn, tstart, tstop, exposure

    @staticmethod
    def check_product_for_gallery(**kwargs):
        if 'src_name' not in kwargs:
            logger.warning('The src_name parameter is mandatory for a light-curve product\n')
            raise api.UserError('the src_name parameter is mandatory for a light-curve product')
        logger.info('Policy for a light-curve product successfully verified\n')
        return True


class OdaSpectrum(OdaProduct):
    name = 'spectrum'

    def show_spectral_products(self):

        summed_data = self.data

        for dd, nn in zip(summed_data._p_list, summed_data._n_list):
            self.logger.debug(nn)
            dd.show_meta()
            # for kk in dd.meta_data.items():
            if 'spectrum' in dd.meta_data['product']:
                self.logger.debug(dd.data_unit[1].header['EXPOSURE'])
            dd.show()

    def get_spectrum_products(self, in_source_name='none'):
        if in_source_name == 'none':
            return None

        specprod = [l for l in self.data._p_list if l.meta_data['src_name'] == in_source_name]

        if (len(specprod) < 1):
            self.logger.warning("source %s not found in spectral products" % in_source_name)
            return None

        return specprod

    def get_image_for_gallery(self, in_source_name='', systematic_fraction=0, xlim=[]):
        pic_name = None
        plt = self.build_fig(in_source_name=in_source_name, systematic_fraction=systematic_fraction,
                             xlim=xlim)

        if plt is not None:
            request_time = _time.time()
            pic_name = str(request_time) + '_image.png'

            plt.savefig(pic_name)

        return pic_name

    def show(self, in_source_name='', systematic_fraction=0, xlim=[]):

        plt = self.build_fig(in_source_name=in_source_name, systematic_fraction=systematic_fraction,
                             xlim=xlim)

        if plt is not None:
            plt.show()

    def build_fig(self, in_source_name='', systematic_fraction=0, xlim=[]):

        if in_source_name == '':
            self.show_spectral_products()
            return

        specprod = self.get_spectrum_products(in_source_name)
        if specprod is None:
            return

        spec = specprod[0].data_unit[1].to_fits_hdu()
        for hh in specprod[2].data_unit:
            if hh.to_fits_hdu().header['EXTNAME'] == 'EBOUNDS':
                ebounds = hh.to_fits_hdu()

        x = (ebounds.data['E_MAX'] + ebounds.data['E_MIN'])/2.
        dx = (ebounds.data['E_MAX'] - ebounds.data['E_MIN']) / 2.
        y = spec.data['RATE']
        dy = numpy.sqrt(spec.data['STAT_ERR']**2 + spec.data['SYS_ERR']**2 + (y*systematic_fraction)**2)

        fig = plt.figure()
        _ = plt.errorbar(x, y, xerr=dx, yerr=dy, marker='o', capsize=0, linestyle='', label='spectrum')

        _ = plt.xlabel('Energy [keV]')
        _ = plt.xscale('log')
        _ = plt.yscale('log')
        _ = plt.ylabel('Rate')
        _ = plt.title(in_source_name)
        if len(xlim) == 2:
            _ = plt.xlim(xlim)

        return fig
    
    def write_fits(self, source_name='', file_suffix='', grouping=[0, 0, 0], systematic_fraction=0,
                                  output_dir='.'):
        """
        Grouping argument is [minimum_energy, maximum_energy, number_of_bins]
        number of bins > 0, linear grouping
        number_of_bins < 0, logarithmic binning
        """

        if source_name == '':
            self.show_spectral_products()
            self.logger.warning('PLease specify a source to save the spectral products')
            return "none", 0, 0, 0

        specprod = self.get_spectrum_products(source_name)
        if specprod is None:
            return "none", 0, 0, 0

        instrument = specprod[0].data_unit[1].header['INSTRUME']

        out_name = source_name.replace(' ', '_').replace('+', 'p')
        spec_fn = output_dir + "/%s_spectrum_%s%s.fits" % (instrument, out_name, file_suffix)
        arf_fn = output_dir + "/%s_arf_%s%s.fits" % (instrument, out_name, file_suffix)
        rmf_fn = output_dir + "/%s_rmf_%s%s.fits" % (instrument, out_name, file_suffix)

        self.logger.info("Saving spectrum %s with rmf %s and arf %s" % (spec_fn, rmf_fn, arf_fn))

        specprod[0].write_fits_file(spec_fn)
        specprod[1].write_fits_file(arf_fn)
        specprod[2].write_fits_file(rmf_fn)

        ff = fits.open(spec_fn, mode='update')

        ff[1].header['RESPFILE'] = rmf_fn
        ff[1].header['ANCRFILE'] = arf_fn
        mjdref = ff[1].header['MJDREF']
        tstart = float(ff[1].header['TSTART']) + mjdref
        tstop = float(ff[1].header['TSTOP']) + mjdref
        exposure = ff[1].header['EXPOSURE']
        ff[1].data['SYS_ERR'] = numpy.zeros(len(ff[1].data['SYS_ERR'])) + systematic_fraction
        ind = numpy.isfinite(ff[1].data['RATE'])
        ff[1].data['QUALITY'][ind] = 0

        if numpy.sum(grouping) != 0:

            if grouping[1] <= grouping[0] or grouping[2] == 0:
                raise RuntimeError('Wrong grouping arguments')

            ff_rmf = fits.open(rmf_fn)

            e_min = ff_rmf['EBOUNDS'].data['E_MIN']
            e_max = ff_rmf['EBOUNDS'].data['E_MAX']

            ff_rmf.close()

            ind1 = numpy.argmin(numpy.abs(e_min - grouping[0]))
            ind2 = numpy.argmin(numpy.abs(e_max - grouping[1]))

            n_bins = numpy.abs(grouping[2])

            ff[1].data['GROUPING'][0:ind1] = 0
            ff[1].data['GROUPING'][ind2:] = 0

            ff[1].data['QUALITY'][0:ind1] = 1
            ff[1].data['QUALITY'][ind2:] = 1

            if grouping[2] > 0:
                step = int((ind2 - ind1 + 1) / n_bins)
                self.logger.info('Linear grouping with step %d' % step)
                for i in range(1, step):
                    j = range(ind1 + i, ind2, step)
                    ff[1].data['GROUPING'][j] = -1
            else:
                ff[1].data['GROUPING'][ind1:ind2] = -1
                e_step = (e_max[ind2] / e_min[ind1]) ** (1.0 / n_bins)
                self.logger.info('Geometric grouping with step %.3f' % e_step)
                loc_e = e_min[ind1]
                while (loc_e < e_max[ind2]):
                    ind_loc_e = numpy.argmin(numpy.abs(e_min - loc_e))
                    ff[1].data['GROUPING'][ind_loc_e] = 1
                    loc_e *= e_step

        ff.flush()
        ff.close()

        return spec_fn, tstart, tstop, exposure

    @staticmethod
    def check_product_for_gallery(**kwargs):
        if 'src_name' not in kwargs:
            logger.warning('The src_name parameter is mandatory for a spectrum product\n')
            raise api.UserError('the src_name parameter is mandatory for a spectrum product')

        logger.info("Policy for a spectrum product successfully verified\n")
        return True


class OdaGWContours(OdaProduct):

    # TODO to clarify the name, also for the gallery
    name = 'contour'
    
    @staticmethod
    def _plot_single_contour(contour_coords, ax, color='r'):
        coords = numpy.array(contour_coords)
        try:
            ax.plot(coords[:,0], coords[:,1], '-', transform=ax.get_transform('world'), color = color)
        except TypeError:
            ax.plot(coords[:,0], coords[:,1], '-', transform=ax.get_transform(), color = color)

    @staticmethod
    def _plot_contour_list(contour_list, ax, color=None):
        kwargs = {}
        if color is not None:
            kwargs['color'] = color
        for contour_coords in contour_list:
            OdaGWContours._plot_single_contour(contour_coords, ax, **kwargs)
    
    def plot_event_contours(self, event, legend=True, name_in_legend=True, colors = [], ax = None):
        if ax is None:
            ax = plt.axes(projection='astro hours mollweide')
        
        if not colors:
            prop_cycle = plt.rcParams['axes.prop_cycle']
            colors = prop_cycle.by_key()['color']
        
        lpr = []
        names = []
        if event in self.data.contours.keys():
            for i in range(len(self.data.contours[event].levels)):
                color = colors[i%len(colors)]
                OdaGWContours._plot_contour_list(self.data.contours[event].contours[i], ax, color)
                lpr.append(plt.Rectangle((0, 0), 1, 1, fc = color))
                names.append(f"{self.data.contours[event].name+' ' if name_in_legend else ''}{self.data.contours[event].levels[i]}%")
        else:
            raise ValueError(f'Wrong event name: {event}')
        
        if legend is True:
            ax.legend(lpr, names)
            
    def plot_contours(self, legend=True, colors = [], ax = None):
        if ax is None:
            ax = plt.axes(projection='astro hours mollweide')
        
        if not colors:
            prop_cycle = plt.rcParams['axes.prop_cycle']
            colors = prop_cycle.by_key()['color']
        
        lpr = []
        names = []
        i = 0
        for event, data in self.data.contours.items():
            color = colors[i%len(colors)]
            self.plot_event_contours(event, ax = ax, colors = [color], legend = False)
            i+=1
            lpr.append(plt.Rectangle((0, 0), 1, 1, fc = color))
            names.append(event)

        if legend is True:
            ax.legend(lpr, names, numpoints=1, bbox_to_anchor=(1.05, 1), loc='upper left')            
        
    def show(self, event_name = None):
        fig = self.build_fig(event_name=event_name)

        if fig is not None:
            fig.show()

    def get_image_for_gallery(self, event_name=None):
        pic_name = None
        fig = self.build_fig(event_name=event_name)

        if fig is not None:
            request_time = _time.time()
            pic_name = str(request_time) + '_image.png'

            fig.savefig(pic_name)

        return pic_name

    def build_fig(self, event_name = None):
        fig = plt.figure()
        if event_name is None:
            self.plot_contours()
        else:
            self.plot_event_contours(event_name)
        return fig

    # TODO can an implementation of this method provided?
    def write_fits(self):
        raise NotImplementedError
