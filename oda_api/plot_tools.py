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


__all__ = ['OdaImage', 'OdaLightCurve']

class OdaImage(object):

    def __init__(self, data):
        self.data = data

        self.meta = data

    def show(self, data=None, meta=None, unit_ID=4):
        if data is None:
            data = self.data.data_unit[unit_ID].data
        if meta is None:
            self.meta = self.data.meta_data

        fig = plt.figure(figsize=(8, 6))
        ax = fig.subplots(1, 1)
        self.line =ax.imshow(data, interpolation='nearest')
        cmin = plt.axes([0.1, 0.05, 0.8, 0.02])
        cmax = plt.axes([0.1, 0.01, 0.8, 0.02])
        self.smin = Slider(cmin, 'vmin',  data.min(), data.max(), valinit=data.min(),)
        self.smax = Slider(cmax, 'vmax', data.min(), data.max(), valinit=data.max(),)
        self.smin.on_changed(self.update)
        self.smax.on_changed(self.update)


        plt.show()

    def update(self, x):
        #print('x',x)
        if self.smin.val < self.smax.val:
            self.line.set_clim(self.smin.val, self.smax.val)




class OdaLightCurve(object):

    def __init__(self, data):
        self.data = data



    def show(self, data=None, meta=None, unit_ID=0):

        if data is None:
            data = self.data.data_unit[unit_ID].data
        if meta is None:
            meta = self.data.meta_data

        #print(data,meta['time'],data[meta['time']])
        fig = plt.figure(figsize=(8, 6))
        ax = fig.subplots(1, 1)
        x = data[meta['time']]
        y=data[meta['rate']]
        dy=data[meta['rate_err']]

        ax.errorbar(x, y, yerr=dy, xerr=meta['time_bin']*0.5, ls="")
        ax.set_title(meta['src_name'])
        plt.show()