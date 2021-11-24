from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)

__author__ = "Andrea Tramacere"

# Standard library
# eg copy
# absolute import rg:from copy import deepcopy

# Dependencies
# eg numpy
# absolute import eg: import numpy as np

# Project
# relative import eg: from .mod import f



# must
import numpy
from matplotlib import pylab as plt
#from ipywidgets import *
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib import cm
import astropy.wcs as wcs

import logging

logger = logging.getLogger("oda_api.plot_tools")

__all__ = ['OdaImage', 'OdaLightCurve']

class OdaImage(object):

    def __init__(self, data):
        self.data = data
        self.meta = None


    def show(self, data=None, meta=None, header=None, sources=None,
             levels=numpy.linspace(1, 10, 10), cmap=cm.gist_earth,
             unit_ID=4, det_sigma=3):
        if data is None:
            data = self.data.mosaic_image_0_mosaic.data_unit[unit_ID].data
        if meta is None:
            self.meta = self.data.mosaic_image_0_mosaic.meta_data
        if header is None:
            header = self.data.mosaic_image_0_mosaic.data_unit[unit_ID].header
        if sources is None:
            sources = self.data.dispatcher_catalog_1.table

        fig = plt.figure(figsize=(8, 6))

        j, i = plt.meshgrid(range(data.shape[0]), range(data.shape[1]))
        w = wcs.WCS(header)
        ra, dec = w.wcs_pix2world(numpy.column_stack([i.flatten(), j.flatten()]), 0).transpose()
        ra = ra.reshape(i.shape)
        dec = dec.reshape(j.shape)

        data = numpy.transpose(data)
        data = numpy.ma.masked_equal(data, numpy.NaN)

        ## CF display image crossing ra =0
        zero_crossing = False
        # print("******************", ra.max(), ra.min())
        # print("******************", numpy.abs(ra.max() - 360.0), numpy.abs(ra.min()))
        if numpy.abs(ra.max() - 360.0) < 0.1 and numpy.abs(ra.min()) < 0.1:
            zero_crossing = True
            ind_ra = ra > 180.
            ra[ind_ra] -= 360.

            # print("ra shape ", ra.shape)
            ind_sort = numpy.argsort(ra, axis=-1)

            # print("Sorted RA", ind_sort.shape)
            # print(ind_sort)

            ra = numpy.take_along_axis(ra, ind_sort, axis=-1)
            # ra = ra[ind_sort]

            # tmp = [ ra[ii] for ii in ind_sort]
            #
            # ra=tmp.copy()
            # print("ordered ra shape ", ra.shape)
            # tmp = [data[ii] for ii in ind_sort]
            #
            # data = tmp.copy()
            data = numpy.take_along_axis(data, ind_sort, axis=-1)
            # print("data shape ", data.shape)
            #
            # print("Finished sorting")

        ## CF end
        #ax = plt.subplots(1, 1)
        self.cs = plt.contourf(ra, dec, data, cmap=cmap, levels=levels,
                          extend="both", zorder=0)
        self.cs.cmap.set_under('k')
        self.cs.set_clim(numpy.min(levels), numpy.max(levels))

        self.cb = plt.colorbar(self.cs)
        #plt.tight_layout()

        plt.xlim([ra.max(), ra.min()])
        plt.ylim([dec.min(), dec.max()])

        if len(sources) > 0:
            ras = numpy.array([x for x in sources['ra']])
            decs = numpy.array([x for x in sources['dec']])
            names = numpy.array([x for x in sources['src_names']])
            sigmas = numpy.array([x for x in sources['significance']])
            # Defines relevant indexes for plotting regions

            m_new = numpy.array(['NEW' in name for name in names])

            # m_offaxis = self.source_results.MEAN_VAR > 5
            # m_noisy = self.source_results.DETSIG_CORR < 5

            # plot new sources as pink circles

            try:
                m = m_new & (sigmas > det_sigma)
                ra_coord = ras[m]
                dec_coord = decs[m]
                new_names = names[m]
                if zero_crossing:
                    ind_ra = ra_coord > 180.
                    try:
                        ra_coord[ind_ra] -= 360.
                    except:
                        pass
            except:
                ra_coord = []
                dec_coord = []
                new_names = []

            plt.scatter(ra_coord, dec_coord, s=100, marker="o", facecolors='none',
                        edgecolors='pink',
                        lw=3, label="NEW any", zorder=5)
            for i in range(len(ra_coord)):
                # print("%f %f %s\n"%(ra_coord[i], dec_coord[i], names[i]))
                plt.text(ra_coord[i],
                         dec_coord[i] + 0.5,
                         new_names[i], color="pink", size=15)

            try:
                m = ~m_new & (sigmas > det_sigma - 1)
                ra_coord = ras[m]
                dec_coord = decs[m]
                cat_names = names[m]
                if zero_crossing:
                    ind_ra = ra_coord > 180.
                    try:
                        ra_coord[ind_ra] -= 360.
                    except:
                        pass
            except:
                ra_coord = []
                dec_coord = []
                cat_names = []

            plt.scatter(ra_coord, dec_coord, s=100, marker="o", facecolors='none',
                        edgecolors='magenta', lw=3, label="known", zorder=5)
            for i in range(len(ra_coord)):
                # print("%f %f %s\n"%(ra_coord[i], dec_coord[i], names[i]))
                plt.text(ra_coord[i],
                         dec_coord[i] + 0.5,
                         cat_names[i], color="magenta", size=15)

        plt.grid(color="grey", zorder=10)

        plt.xlabel("RA")
        plt.ylabel("Dec")

        #Nice to have : slider
        cmin = plt.axes([0.85, 0.05, 0.02, 0.4])
        cmax = plt.axes([0.85, 0.55, 0.02, 0.4])
        self.smin = Slider(cmin, 'Min',  data.min(), data.max(), valinit=1., orientation='vertical')
        self.smax = Slider(cmax, 'Max', data.min(), data.max(), valinit=10., orientation='vertical')
        self.smin.on_changed(self.update)
        self.smax.on_changed(self.update)

        plt.show()

        return fig

    def update(self, x):
        #print('x',x)
        if self.smin.val < self.smax.val:
            self.cs.set_clim(self.smin.val, self.smax.val)
            #self.cb = plt.colorbar(self.cs)




class OdaLightCurve(object):

    def __init__(self, data):
        self.data = data
        self.logger = logger.getChild(self.__class__.__name__.lower())
        self.progress_logger = self.logger.getChild("progress")

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
    
    def show(self,  in_source_name='', systematic_fraction=0, ng_sig_limit=0, find_excesses=False):
        #if ng_sig_limit <1 does not plot range
        combined_lc = self.data
        from scipy import stats

        if in_source_name == '':
            source_names = [dd.meta_data['src_name'] for dd in combined_lc._p_list]
        else:
            source_names = [in_source_name]

        for source_name in source_names:
            x, dx, y, dy, e_min, e_max = self.get_lc(source_name, systematic_fraction)
            if x is None:
                return

            meany = numpy.sum(y / dy ** 2) / numpy.sum(1. / dy ** 2)
            err_mean = numpy.sum(1 / dy ** 2)

            std_dev = numpy.std(y)

            fig = plt.figure()
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

        return fig

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
