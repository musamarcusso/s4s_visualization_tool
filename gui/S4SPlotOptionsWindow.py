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

import S4SBase


class S4SPlotOptionsWindow(S4SBase.S4SBase):
    def __init__(self, title, xlabel, ylabel, zlabel, colormaps, colormap_index, aspect_ratio, marker_size,
                 plot_types, plot_type_default, font_size, is_3d_active, is_scatter):
        S4SBase.S4SBase.__init__(self)

        assert type(title) == str
        assert type(xlabel) == str
        assert type(ylabel) == str
        assert type(zlabel) == str
        assert type(colormaps) == list
        assert marker_size > 0

        self._widgets_3d = ['xy_view_button', 'yz_view_button', 'xz_view_button', 'reset_camera', 'zlabel_entry',
                            'show_plane']

        self._signals = {'add_new_mask': ('clicked', self._add_new_mask_clicked),
                         'show_masks': ('toggled', self._show_masks_toggled),
                         'calc_plane': ('clicked', self._calc_plane_clicked),
                         'apply_plot_options': ('clicked', self._apply_plot_options_clicked),
                         'close_plot_options': ('clicked', self.close),
                         'xlabel_entry': ('activate', self._xlabel_edited),
                         'ylabel_entry': ('activate', self._ylabel_edited),
                         'zlabel_entry': ('activate', self._zlabel_edited),
                         'title_entry': ('activate', self._title_edited),
                         'xy_view_button': ('clicked', self._xy_view_clicked),
                         'yz_view_button': ('clicked', self._yz_view_clicked),
                         'xz_view_button': ('clicked', self._xz_view_clicked),
                         'reset_camera': ('clicked', self._reset_view_clicked),
                         'update_masks': ('clicked', self._update_masks_clicked),
                         'active_axis_button': ('clicked', self._active_axis_clicked),
                         'use_plan_for_color': ('toggled', self._colormap_plane_toggled),
                         'set_plane_fit': ('toggled', self._colormap_plane_toolbar_toggled),
                         'show_plane': ('toggled', self._show_plane_toggled),
                         'min_color_spin': ('value-changed', self._min_color_spin_changed),
                         'max_color_spin': ('value-changed', self._max_color_spin_changed),
                         'colormap_combo': ('changed', self._colormap_combo_changed),
                         'aspect_ratio_combo': ('changed', self._aspect_ratio_combo_changed),
                         'radius_spin': ('value-changed', self._radius_changed),
                         'font_size_spin': ('value-changed', self._font_size_changed),
                         'sampling_spin': ('value-changed', self._sampling_spin_changed),
                         'alpha_spin': ('value-changed', self._alpha_spin_changed),
                         'delete_masks': ('clicked', self._delete_masks_clicked),
                         'delete_all_masks': ('clicked', self._delete_masks_clicked),
                         'plot_type_combo': ('changed', self._plot_type_changed),
                         'apply_colormap': ('clicked', self._apply_colormap_clicked),
                         'toggle_plot': ('toggled', self._toggle_plot_type),
                         'set_3d_toolbar': ('toggled', self._toggle_plot_type_toolbar),
                         'set_equal_scale': ('toggled', self._plot_equal_toggled),
                         'set_scatter_plot': ('toggled', self._scatter_plot_toggled),
                         'center_color': ('clicked', self._center_colorbar_clicked),
                         'reset_color': ('clicked', self._reset_colorbar_clicked)}

        self._callback_fcn = {'title': None,
                              'xlabel': None,
                              'ylabel': None,
                              'zlabel': None,
                              'xy_view': None,
                              'yz_view': None,
                              'xz_view': None,
                              'reset_view': None,
                              'axis_on': None,
                              'axis_off': None,
                              'colormap': None,
                              'activate_plane': None,
                              'clim': None,
                              'aspect_ratio': None,
                              'marker_size': None,
                              'plot_type': None,
                              'is_3d': None,
                              'font_size': None}

        self.builder.get_object('set_3d_toolbar').set_active(is_3d_active)
        self.builder.get_object('toggle_plot').set_active(not is_3d_active)
        self.builder.get_object('set_scatter_plot').set_active(is_scatter)

        self._filter_index = 0

        self.builder.get_object('title_entry').set_text(title)
        self.builder.get_object('xlabel_entry').set_text(xlabel)
        self.builder.get_object('ylabel_entry').set_text(ylabel)
        self.builder.get_object('zlabel_entry').set_text(zlabel)

        self.processor.set_callback_fcn('update_data', self.update_widgets)

        self.connect_all_signals()

        self._window = self.builder.get_object('plot_options_window')
        self._window.set_title('Plotting options')
        self._window.set_deletable(False)
        self._set_window_icon(self._window)

        self._mask_table = gtk.TreeView()

        self.builder.get_object('scrolledwindow_mask').add_with_viewport(self._mask_table)
        self._mask_store = gtk.TreeStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_STRING,
                                         gobject.TYPE_BOOLEAN)
        cols = [gtk.TreeViewColumn('#'), gtk.TreeViewColumn('Mask'), gtk.TreeViewColumn('Details'),
                gtk.TreeViewColumn('Apply filter')]
        cell_rend = [gtk.CellRendererText(), gtk.CellRendererText(), gtk.CellRendererText(), gtk.CellRendererToggle()]

        for col, rend, i in zip(cols, cell_rend, range(len(cols))):
            self._mask_table.append_column(col)
            col.pack_start(rend)
            if i == 3:
                col.add_attribute(rend, 'active', i)
            else:
                col.add_attribute(rend, 'text', i)

            if i == 2:
                rend.set_property('editable', True)
                rend.connect('edited', self._cell_edited_callback, self._mask_store)
            elif i == 3:
                rend.set_property('active', True)
                rend.connect('toggled', self._filter_active_toggled, self._mask_store)

        self._mask_table.set_model(self._mask_store)
        self._mask_table.show_all()
        self._is_open = False

        # Setting the list of mask labels
        labels = {'combobox_mask_labels': self.processor.get_mask_labels(),
                  'plot_type_combo': plot_types,
                  'colormap_combo': colormaps,
                  'aspect_ratio_combo': aspect_ratio}

        self._init_combobox(labels)

        self._init_spin_button('sampling_spin', [1, 100], self.processor.get_step(), [1, 1], 0)
        self._init_spin_button('alpha_spin', [0.0, 1.0], 1.0, [0.1, 1], 1)
        self._init_spin_button('radius_spin', [1, 50], marker_size, [1, 1],0)
        self._init_spin_button('font_size_spin', [0, 25], font_size, [1, 1], 0)
        self._init_spin_button('min_color_spin', [-100, 100], 0, [0.01, 1], 2)
        self._init_spin_button('max_color_spin', [-100, 100], 0, [0.01, 1], 2)


        disabled_widgets = ['apply_colormap', 'update_masks', 'apply_plot_options', 'show_plane']
        [self.builder.get_object(key).set_sensitive(False) for key in disabled_widgets]

    @property
    def is_open(self):
        return self._is_open

    def set_callback_fcn(self, label, fcn):
        if label not in self._callback_fcn:
            raise KeyError('Invalid label for a callback function')

        self._callback_fcn[label] = fcn

    def set_clim(self, clim):
        assert type(clim) == list
        assert len(clim) == 2
        assert clim[0] < clim[1]
        self.builder.get_object('min_color_spin').set_value(clim[0])
        self.builder.get_object('min_color_spin').set_value(clim[1])

    def call_callback_fcn(self, label, arg=None):
        if label not in self._callback_fcn:
            raise KeyError('Invalid label for a callback function')
        if self._callback_fcn[label] is not None:
            if arg is None:
                self._callback_fcn[label]()
            else:
                self._callback_fcn[label](arg)

    def open(self):
        self._window.show_all()
        self._is_open = True

    def close(self, widget):
        self._window.hide()
        self._is_open = False

    def set_title(self, title):
        self.builder.get_object('title_entry').set_text(title)

    def get_plot_type(self):
        return self._get_active_from_combo('plot_type_combo')

    def delete_masks(self):
        self._mask_store.clear()

    def update_masks(self):
        self.delete_masks()
        idxs = self.processor.get_mask_indexes()
        for idx in idxs:
            self.add_mask_to_table(idx)
        self._mask_table.expand_all()

    def update_widgets(self):
        self.builder.get_object('sampling_spin').set_value(self.processor.get_step())

        iter = self._mask_store.get_iter_root()
        while iter:
            index = self._mask_store.get_value(iter, 0)
            active = self.processor.get_mask_active(index)
            self._mask_store.set_value(iter, 3, active)
            iter = self._mask_store.iter_next(iter)

        range_z = self.processor.get_c_range()
        if sum(range_z) != -2:
            self.builder.get_object('min_color_spin').set_range(-100, range_z[1])
            self.builder.get_object('min_color_spin').set_value(range_z[0])
            self.builder.get_object('max_color_spin').set_range(range_z[0], 100)
            self.builder.get_object('max_color_spin').set_value(range_z[1])

    def _center_colorbar_clicked(self, widget):
        range_z = [abs(x) for x in self.processor.get_c_range()]
        self.call_callback_fcn('clim', [-max(range_z), max(range_z)])
        self.builder.get_object('min_color_spin').set_value(-max(range_z))
        self.builder.get_object('max_color_spin').set_value(max(range_z))

    def _reset_colorbar_clicked(self, widget):
        range_z = self.processor.get_c_range()
        self.call_callback_fcn('clim', range_z)
        self.builder.get_object('min_color_spin').set_range(-100, range_z[1])
        self.builder.get_object('min_color_spin').set_value(range_z[0])
        self.builder.get_object('max_color_spin').set_range(range_z[0], 100)
        self.builder.get_object('max_color_spin').set_value(range_z[1])

    def _font_size_changed(self, widget):
        self.call_callback_fcn('font_size', widget.get_value())

    def _plot_equal_toggled(self, widget):
        self.call_callback_fcn('aspect_ratio', 'equal' if widget.get_active() else 'auto')
        self._set_active_in_combo('aspect_ratio_combo', 'equal' if widget.get_active() else 'auto')

    def _scatter_plot_toggled(self, widget):
        self.call_callback_fcn('plot_type', 'Scatter' if widget.get_active() else 'Surface')
        self._set_active_in_combo('plot_type_combo', 'Scatter' if widget.get_active() else 'Surface')
        self.builder.get_object('apply_plot_options').set_sensitive(False)

    def _delete_masks_clicked(self, widget):
        dialog = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
        dialog.set_markup('Would you like to delete all masks?')
        dialog.set_position(gtk.WIN_POS_CENTER)
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_YES:
            self.delete_masks()
            self.processor.delete_all_masks()

    def _toggle_plot_type(self, widget):
        if widget.get_active():
            widget.set_label('2D')
        else:
            widget.set_label('3D')
        for widget_label in self._widgets_3d:
            self.builder.get_object(widget_label).set_sensitive(not widget.get_active())
        self.call_callback_fcn('is_3d', not widget.get_active())
        clim = [self.builder.get_object('min_color_spin').get_value(),
                self.builder.get_object('max_color_spin').get_value()]
        self.call_callback_fcn('clim', clim)
        self.builder.get_object('set_3d_toolbar').set_active(not widget.get_active())

    def _toggle_plot_type_toolbar(self, widget):
        for widget_label in self._widgets_3d:
            self.builder.get_object(widget_label).set_sensitive(not widget.get_active())
        self.call_callback_fcn('is_3d', widget.get_active())
        clim = [self.builder.get_object('min_color_spin').get_value(),
                self.builder.get_object('max_color_spin').get_value()]
        self.call_callback_fcn('clim', clim)
        self.builder.get_object('toggle_plot').set_active(not widget.get_active())

    def _min_color_spin_changed(self, widget):
        sb = self.builder.get_object('max_color_spin')
        widget.set_range(-100, sb.get_value())
        self.builder.get_object('apply_colormap').set_sensitive(True)

    def _max_color_spin_changed(self, widget):
        sb = self.builder.get_object('min_color_spin')
        widget.set_range(sb.get_value(), 100)
        self.builder.get_object('apply_colormap').set_sensitive(True)

    def _apply_colormap_clicked(self, widget):
        clim = [self.builder.get_object('min_color_spin').get_value(),
                self.builder.get_object('max_color_spin').get_value()]
        self.call_callback_fcn('clim', clim)
        self.builder.get_object('apply_colormap').set_sensitive(False)

    def _show_plane_toggled(self, widget):
        if widget.get_active():
            widget.set_label('Showing on graph')
        else:
            widget.set_label('Hidden on graph')
        self.call_callback_fcn('activate_plane', widget.get_active())

    def _colormap_plane_toolbar_toggled(self, widget):
        self.builder.get_object('show_plane').set_sensitive(widget.get_active())
        self.builder.get_object('use_plan_for_color').set_active(widget.get_active())
        self.processor.set_use_plane(widget.get_active())


    def _colormap_plane_toggled(self, widget):
        if widget.get_active():
            widget.set_label('Color map enabled')
        else:
            self.builder.get_object('show_plane').set_active(False)
            widget.set_label('Color map disabled')
        self.builder.get_object('show_plane').set_sensitive(widget.get_active())
        self.builder.get_object('set_plane_fit').set_active(widget.get_active())
        self.processor.set_use_plane(widget.get_active())

    def _colormap_combo_changed(self, widget):
        index = widget.get_active()
        self.call_callback_fcn('colormap', index)

    def _aspect_ratio_combo_changed(self, widget):
        self.call_callback_fcn('aspect_ratio', self._get_active_from_combo('aspect_ratio_combo'))
        self.builder.get_object('set_equal_scale').set_active(self._get_active_from_combo('aspect_ratio_combo') ==
                                                              'equal')

    def _active_axis_clicked(self, widget):
        if widget.get_active():
            widget.set_label('Active')
            self.call_callback_fcn('axis_on')
        else:
            widget.set_label('Hidden')
            self.call_callback_fcn('axis_off')

    def _title_edited(self, widget):
        self.call_callback_fcn('title', widget.get_text())

    def _xlabel_edited(self, widget):
        self.call_callback_fcn('xlabel', widget.get_text())

    def _ylabel_edited(self, widget):
        self.call_callback_fcn('ylabel', widget.get_text())

    def _zlabel_edited(self, widget):
        self.call_callback_fcn('zlabel', widget.get_text())

    def _xy_view_clicked(self, widget):
        self.call_callback_fcn('xy_view')

    def _yz_view_clicked(self, widget):
        self.call_callback_fcn('yz_view')

    def _xz_view_clicked(self, widget):
        self.call_callback_fcn('xz_view')

    def _reset_view_clicked(self, widget):
        self.call_callback_fcn('reset_view')

    def _cell_edited_callback(self, cell, path, new_text, model=None):
        if len(path) == 1:
            return
        self.builder.get_object('update_masks').set_sensitive(True)
        child_iter = model.get_iter(path)
        parent_iter = model.iter_parent(child_iter)

        filter_name = model.get_value(parent_iter, 1)
        filter_index = model.get_value(parent_iter, 0)
        item = model.get_value(child_iter, 1)

        if item == 'Is excluding?':
            yes = ['yes', 'Yes', 'True', 'true', '1']
            no = ['no', 'No', 'False', 'false', '0']
            if new_text not in yes and new_text not in no:
                self._open_error_dialog('Invalid input for the exclusion flag')
            else:
                if self.processor.set_mask_param(filter_index, item, new_text in yes):
                    model.set_value(child_iter, 2, new_text in yes)
        elif filter_name == 'Range':
            if item == 'Axis':
                if new_text not in ['x', 'y', 'z']:
                    self._open_error_dialog('The valid axis are x, y, z')
                else:
                    if self.processor.set_mask_param(filter_index, item, new_text):
                        model.set_value(child_iter, 2, new_text)
            elif item == 'Lower':
                try:
                    value = float(new_text)
                    if self.processor.set_mask_param(filter_index, item, value):
                        model.set_value(child_iter, 2, str(value))
                except:
                    pass
            elif item == 'Upper':
                try:
                    value = float(new_text)
                    if self.processor.set_mask_param(filter_index, item, value):
                        model.set_value(child_iter, 2, str(value))
                except:
                    pass
        elif filter_name == 'Circle':
            if item == 'Plane':
                if new_text not in ['xy', 'yz', 'xz']:
                    self._open_error_dialog('The valid planes are xy, yz, xz')
                else:
                    if self.processor.set_mask_param(filter_index, item, new_text):
                        model.set_value(child_iter, 2, new_text)
            elif item == 'Radius':
                try:
                    value = float(new_text)
                    if self.processor.set_mask_param(filter_index, item, value):
                        model.set_value(child_iter, 2, str(value))
                except:
                    self._open_error_dialog('Invalid value for the radius')

            elif item == 'Center':
                try:
                    center_str = new_text.replace('[', '')
                    center_str = center_str.replace(']', '')
                    pos = [float(value) for value in center_str.split(' ')]
                    if len(pos) == 3:
                        if not self.processor.set_mask_param(filter_index, item, pos):
                            raise ValueError
                        else:
                            model.set_value(child_iter, 2, str(pos))
                except:
                    self._open_error_dialog('Invalid value center for the circle filter')
        elif filter_name == 'Rectangle':
            if item == 'Lower point':
                try:
                    center_str = new_text.replace('[', '')
                    center_str = center_str.replace(']', '')
                    pos = [float(value) for value in center_str.split(' ')]
                    if len(pos) == 2:
                        if not self.processor.set_mask_param(filter_index, item, pos):
                            raise ValueError
                        else:
                            model.set_value(child_iter, 2, str(pos))
                except:
                    pass
            elif item == 'Upper point':
                try:
                    center_str = new_text.replace('[', '')
                    center_str = center_str.replace(']', '')
                    pos = [float(value) for value in center_str.split(' ')]
                    if len(pos) == 2:
                        if not self.processor.set_mask_param(filter_index, item, pos):
                            raise ValueError
                        else:
                            model.set_value(child_iter, 2, str(pos))
                except:
                    pass


    def _filter_active_toggled(self, cell, path, model=None):
        if len(path) > 1:
            return
        iter = model.get_iter(path)
        flag = model.get_value(iter, 3)
        model.set_value(iter, 3, not flag)
        self.builder.get_object('update_masks').set_sensitive(True)

    def _apply_plot_options_clicked(self, widget):
        self.processor.set_step(self.builder.get_object('sampling_spin').get_value())
        self.call_callback_fcn('marker_size', self.builder.get_object('radius_spin').get_value())
        self.call_callback_fcn('plot_type', self._get_active_from_combo('plot_type_combo'))
        widget.set_sensitive(False)

    def _radius_changed(self, widget):
        self.builder.get_object('apply_plot_options').set_sensitive(True)

    def _sampling_spin_changed(self, widget):
        self.builder.get_object('apply_plot_options').set_sensitive(True)

    def _alpha_spin_changed(self, widget):
        self.builder.get_object('apply_plot_options').set_sensitive(True)

    def _plot_type_changed(self, widget):
        self.builder.get_object('apply_plot_options').set_sensitive(True)

    def _update_masks_clicked(self, widget):
        iter = self._mask_store.get_iter_root()
        while iter:
            index = self._mask_store.get_value(iter, 0)
            active = self._mask_store.get_value(iter, 3)
            self.processor.set_mask_active(int(index), active)
            iter = self._mask_store.iter_next(iter)
        widget.set_sensitive(False)
        self.processor.update_masks()

    def _add_new_mask_clicked(self, widget):
        combobox = self.builder.get_object('combobox_mask_labels')
        model = combobox.get_model()
        index = combobox.get_active()
        mask_label = model[index][0]

        if mask_label == 'Circle':
            index = self.processor.add_circle_mask()
        elif mask_label == 'Rectangle':
            index = self.processor.add_rect_mask()
        elif mask_label == 'Range':
            index = self.processor.add_range_mask()
        else:
            return

        self.add_mask_to_table(index)
        self._mask_table.expand_all()
        self.builder.get_object('update_masks').set_sensitive(True)

    def add_mask_to_table(self, index):
        mask_label = self.processor.get_mask_type(index)
        parent = self._mask_store.append(None, [int(index), mask_label, '', self.processor.get_mask_active(index)])
        i = 0
        param_values = self.processor.get_mask_info(index)
        for key in param_values:
            self._mask_store.append(parent, [int(i), key, param_values[key], False])
            i += 1
        self._mask_table.expand_all()

    def _show_masks_toggled(self, widget):
        if widget.get_active():
            widget.set_label('Masks plotted')
        else:
            widget.set_label('Masks hidden')

    def _open_error_dialog(self, message):
        dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.set_markup(message)
        dialog.run()
        dialog.destroy()

    def _calc_plane_clicked(self, widget):
        self.processor.calc_fitting_plane()

