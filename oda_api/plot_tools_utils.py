# mypy: ignore-errors
# pylint: skip-file
# pylint: disable-all

from __future__ import absolute_import, division, print_function

import os.path
from builtins import (str, open, range,
                      zip, round, input, int, pow, object, zip)


__author__ = "Carlo Ferrigno"


from bokeh.layouts import row, gridplot
from bokeh.models import HoverTool
from bokeh.embed import components
from bokeh.plotting import figure

# NOTE GW, optional
try:
    import ligo.skymap.plot
except ModuleNotFoundError:
    pass 

import logging

logger = logging.getLogger("oda_api.plot_tools")

__all__ = ['ScatterPlot', 'GridPlot']


class ScatterPlot(object):

    def __init__(self,w,h,x_label=None,y_label=None,x_range=None,y_range=None,title=None,y_axis_type='linear',x_axis_type='linear'):
        hover = HoverTool(tooltips=[("x", "$x"), ("y", "$y")])

        self.fig = figure(title=title, width=w, height=h,x_range=x_range,y_range=y_range,
                          y_axis_type=y_axis_type,
                          x_axis_type=x_axis_type,
                     tools=[hover, 'pan,box_zoom,box_select,wheel_zoom,reset,save,crosshair']
                     )

        if x_label is not None:
            self.fig.xaxis.axis_label = x_label

        if y_label is not None:
            self.fig.yaxis.axis_label = y_label

    def add_errorbar(self, x, y, xerr=None, yerr=None, color='red',
                 point_kwargs={}, error_kwargs={}):

        self.fig.circle(x, y, color=color, **point_kwargs)

        if xerr is not None:
            x_err_x = []
            x_err_y = []
            for px, py, err in zip(x, y, xerr):
                x_err_x.append((px - err, px + err))
                x_err_y.append((py, py))
            self.fig.multi_line(x_err_x, x_err_y, color=color, **error_kwargs)

        if yerr is not None:
            y_err_x = []
            y_err_y = []
            for px, py, err in zip(x, y, yerr):
                y_err_x.append((px, px))
                y_err_y.append((py - err, py + err))
            self.fig.multi_line(y_err_x, y_err_y, color=color, **error_kwargs)



    def add_step_line(self, x, y, legend=None):
        if legend:
            self.fig.step(x, y, legend_label=legend, mode="center")
        else:
            self.fig.step(x, y, mode="center")

    def add_line(self, x, y, legend=None, color='red'):
        if legend:
            self.fig.line(x, y, legend_label=legend, line_color=color)
        else:
            self.fig.line(x, y, line_color=color)

    def get_html_draw(self):

        layout = row(
            self.fig
        )
        script, div = components(layout)

        html_dict = {'script': script, 'div': div}
        return html_dict


class GridPlot(object):

    def __init__(self,f1,f2,w=None,h=None):

        self.f1=f1
        self.f2=f2

    def get_html_draw(self,w=None,h=None):
        grid = gridplot([self.f1.fig,self.f2.fig],ncols=1,plot_width=w, plot_height=h)
        script, div = components(grid)

        html_dict= {'script': script, 'div': div}
        return html_dict

