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

from gui import S4SMainWindow


class S4SVisualisationTool:
    def __init__(self):
        self._gui = S4SMainWindow.S4SMainWindow()

if __name__ == '__main__':
    tool = S4SVisualisationTool()

    gobject.threads_init()
    gtk.gdk.threads_init()
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()

