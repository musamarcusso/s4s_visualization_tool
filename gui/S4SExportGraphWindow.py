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


class S4SExportGraphWindow(object, S4SBase.S4SBase):
    def __init__(self, orientation, paper_type, format, callback):
        S4SBase.S4SBase.__init__(self)

        self._signals = {'ok_figure': ('clicked', self._ok_clicked),
                         'cancel_figure': ('clicked', self._cancel_clicked),
                         'save_figure_as': ('clicked', self._save_as_clicked)}

        self._init_spin_button(label='dpi_spin', range=[100,1000], value=600, increments=[100,1], digits=0)
        labels = {'orientation_combo': orientation,
                  'paper_type_combo': paper_type,
                  'format_combo': format}

        self._init_combobox(labels)

        self._filename = ''
        self._callback = callback

        self._window = self.builder.get_object('export_fig_window')
        self._window.set_title('Export figure...')
        self._window.set_position(gtk.WIN_POS_CENTER)
        self._set_window_icon(self._window)

        self.connect_all_signals()

    @property
    def dpi(self):
        return self.builder.get_object('dpi_spin').get_value()

    @property
    def paper_type(self):
        return self._get_active_from_combo('paper_type_combo')

    @property
    def orientation(self):
        return self._get_active_from_combo('orientation_combo')

    @property
    def format(self):
        return self._get_active_from_combo('format_combo')

    @property
    def filename(self):
        return self.builder.get_object('figure_name_entry').get_text()

    def open(self):
        self._filename = ''
        self.builder.get_object('figure_name_entry').set_text(self._filename)
        self.builder.get_object('dpi_spin').set_value(600)
        combos = ['orientation_combo', 'paper_type_combo', 'format_combo']
        for combo in combos:
            self.builder.get_object(combo).set_active(0)
        self._window.show()

    def _ok_clicked(self, widget):
        self._callback()
        self.builder.get_object('export_fig_window').hide()

    def _cancel_clicked(self, widget):
        self.builder.get_object('export_fig_window').hide()

    def _save_as_clicked(self, widget):
        dialog = gtk.FileChooserDialog("Save figure as...", None, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL,
                                                                                                 gtk.RESPONSE_CANCEL,
                                                                                                 gtk.STOCK_SAVE_AS,
                                                                                                 gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_CANCEL)
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            self._filename = dialog.get_filename()
        else:
            self._filename = ''

        self.builder.get_object('figure_name_entry').set_text(self._filename)

        dialog.destroy()



