__author__ = 'Musa Morena Marcusso Manhaes'

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
import S4SBase


class S4SImportWizardWindow(S4SBase.S4SBase):
    _MAX_LINES = 100

    def __init__(self, open_file_callback=None):
        S4SBase.S4SBase.__init__(self)

        if open_file_callback is None:
            raise TypeError('Open file callback is invalid')

        self._open_file_fcn = open_file_callback

        self._signals = {'import_wizard_window': ('destroy', self.close),
                         'ok_import': ('clicked', self._ok_button_clicked),
                         'cancel_import': ('clicked', self.close),
                         'comment_entry': ('activate', self._comment_changed),
                         'separator_entry': ('activate', self._separator_changed)}

        self._window = self.builder.get_object('import_wizard_window')
        self._window.set_title('Import wizard')
        self._window.set_position(gtk.WIN_POS_CENTER)

        self._file_config = {'delimiter': '',
                             'comments': '#',
                             'first_row': 0}

        self.builder.get_object('comment_entry').set_text(self._file_config['comments'])
        self.builder.get_object('separator_entry').set_text(self._file_config['delimiter'])

        sb = self.builder.get_object('start_line_spin')
        sb.set_range(0, self._MAX_LINES)
        sb.set_value(0)
        sb.set_increments(1, 1)
        sb.set_digits(0)

        self._text_view = gtk.TreeView()
        self._text_store = gtk.ListStore(str, str)
        cols = [gtk.TreeViewColumn('#'), gtk.TreeViewColumn('Text')]
        rends = [gtk.CellRendererText(), gtk.CellRendererText()]

        for col, rend, i in zip(cols, rends, range(len(cols))):
            self._text_view.append_column(col)
            col.pack_start(rend)
            col.add_attribute(rend, 'text', i)

        self._text_view.set_model(self._text_store)
        self._text_view.show_all()

        self.builder.get_object('scrolledwindow_text').add_with_viewport(self._text_view)

        self._path = None
        self._filename = None
        self._set_window_icon(self._window)
        self.connect_all_signals()

    def close(self, widget):
        self._window.hide()

    def _ok_button_clicked(self, widget):
        self._open_file_fcn(self.builder.get_object('comment_entry').get_text(),
                            self.builder.get_object('separator_entry').get_text(),
                            self.builder.get_object('start_line_spin').get_value())
        self._window.hide()


    def open(self, path, filename):
        if type(path) is not str or type(filename) is not str:
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
            dialog.set_markup('Invalid input filename')
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()
            return

        if not os.path.isdir(path):
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
            dialog.set_markup('Invalid directory')
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()
            return

        if not os.path.isfile(os.path.join(path, filename)):
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
            dialog.set_markup('Invalid filename')
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()
            return

        self._window.show()
        self._path = path
        self._filename = filename
        self._load_text()

    def _load_text(self):
        if type(self._path) is not str or type(self._filename) is not str:
            raise TypeError('File path or name is invalid')
        self._text_store.clear()

        try:
            data_file = open(os.path.join(self._path, self._filename))

            i = 0
            for line in data_file:
                file_line = line.replace("\n","")
                file_line = file_line.replace("\r", "")
                self._text_store.append([str(i), file_line])
                i += 1
                if i >= self._MAX_LINES:
                    break

            data_file.close()
        except Exception, e:
            print e

    def _comment_changed(self, widget):
        print widget.get_text()

    def _separator_changed(self, widget):
        print widget.get_text()





