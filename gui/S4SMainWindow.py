__author__ = 'Musa Morena Marcusso Manhaes'

import os
from copy import deepcopy
import datetime

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

import time
import S4SBase
import S4SCanvas
import S4SImportWizardWindow
from processor import S4SMessageHandler


class S4SMainWindow(S4SBase.S4SBase):
    _DEFAULT_EXT = ['asc']
    _WIDGETS_ACTIVE_AFTER_LOADED = ['notebook', 'save_cur_image', 'set_3d_toolbar', 'set_equal_scale',
                                    'set_scatter_plot', 'set_plane_fit', 'center_color', 'reset_color',
                                    'add_circle_mask', 'add_rect_mask', 'exclude_points', 'delete_all_masks',
                                    'file_label', 'file_comment']
    _ICON_IMAGES = {'set_3d_image': './gui/icons/3d_icon.png',
                    'set_equal_scale_image': './gui/icons/equal_icon.png',
                    'set_scatter_plot_image': './gui/icons/scatter_icon.png',
                    'set_plane_fit_image': './gui/icons/fit_icon.png',
                    'open_plot_options_image': './gui/icons/options_icon.png',
                    'center_color_image': './gui/icons/center_icon.png',
                    'reset_color_image': './gui/icons/reset_colors_icon.png',
                    'add_circle_mask_image': './gui/icons/circle.png',
                    'add_rect_mask_image': './gui/icons/rect.png',
                    'exclude_points_image': './gui/icons/exclude.png',
                    'delete_all_masks_image': './gui/icons/erase.png'}

    def __init__(self):
        S4SBase.S4SBase.__init__(self)

        self._message_handler = S4SMessageHandler.S4SMessageHandler.get_instance()
        self._message_handler.set_callback(self._update_status_bar)

        # List all the signals to be connected
        self._signals = {'main_window': ('destroy', self.close_all),
                         'open_dir': ('clicked', self._open_dir_clicked),
                         'open_cur_file': ('clicked', self._open_cur_file_clicked),
                         'open_file': ('clicked', self._open_cur_file_clicked),
                         'load_file': ('clicked', self._load_file_clicked),
                         'save_cur_image': ('clicked', self._save_cur_image_clicked),
                         'open_plot_options': ('clicked', self._open_plot_options_clicked),
                         'add_circle_mask': ('clicked', self._add_new_circle_mask_clicked),
                         'add_rect_mask': ('clicked', self._add_new_rect_mask_clicked),
                         'extensions_entry': ('activate', self._ext_text_changed),
                         'file_label': ('activate', self._file_label_changed),
                         'file_comment': ('activate', self._file_comment_changed)}

        self.connect_all_signals()

        # Set some of the icon images (not using libglade)
        for key in self._ICON_IMAGES:
            self.builder.get_object(key).set_from_file(self._ICON_IMAGES[key])

        self._enable_widgets(self._WIDGETS_ACTIVE_AFTER_LOADED, False)

        # Setting the canvas for the plots
        self._canvas = S4SCanvas.S4SCanvas()
        self._import_wizard = S4SImportWizardWindow.S4SImportWizardWindow(open_file_callback=self._load_file_with_properties)

        self.processor.set_callback_fcn('update_data', self._update_plot)
        self.processor.set_callback_fcn('update_filter', self._update_plot)
        self.processor.set_callback_fcn('is_loaded', self.enable_widgets)
        self.processor.set_callback_fcn('is_loaded', self.callback_loaded_file)

        if self.processor.current_directory is None:
            self._cur_directory = os.getcwd()
        else:
            self._cur_directory = self.processor.current_directory

        self._cur_file = ''
        self._max_elem = 23
        self._set_dir_string()

        # Setting the extensions for measurement files
        self._file_ext = deepcopy(self._DEFAULT_EXT)

        self._spinner = self.builder.get_object('spinner')

        # Files list tree view
        self._treeview_files = gtk.TreeView()
        tree_selection = self._treeview_files.get_selection()
        tree_selection.set_mode(gtk.SELECTION_SINGLE)
        tree_selection.connect('changed', self._file_selection_changed)

        self._files_store = gtk.TreeStore(gobject.TYPE_STRING,
                                          gobject.TYPE_STRING,
                                          gobject.TYPE_STRING)

        # Set the file table columns
        self._files_cols = [gtk.TreeViewColumn('Files'),
                            gtk.TreeViewColumn('Size'),
                            gtk.TreeViewColumn('Last modified')]

        self._cell_rend_text = [gtk.CellRendererText(),
                                gtk.CellRendererText(),
                                gtk.CellRendererText()]

        # Set maximum width for the column with the file name information
        self._files_cols[0].set_max_width(200)
        # Add all columns to the files tree view
        for i in range(len(self._files_cols)):
            col = self._files_cols[i]
            self._treeview_files.append_column(col)
            col.pack_start(self._cell_rend_text[i], expand=True)
            col.add_attribute(self._cell_rend_text[i], 'text', i)

        self._treeview_files.set_model(self._files_store)
        self._treeview_files.set_headers_visible(True)
        self._update_files_table()

        # Details tree view
        self._treeview_details = gtk.TreeView()
        self._details_store = gtk.ListStore(str, str)
        self._files_cols[2].set_sort_column_id(2)
        # Set the details table columns
        self._details_cols = [gtk.TreeViewColumn('Information'), gtk.TreeViewColumn('Value')]

        for i in range(len(self._details_cols)):
            cell_rend = gtk.CellRendererText()
            self._details_cols[i].pack_start(cell_rend)
            self._details_cols[i].add_attribute(cell_rend, 'text', i)
            self._treeview_details.append_column(self._details_cols[i])

        self._treeview_details.set_model(self._details_store)
        self._update_details_table()

        self._treeview_files.set_reorderable(True)

        # Add the tree view to the scrolled area
        self.builder.get_object('scrolledwindow_files').add(self._treeview_files)
        self.builder.get_object('scrolledwindow_details').add(self._treeview_details)

        self._ext_entry = self.builder.get_object('extensions_entry')
        self._set_extensions()

        self._timestamp = 0
        # Main window
        self._window = self.builder.get_object('main_window')
        self._treeview_files.show_all()
        self._treeview_details.show_all()
        self._set_window_icon(self._window)
        self._window.show_all()

    def tic(self):
        self._timestamp = time.time()

    def toc(self):
        return time.time() - self._timestamp

    def enable_widgets(self):
        if self.processor.is_data_loaded:
            self._enable_widgets(self._WIDGETS_ACTIVE_AFTER_LOADED)

    def close_all(self, widget=None):
        self.processor.store_cur_directory()
        gtk.main_quit()

    def _save_cur_image_clicked(self, widget):
        if not self.processor.is_data_loaded:
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
            dialog.set_markup('No file has been loaded')
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()
        else:
            self._canvas.save_fig()

    def _set_dir_string(self):
        cur_dir = '...'
        if len(self._cur_directory) < self._max_elem:
            cur_dir = deepcopy(self._cur_directory)
        else:
            for i in range(len(self._cur_directory) - self._max_elem, len(self._cur_directory)):
                cur_dir += self._cur_directory[i]
        # Set the current directory to the backend processor
        self.processor.current_directory = self._cur_directory
        self.builder.get_object('root_directory_label').set_text(cur_dir)
        self._message_handler.push_message('Main window', 'info', 'New directory selected: ' + self._cur_directory)

    def _set_file_string(self):
        cur_file = '...'
        if len(self._cur_file) < self._max_elem:
            cur_file = deepcopy(self._cur_file)
        else:
            for i in range(len(self._cur_file) - self._max_elem, len(self._cur_file)):
                cur_file += self._cur_file[i]
        # Update filename in the processor
        self.processor.current_file = self._cur_file
        self.builder.get_object('current_file_label').set_text(cur_file)
        self._message_handler.push_message('Main window', 'info', 'New file selected: ' + self._cur_file)

    def _set_extensions(self):
        input_ext = self._file_ext[0]
        if len(self._file_ext) > 1:
            for i in range(1, len(self._file_ext)):
                input_ext = input_ext + ';' + self._file_ext[i]

        self._ext_entry.set_text(input_ext)
        self._update_files_table()

    def _ext_text_changed(self, widget):
        entry_text = widget.get_text()
        ext_list = entry_text.split(';')
        for ext in ext_list:
            if not ext.isalpha():
                self._set_extensions()
                return
        self._file_ext = ext_list
        self._set_extensions()

    def _update_files_table(self):
        if self._files_store:
            self._files_store.clear()

        files = []
        last_mod = []
        sizes = []
        for f in os.listdir(self._cur_directory):
            for ext in self._file_ext:
                if '.' + ext in f:
                    full_path = os.path.join(self._cur_directory, f)

                    files.append(f)
                    last_mod.append(os.path.getmtime(full_path))
                    sizes.append(int(os.path.getsize(full_path) * 0.001))

        sort_idx = sorted(range(len(last_mod)), key=lambda k: last_mod[k])
        convert_size = lambda x: str(size) + ' kB' if size < 1000  else str(float(size / 1000.0)) + ' MB'

        for i in sort_idx:
            file = files[i]
            lm = last_mod[i]
            size = sizes[i]
            self._files_store.append(None, [file,
                                            convert_size(size),
                                            datetime.datetime.fromtimestamp(lm)])

        self._treeview_files.expand_all()

    def _update_details_table(self):
        if self._details_store:
            self._details_store.clear()
            for key in self.processor.data_details_labels:
                self._details_store.append([self.processor.data_details_labels[key],
                                            str(self.processor.data_details[key])])
            self._treeview_details.set_model(self._details_store)

    def _update_plot(self):
        self._canvas.plot(*self.processor.get_points())
        if self.processor.get_use_plane():
            self._canvas.add_plane(*self.processor.get_plane())
        self._canvas.set_title(self._cur_file)
        self._update_details_table()

    def callback_loaded_file(self):
        gobject.idle_add(self.builder.get_object('spinner').stop)
        if not self.processor.is_data_loaded:
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_YES_NO)
            dialog.set_markup('An error occurred while loading the file. Do you want to open the import wizard?')
            dialog.set_position(gtk.WIN_POS_CENTER)
            response = dialog.run()
            dialog.destroy()
            if response == gtk.RESPONSE_YES:
                self._import_wizard.open(self.processor.current_directory, self.processor.current_file)
                self._message_handler.push_message('Main window', 'info', 'Opening import wizard')
        else:
            self._message_handler.push_message('Main window', 'info', 'File opened: %s' % self.processor.current_file)
            self._canvas.delete_masks()

        self.builder.get_object('load_file').set_stock_id(gtk.STOCK_APPLY)
        self._enable_widgets(self._WIDGETS_ACTIVE_AFTER_LOADED, True)

        print 'label', self.processor.get_data_label()
        print 'comment', self.processor.get_data_comment()

        gtk.gdk.threads_enter()
        self.builder.get_object('file_label').set_text(self.processor.get_data_label())
        self.builder.get_object('file_comment').set_text(self.processor.get_data_comment())
        gtk.gdk.threads_leave()

    def callback_add_mask(self, mask_type, points):
        if mask_type not in ['circle', 'rect']:
            return
        if type(points) != list:
            return
        if len(points) != 2:
            return

        if mask_type == 'circle':
            index = self.processor.add_circle_mask(center=[points[0][0], points[0][1], 0.0], radius=float(points[1]),
                                                   plan='xy',
                                                   is_exc=self.builder.get_object('exclude_points').get_active())
        elif mask_type == 'rect':
            index = self.processor.add_rect_mask(low_point=list(points[0]), upper_point=list(points[1]),
                                                 is_exc=self.builder.get_object('exclude_points').get_active())

        self.processor.set_mask_active(index, True)
        self.processor.update_masks()
        self._canvas.options_win.update_masks()
        self._update_plot()

    def _add_new_circle_mask_clicked(self, widget):
        self._canvas.start_capture('circle', self.callback_add_mask)

    def _add_new_rect_mask_clicked(self, widget):
        self._canvas.start_capture('rect', self.callback_add_mask)

    # -------------------------------------------------------------------------------
    # Signal callback function
    # -------------------------------------------------------------------------------

    def _file_label_changed(self, widget):
        self.processor.set_data_label(widget.get_text())

    def _file_comment_changed(self, widget):
        self.processor.set_data_comment(widget.get_text())

    def _update_status_bar(self, message):
        self.builder.get_object('statusbar').push(0, message)

    def _open_plot_options_clicked(self, widget):
        self._canvas.options_win.open()

    def _load_file_with_properties(self, comment='#', separator='', skip_row=0):
        if not self.processor.is_data_loading():
            self._canvas.clear_figure()
            self.builder.get_object('spinner').start()

            self.builder.get_object('load_file').set_stock_id(gtk.STOCK_MEDIA_PAUSE)
            self._enable_widgets(self._WIDGETS_ACTIVE_AFTER_LOADED, False)
            self.processor.load_file(comment, separator, 0)
            self.tic()
        else:
            if self.toc() < 0.5:
                return
            self.processor.stop_loading()
            self.builder.get_object('load_file').set_stock_id(gtk.STOCK_APPLY)
            self.builder.get_object('spinner').stop()

    def _load_file_clicked(self, widget=None):
        if not self.processor.is_data_loading():
            self._canvas.clear_figure()
            if self.processor.current_file is None:
                dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
                dialog.set_markup('No file has been selected')
                dialog.set_position(gtk.WIN_POS_CENTER)
                dialog.run()
                dialog.destroy()
                self._message_handler.push_message('Main window', 'error', 'No file has been selected')
                return

            self.builder.get_object('spinner').start()

            self.builder.get_object('load_file').set_stock_id(gtk.STOCK_MEDIA_PAUSE)
            self._enable_widgets(self._WIDGETS_ACTIVE_AFTER_LOADED, False)
            self.processor.load_file()

            self.tic()
        else:
            if self.toc() < 0.5:
                return
            self.processor.stop_loading()
            self.builder.get_object('load_file').set_stock_id(gtk.STOCK_APPLY)
            self.builder.get_object('spinner').stop()

    def _open_dir_clicked(self, widget):
        # Create the dialog to open a new directory
        dialog = gtk.FileChooserDialog('Open...',
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(self._cur_directory)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            # Set the new directory
            self._cur_directory = dialog.get_current_folder()
            self._set_dir_string()
            self._update_files_table()

        dialog.destroy()

    def _open_cur_file_clicked(self, widget):
        dialog = gtk.FileChooserDialog('Open...',
                                       None,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(self._cur_directory)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self._cur_directory = dialog.get_current_folder()
            file_path = dialog.get_filename().split('/')
            self._cur_file = file_path[-1]
            self._set_dir_string()
            self._set_file_string()
            self._update_files_table()

        dialog.destroy()

    def _file_selection_changed(self, tree_selection):
        (model, pathlist) = tree_selection.get_selected_rows()
        for path in pathlist:
            tree_iter = model.get_iter(path)
            value = model.get_value(tree_iter, 0)
            self._cur_file = value
            self._set_file_string()