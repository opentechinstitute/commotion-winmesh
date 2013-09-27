from distutils.core import setup
import py2exe
import os
import sys
from glob import glob

# Find GTK+ installation path
__import__('gtk')
m = sys.modules['gtk']
gtk_base_path = m.__path__[0]

setup(
    name = 'comwinui',
    description = 'Commotion Wireless for Windows',
    version = '1.0',

    windows = [
                  {
                      'script': 'comwinui.py',
                      'icon_resources': [(1, "commotion_fav.png")],
                  }
              ],

    options = {
                  'py2exe': {
                      'packages':'encodings',
                      # Optionally omit gio, gtk.keysyms, and/or rsvg if you're not using them
                      #'includes': 'cairo, pango, pangocairo, atk, gobject, gio, gtk.keysyms, rsvg',
                        'includes': 'cairo, pango, pangocairo, atk, gobject, gio, gtk.keysyms',
                  }
              },

    data_files=[
                   #'handytool.glade',
                   'jsoninfo.json',
                   ("Microsoft.VC90.CRT", glob(r'.\Microsoft.VC90.CRT\*.*')),
                   # If using GTK+'s built in SVG support, uncomment these
                   #os.path.join(gtk_base_path, '..', 'runtime', 'bin', 'gdk-pixbuf-query-loaders.exe'),
                   #os.path.join(gtk_base_path, '..', 'runtime', 'bin', 'libxml2-2.dll'),
               ]
)
