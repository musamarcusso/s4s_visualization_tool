__author__ = 'Musa Morena Marcusso Manhaes'

import sys
import os

try:
    import pygtk
    pygtk.require('2.0')
except:
    raise ImportError('Error importing PyGTK')

try:
    import gtk
    import gtk.glade
except:
    raise ImportError('Error importing Glade dependencies')

from processor import S4SProcessor


class S4SBase:
    _GLADE_FILE = 'gui/S4SVisualisationTool.glade'
    _THEME = '../Resources/GUI/Themes/Vista-Gray/gtk-2.0/gtkrc'
    _GLADE = None
    _S4S_INSTANCE = None
    _IS_THEME_APPLIED = False
    _PROCESSOR = None
    _MAIN_ICON = './gui/icons/main_icon.ico'

    def __init__(self):
        # List of signals to be connected
        self._signals = {}
        # Set GTK theme and set static flag to true
        if os.name is not 'posix' and not S4SBase._IS_THEME_APPLIED:
            gtk.rc_parse(self._THEME)
            S4SBase._IS_THEME_APPLIED = True

        self._init_widgets = []

    @property
    def builder(self):
        if S4SBase._GLADE is None:
            print 'Loading builder'
            S4SBase._GLADE = gtk.Builder()
            S4SBase._GLADE.add_from_file(self._GLADE_FILE)
        return S4SBase._GLADE

    @property
    def engine(self):
        if S4SBase._S4S_INSTANCE is None:
            print 'Loading Scan4Surf engine'
            S4SBase._S4S_INSTANCE = None

        return S4SBase._S4S_INSTANCE

    @property
    def processor(self):
        # Creating instance of the backend processor
        if S4SBase._PROCESSOR is None:
            S4SBase._PROCESSOR = S4SProcessor.S4SProcessor()
        return S4SBase._PROCESSOR

    def activate_widgets(self):
        self._set_widget_sensitive(True)

    def deactivate_widgets(self):
        self._set_widget_sensitive(False)

    def _set_widget_sensitive(self, is_sensitive=True):
        for key in self._signals:
            self.builder.get_object(key).set_sensitive(is_sensitive)

    def connect_all_signals(self):
        if self.builder is None:
            raise TypeError('Glade file was not loaded')

        for key in self._signals:
            self.builder.get_object(key).connect(self._signals[key][0], self._signals[key][1])

    def _enable_widgets(self, list_widgets, is_enabled=True):
        for widget in list_widgets:
            self.builder.get_object(widget).set_sensitive(is_enabled)

    def _set_window_icon(self, window):
        try:
            window.set_icon_from_file(self._MAIN_ICON)
        except:
            pass

    def _init_combobox(self, labels_dict):
        try:
            for key in labels_dict:
                if key in self._init_widgets:
                    continue
                else:
                    self._init_widgets.append(key)
                list_store_mask = gtk.ListStore(str)
                cell = gtk.CellRendererText()
                self.builder.get_object(key).pack_start(cell)
                self.builder.get_object(key).add_attribute(cell, 'text', 0)
                for label in labels_dict[key]:
                    list_store_mask.append([label])
                model = self.builder.get_object(key).get_model()
                if model is not None:
                    del model
                self.builder.get_object(key).set_model(list_store_mask)
                self.builder.get_object(key).set_active(0)
        except Exception, e:
            print e

    def _init_spin_button(self, label, range, value, increments, digits):
        try:
            if label in self._init_widgets:
                return
            else:
                self._init_widgets.append(label)

            sb = self.builder.get_object(label)
            sb.set_range(range[0], range[1])
            sb.set_value(value)
            sb.set_increments(increments[0], increments[1])
            sb.set_digits(digits)
        except Exception, e:
            print e

    def _get_active_from_combo(self, label):
        try:
            combo = self.builder.get_object(label)
            index = combo.get_active()
            model = combo.get_model()
            return model[index][0]
        except Exception, e:
            print e
            return None

    def _set_active_in_combo(self, label, item):
        try:
            combo = self.builder.get_object(label)
            index = 0
            model = combo.get_model()
            iter = model.get_iter_root()
            while iter:
                if model.get_value(iter, 0) == item:
                    combo.set_active(index)
                    break
                index += 1
                iter = model.iter_next(iter)
        except Exception, e:
            print e
            return None

