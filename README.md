## Development environment setup

Platform: Debian Wheezy.

### Cross-compiling olsrd for Windows on Debian

1. The version of mingw-w64 in the Debian Wheezy repository has a bug (fixed
   in [changeset
   5386](http://sourceforge.net/apps/trac/mingw-w64/changeset/5386)) which
   causes problems for us, so we need to use a newer version.


1. ``> apt-get install dpkg-cross bison flex``

1. Download and unzip [olsrd](http://www.olsr.org/releases/0.6/olsrd-0.6.6.tar.gz)
where you want to work. 

1. Change to the olsrd directory.

1. ``> CC=i686-w64-mingw32-gcc make build_all OS=win32``

__TODO__

### Preparing the Windows environment

Platform: Windows 7 Professional

1. Install the python.org [Python
   2.7.5](http://www.python.org/ftp/python/2.7.5/python-2.7.5.msi)

1. Install the
   [pywin32](http://sourceforge.net/projects/pywin32/files/?source=navbar) Python
   extension

1. Install the [WMI](https://pypi.python.org/pypi/WMI/) Python extension

1. Install the [Comtypes](http://sourceforge.net/projects/comtypes/files/comtypes/) Python extension

We also depend on the [winreg](http://docs.python.org/2/library/_winreg.html) and
[ctypes](http://docs.python.org/2/library/ctypes.html) Python extensions, but these
are built into Python 2.7.

###olsrd.conf
- olsrd.conf belongs in \Windows
- Paths to plugins must be specified relative to olsrd.exe
- You can also specify the olsrd.conf you want in the invocation. Give an invalid invocation and olsrd.exe will provide help.

###workout.py
Goal: workout.py is roughly tending toward [olsrd/files/olsrd-adhoc-setup](https://github.com/opentechinstitute/olsrd/blob/release-0.6.5.4/files/olsrd-adhoc-setup)


