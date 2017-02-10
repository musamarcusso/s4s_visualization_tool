__author__ = 'Musa Morena Marcusso Manhaes'

try:
    import pygtk
    pygtk.require('2.0')
except:
    raise ImportError('Error importing PyGTK')

try:
    import gtk
    import gtk.glade
    import gobject
except:
    raise ImportError('Error importing Glade dependencies')

import matplotlib
matplotlib.use('Agg')

from copy import deepcopy
from threading import Thread
import time
import numpy as np
from matplotlib import cm
from matplotlib.figure import Figure
import mpl_toolkits.mplot3d as Axes3D
from matplotlib.lines import Line2D
import matplotlib.patches as pt
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
import S4SPlotOptionsWindow
import S4SExportGraphWindow
import S4SBase


class S4SCanvas(object, S4SBase.S4SBase):
    _COLORMAPS = ['jet', 'hsv', 'hot', 'summer', 'winter', 'spring', 'gray', 'pink', 'ocean']
    _ASPECT_RATIO = ['equal', 'auto', 'normal']
    _PAPER_TYPE = {'Letter': 'letter',
                   'Legal': 'legal',
                   'Executive': 'executive',
                   'Ledger': 'ledger'}
    _ORIENTATION = {'Landscape': 'landscape',
                    'Portrait': 'portrait'}
    _FORMAT = {'PNG': 'png',
               'PDF': 'pdf',
               'PS': 'ps',
               'EPS': 'eps',
               'SVG': 'svg'}
    _MASK_TYPES = ['circle', 'rect']

    def __init__(self, options_window=None):
        S4SBase.S4SBase.__init__(self)

        for i in range(11):
            self._PAPER_TYPE['A' + str(i)] = 'a' + str(i)
        for i in range(11):
            self._PAPER_TYPE['B' + str(i)] = 'b' + str(i)

        self._figure = Figure(facecolor='white')
        self._canvas = FigureCanvas(self._figure)
        self._axes = None
        self._is_plot_3d = False
        self._font_size = 10

        self.builder.get_object('panel_plot').add(self._canvas)

        self._figure.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self._figure.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)

        self._plots = {'main_plot': None,
                       'plane': None}

        self._updating_plot = False
        self._thread_plot_update = None
        self._title = ''
        self._xlabel = 'X [mm]'
        self._ylabel = 'Y [mm]'
        self._zlabel = 'Z [mm]'
        self._clim = []

        self._aspect_ratio = self._ASPECT_RATIO[0]

        self._plane = {'x': [], 'y': [], 'z': []}

        self._xs = None
        self._ys = None
        self._zs = None
        self._cs = None

        self._start_capture = False
        self._capture_points = []
        self._mask_form = None
        self._mask_type = None

        self._marker_size = 8
        self._plot_types = {'Scatter': {'on': True, 'fcn': self.plot_scatter},
                            'Surface': {'on': False, 'fcn': self.plot_surface}}

        self._plane_active = False
        self._is_axis_on = True
        self._is_color_relative_to_plane = False
        self._colormap_index = 0
        self._color_bar = None
        self._exp_window = None
        self._callback_capture = None

        self._options_window = S4SPlotOptionsWindow.S4SPlotOptionsWindow(title=self.get_title(),
                                                                         xlabel=self.get_xlabel(),
                                                                         ylabel=self.get_ylabel(),
                                                                         zlabel=self.get_zlabel(),
                                                                         colormaps=self.get_colormaps(),
                                                                         colormap_index=self.get_colormap_index(),
                                                                         aspect_ratio=self._ASPECT_RATIO,
                                                                         marker_size=self._marker_size,
                                                                         plot_types=self._plot_types.keys(),
                                                                         plot_type_default=self.get_plot_type(),
                                                                         font_size=self._font_size,
                                                                         is_3d_active=self._is_plot_3d,
                                                                         is_scatter=self._plot_types['Scatter']['on'])

        callbacks_canvas = {'title': self.set_title,
                            'xlabel': self.set_xlabel,
                            'ylabel': self.set_ylabel,
                            'zlabel': self.set_zlabel,
                            'xy_view': self.set_xy_view,
                            'yz_view': self.set_yz_view,
                            'xz_view': self.set_xz_view,
                            'reset_view': self.reset_view,
                            'axis_on': lambda : self.set_axis_visible(True),
                            'axis_off': lambda : self.set_axis_visible(False),
                            'colormap': self.set_colormap_index,
                            'activate_plane': self.set_plane_plot,
                            'clim': self.set_clim,
                            'aspect_ratio': self.set_aspect_ratio,
                            'marker_size': self.set_marker_size,
                            'plot_type': self.set_plot_type,
                            'is_3d': self.set_plot_3d,
                            'font_size': self.set_font_size}

        for label in callbacks_canvas:
            self._options_window.set_callback_fcn(label, callbacks_canvas[label])

    @property
    def options_win(self):
        return self._options_window

    def delete_masks(self):
        self._options_window.delete_masks()

    def get_colormaps(self):
        return self._COLORMAPS

    def get_cur_colormap(self):
        return self._COLORMAPS[self._colormap_index]

    def set_colormap_index(self, index):
        if index < 0 or index >= len(self._COLORMAPS):
            raise ValueError('The index for the colormap is out of range')
        self._colormap_index = index
        self.run_plot()

    def get_colormap_index(self):
        return self._colormap_index

    def set_font_size(self, font_size):
        assert font_size >= 1
        self._font_size = font_size
        self.set_title(self._title)
        self.set_xlabel(self._xlabel)
        self.set_ylabel(self._ylabel)
        self.set_zlabel(self._zlabel)
        self.set_tick_size(self._font_size)

    def set_plot_3d(self, is_3d=True):
        self._is_plot_3d = is_3d
        self._enable_widgets(['add_circle_mask', 'add_rect_mask', 'exclude_points'], not is_3d)
        self.set_new_axes()
        self.run_plot()

    def set_axis_visible(self, is_active=True):
        self._is_axis_on = is_active
        self._axes.set_axis_on() if is_active else self._axes.set_axis_off()
        self._figure.canvas.draw()

    def set_title(self, new_title):
        self._title = new_title
        self._axes.set_title(new_title, y=1.08, size=self._font_size)
        self._figure.canvas.draw()

    def set_clim(self, c_limits):
        assert len(c_limits) == 2
        cmin = c_limits[0]
        cmax = c_limits[1]
        assert cmin < cmax
        self._clim = [cmin, cmax]
        self.run_plot()

    def get_clim(self):
        return self._clim

    def set_marker_size(self, marker_size):
        assert marker_size > 0, 'Marker size cannot be negative'
        self._marker_size = marker_size
        self.run_plot()

    def get_marker_size(self):
        return self._marker_size

    def set_new_axes(self):
        self._figure.clf()
        if self._is_plot_3d:
            self._axes = Axes3D.Axes3D(self._figure, [0.1, 0.1, 0.8, 0.7])
            self._axes.mouse_init()
            self._axes.autoscale_view(False, False, False)
        else:
            self._axes = self._figure.add_subplot(111, position=[0.1, 0.1, 0.8, 0.7])
        self._mask_form = None
        # First configuration for the axes
        self._axes.grid(False)
        if self._color_bar is not None:
            del self._color_bar
        self._color_bar = None

    def set_xlabel(self, new_label):
        self._xlabel = new_label
        if self._is_plot_3d:
            self._axes.set_xlabel(new_label, labelpad=80, size=self._font_size)
        else:
            self._axes.set_xlabel(new_label, size=self._font_size)
        self._figure.canvas.draw()

    def set_ylabel(self, new_label):
        self._ylabel = new_label
        if self._is_plot_3d:
            self._axes.set_ylabel(new_label, labelpad=80, size=self._font_size)
        else:
            self._axes.set_ylabel(new_label, size=self._font_size)
        self._figure.canvas.draw()

    def set_zlabel(self, new_label):
        if self._is_plot_3d:
            self._zlabel = new_label
            self._axes.set_zlabel(new_label, labelpad=80, size=self._font_size)
            self._figure.canvas.draw()

    def get_title(self):
        return self._title

    def get_xlabel(self):
        return self._xlabel

    def get_ylabel(self):
        return self._ylabel

    def get_zlabel(self):
        return self._zlabel

    def start_capture(self, type_mask, callback):
        if type_mask not in self._MASK_TYPES:
            return False
        self._start_capture = True
        self._capture_points = []
        self._mask_type = type_mask
        self._callback_capture = callback
        return True

    def clear_figure(self):
        self._figure.clf()
        self._color_bar = None
        self.set_new_axes()

    def set_scatter_plot(self):
        for key in self._plot_types:
            if key is 'Scatter':
                self._plot_types[key]['on'] = True
            else:
                self._plot_types[key]['on'] = False

    def set_surface_plot(self):
        for key in self._plot_types:
            if key is 'Surface':
                self._plot_types[key]['on'] = True
            else:
                self._plot_types[key]['on'] = False

    def get_plot_type(self):
        for key in self._plot_types:
            if self._plot_types[key]['on']:
                return key
        return None

    def set_plot_type(self, plot_type):
        assert plot_type in self._plot_types, 'Invalid plot type'
        for key in self._plot_types:
            self._plot_types[key]['on'] = (key == plot_type)

        self.run_plot()

    def set_plane_plot(self, is_active):
        self._plane_active = is_active
        self.plot_plane()

    def plot(self, x=None, y=None, z=None, c=None):
        assert x is not None and y is not None and z is not None

        if x.shape[0] != y.shape[0] or x.shape[0] != z.shape[0] or x.shape[1] != y.shape[1] or x.shape[1] != z.shape[1]:
            raise ValueError('The input vectors must have the same length')
        if c is not None:
            if x.shape != c.shape:
                raise ValueError('The input vectors must have the same length')

            self._is_color_relative_to_plane = not np.array_equal(z, c)
        else:
            self._is_color_relative_to_plane = False

        self._options_window.set_title(self.processor.current_file)
        self._plane_active = False

        self._xs = np.array(x)
        self._ys = np.array(y)
        self._zs = np.array(z)
        self._cs = np.array(z) if c is None else np.array(c)

        self._clim = [self._cs[np.logical_not(np.isnan(self._zs))].min(),
                      self._cs[np.logical_not(np.isnan(self._zs))].max()]

        self.run_plot()

    def set_aspect_ratio(self, mode='auto'):
        assert mode in self._ASPECT_RATIO
        self._aspect_ratio = mode
        if not self._is_plot_3d:
            if self._axes is not None:
                self._axes.set_aspect(mode)
        else:
            x = self._xs[np.logical_not(np.isnan(self._zs))]
            y = self._ys[np.logical_not(np.isnan(self._zs))]
            z = self._zs[np.logical_not(np.isnan(self._zs))]

            if mode == 'equal':
                max_range = np.array([x.max() - x.min(), y.max() - y.min(), z.max() - z.min()]).max() / 2.0
                mean_x = x.mean()
                mean_y = y.mean()
                mean_z = z.mean()

                self._axes.set_xlim(mean_x - max_range, mean_x + max_range)
                self._axes.set_ylim(mean_y - max_range, mean_y + max_range)
                self._axes.set_zlim(mean_z - max_range, mean_z + max_range)
            elif mode == 'auto':
                self._axes.set_xlim(x.min(), x.max())
                self._axes.set_ylim(y.min(), y.max())
                self._axes.set_zlim(z.min(), z.max())
            elif mode == 'normal':
                max_range = np.array([x.max() - x.min(), y.max() - y.min(), z.max() - z.min()]).max()
                mean_x = x.mean()
                mean_y = y.mean()
                mean_z = z.mean()

                self._axes.set_xlim(mean_x - max_range, mean_x + max_range)
                self._axes.set_ylim(mean_y - max_range, mean_y + max_range)
                self._axes.set_zlim(mean_z - max_range, mean_z + max_range)

        self._figure.canvas.draw()

    def add_plane(self, x, y, z):
        self._plane['x'] = x
        self._plane['y'] = y
        self._plane['z'] = z
        self.plot_plane()

    def plot_plane(self):
        if not self._is_plot_3d:
            return

        for key in self._plane:
            if len(self._plane[key]) == 0:
                return
        if self._plane_active and len(self._plane['x']) > 0:
            if self._plots['plane'] is not None:
                del self._plots['plane']
                self._plots['plane'] = None
            self._plots['plane'] = self._axes.plot_surface(self._plane['x'], self._plane['y'], self._plane['z'],
                                                           rstride=1,
                                                           cstride=1,
                                                           linewidth=0,
                                                           antialiased=False,
                                                           alpha=0.3)
        else:
            try:
                if self._plots['plane'] is not None:
                    self._plots['plane'].remove()
            except:
                pass
        self._figure.canvas.draw()

    def set_tick_size(self, size=8):
        if self._axes is None:
            return

        assert size > 0

        for tick in self._axes.xaxis.get_major_ticks():
            tick.label.set_fontsize(size)
        for tick in self._axes.yaxis.get_major_ticks():
            tick.label.set_fontsize(size)
        if self._color_bar is not None:
            self._color_bar.ax.tick_params(labelsize=size)
        if self._is_plot_3d:
            for tick in self._axes.zaxis.get_major_ticks():
                tick.label.set_fontsize(size)

    def run_plot(self):
        gobject.idle_add(self._set_new_plot)

    def _set_new_plot(self):
        self._updating_plot = True
        if self._axes is None:
            self.set_new_axes()

        self._axes.grid(False)
        self.set_tick_size()
        self._axes.grid(False)

        self.plot_plane()

        for key in self._plot_types:
            if self._plot_types[key]['on']:
                if self._plot_types[key]['fcn'] is not None:
                    self._plot_types[key]['fcn']()

        self.set_axis_visible(self._is_axis_on)
        self.set_aspect_ratio(self._aspect_ratio)

        self.set_title(self._title)
        self.set_xlabel(self._xlabel)
        self.set_ylabel(self._ylabel)
        self.set_zlabel(self._zlabel)

        self.set_tick_size(self._font_size)

        self._figure.canvas.draw()
        self._updating_plot = False

    def plot_scatter(self):
        if self._xs is None or self._ys is None or self._zs is None or self._cs is None:
            return

        try:
            if self._plots['main_plot'] is not None:
                self._plots['main_plot'].remove()
        except:
            pass

        if self._is_plot_3d:
            self._plots['main_plot'] = self._axes.scatter(self._xs.flatten(),
                                                          self._ys.flatten(),
                                                          zs=self._zs.flatten(),
                                                          c=self._cs.flatten(),
                                                          s=self._marker_size,
                                                          vmin=self._clim[0],
                                                          vmax=self._clim[1],
                                                          edgecolors=None, lw=0, cmap=self._COLORMAPS[self._colormap_index])

        else:
            self._cs[np.isnan(self._zs)] = np.nan
            self._xs[np.isnan(self._zs)] = np.nan
            self._ys[np.isnan(self._zs)] = np.nan

            self._plots['main_plot'] = self._axes.scatter(self._xs.flatten(),
                                                          self._ys.flatten(),
                                                          c=self._cs.flatten(),
                                                          vmin=self._clim[0],
                                                          vmax=self._clim[1],
                                                          s=self._marker_size,
                                                          edgecolors=None, lw=0, cmap=self._COLORMAPS[self._colormap_index])
            self._axes.grid(True)

            self._axes.set_xlim([self._xs[np.logical_not(np.isnan(self._zs))].min(),
                                 self._xs[np.logical_not(np.isnan(self._zs))].max()])
            self._axes.set_ylim([self._xs[np.logical_not(np.isnan(self._zs))].min(),
                                 self._xs[np.logical_not(np.isnan(self._zs))].max()])


        if self._color_bar is None:
            self._color_bar = self._figure.colorbar(self._plots['main_plot'], shrink=0.5, aspect=5)
        else:
            self._color_bar.on_mappable_changed(self._plots['main_plot'])

        self._color_bar.set_clim(vmin=self._clim[0], vmax=self._clim[1])
        self._color_bar.draw_all()

        self._color_bar.ax.tick_params(labelsize=8)

    def plot_surface(self):
        try:
            if self._plots['main_plot'] is not None:
                self._plots['main_plot'].remove()
        except:
            pass
        color = self._get_norm_color()
        if self._is_plot_3d:
            self._plots['main_plot'] = self._axes.plot_surface(self._xs,
                                                               self._ys,
                                                               self._zs,
                                                               facecolors=cm.jet(color),
                                                               rstride=1,
                                                               cstride=1,
                                                               cmap=self._COLORMAPS[self._colormap_index],
                                                               linewidth=0,
                                                               antialiased=False)
        else:
            x = deepcopy(self._xs)
            y = deepcopy(self._ys)
            x[np.isnan(self._zs)] = np.nan
            y[np.isnan(self._zs)] = np.nan
            self._plots['main_plot'] = self._axes.pcolor(x,
                                                         y,
                                                         self._cs,
                                                         vmin=self._clim[0],
                                                         vmax=self._clim[1],
                                                         cmap=self._COLORMAPS[self._colormap_index])
        if self._color_bar is None:
            color_mappable = cm.ScalarMappable(cmap=cm.jet)
            color_mappable.set_array(color)
            self._color_bar = self._figure.colorbar(color_mappable, shrink=0.5, aspect=5)
        else:
            self._color_bar.on_mappable_changed(self._plots['main_plot'])

        self._color_bar.set_clim(vmin=self._clim[0], vmax=self._clim[1])
        self._color_bar.draw_all()

        self._color_bar.ax.tick_params(labelsize=8)

    def _get_norm_color(self):
        if self._cs is None:
            return None
        cs_min = self._clim[0]
        cs_max = self._clim[1]
        color = (self._cs - cs_min) / (cs_max - cs_min)
        color[np.isnan(self._cs)] = (cs_max - cs_min) / 2 + cs_min
        color[color > 1] = 1
        color[color < 0] = 0

        return color

    def set_xy_view(self):
        if self._is_plot_3d:
            self._axes.view_init(90, 0)
            self._figure.canvas.draw()

    def set_yz_view(self):
        if self._is_plot_3d:
            self._axes.view_init(0, -180)
            self._figure.canvas.draw()

    def set_xz_view(self):
        if self._is_plot_3d:
            self._axes.view_init(0, -90)
            self._figure.canvas.draw()

    def reset_view(self):
        if self._is_plot_3d:
            self._axes.view_init(30, -45)
            self._figure.canvas.draw()

    def save_fig(self):
        if self._exp_window is None:
            self._exp_window = S4SExportGraphWindow.S4SExportGraphWindow(orientation=self._ORIENTATION.keys(),
                                                                         paper_type=self._PAPER_TYPE.keys(),
                                                                         format=self._FORMAT.keys(),
                                                                         callback=self._save_fig_callback)
        self._exp_window.open()

    def _save_fig_callback(self):
        self._figure.savefig(self._exp_window.filename,
                             dpi=self._exp_window.dpi,
                             format=self._FORMAT[self._exp_window.format],
                             bbox_inches='tight',
                             orientation=self._ORIENTATION[self._exp_window.orientation],
                             papertype=self._PAPER_TYPE[self._exp_window.paper_type])

    def _on_mouse_press(self, event):
        if not self._start_capture:
            return

        if len(self._capture_points) == 2:
            return

        self._capture_points.append((event.xdata, event.ydata))

        if len(self._capture_points) == 2:
            self._start_capture = False
            self._mask_form.set_data([], [])
            self._figure.canvas.draw()

            if self._callback_capture is not None:
                if self._mask_type == 'circle':
                    center = self._capture_points[0]
                    pnt = self._capture_points[1]
                    radius = np.sqrt((center[0] - pnt[0])**2 + (center[1] - pnt[1])**2)
                    self._callback_capture(self._mask_type, [center, radius])
                elif self._mask_type == 'rect':
                    p1 = self._capture_points[0]
                    p2 = self._capture_points[1]
                    low_p = [min(p1[0], p2[0]), min(p1[1], p2[1])]
                    up_p = [max(p1[0], p2[0]), max(p1[1], p2[1])]
                    self._callback_capture(self._mask_type, [low_p, up_p])
            return

        if self._mask_form is None:
            self._mask_form = Line2D([], [], color='black', linewidth=2)
            self._axes.add_line(self._mask_form)
            self._figure.canvas.draw()

    def _on_mouse_motion(self, event):
        if not self._start_capture:
            return

        if len(self._capture_points) != 1:
            return

        if self._mask_type is None:
            return

        if event.xdata is None or event.ydata is None:
            return

        x, y = self._capture_points[0]

        if self._mask_type == 'circle':
            t = np.linspace(0, 2*np.pi, 40)
            radius = np.sqrt((event.xdata - x)**2 + (event.ydata - y)**2)
            xs = radius * np.cos(t) + x
            ys = radius * np.sin(t) + y
        elif self._mask_type == 'rect':
            xs = [x, event.xdata, event.xdata, x, x]
            ys = [y, y, event.ydata, event.ydata, y]

        if self._mask_form is None:
            self._mask_form = Line2D(xdata=xs, ydata=ys, color='black', linewidth=2)
            self._axes.add_line(self._mask_form)
        else:
            self._mask_form.set_data(xs, ys)
        self._figure.canvas.draw()