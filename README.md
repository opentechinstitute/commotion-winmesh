## Development environment setup

Platform: Debian Wheezy.

### Cross-compiling olsrd for Windows on Debian

#### 32-bit
From the olsrd build documentation:
``
# Notes for compiling olsrd.exe under Windows using MinGW
# ----------------------------------------------------
# You can build olsrd.exe using MinGW on either Windows or GNU/Linux.
# For MinGW on Windows, run this in the msys shell:
#
#   cd olsrd
#   make clean_all
#   make build_all OS=win32
#
# MinGW also runs on GNU/Linux so you can build Windows binaries on
# any GNU/Linux machine.  It is especially easy on a
# Debian/Ubuntu/Mint system:
#
#   sudo apt-get install mingw32 flex bison make
#   cd olsrd
#   make clean_all
#   CC=i586-mingw32msvc-gcc make build_all OS=win32
``
#### 64-bit (Buggy - proceed at your own risk)_
1. The version of mingw-w64 in the Debian Wheezy repository has a bug (fixed
   in [changeset
   5386](http://sourceforge.net/apps/trac/mingw-w64/changeset/5386)) which
   causes problems for us, so we need to use a newer version.

1. ``> apt-get install dpkg-cross bison flex``

1. Download and unzip [olsrd](http://www.olsr.org/releases/0.6/olsrd-0.6.6.tar.gz)
where you want to work. The [OTI olsrd](https://github.com/opentechinstitute/olsrd)
will work just as well and includes more plugins.

1. Change to the olsrd directory.

1. ``> CC=i686-w64-mingw32-gcc make build_all OS=win32``

### Preparing the Windows development environment

Platform: Windows 7 Professional

1. Install [Git for Windows](http://git-scm.com/download/win)

1. Install the python.org [Python
   2.7.5](http://www.python.org/ftp/python/2.7.5/python-2.7.5.msi)

1. setup your path variables, e.g. adding C:\Python27 and C:\Python27\Scripts

1. Install the
   [pywin32](http://sourceforge.net/projects/pywin32/files/?source=navbar) Python
   extension

1. Install the [WMI](https://pypi.python.org/pypi/WMI/) Python extension

1. Install the [Comtypes](http://sourceforge.net/projects/comtypes/files/comtypes/) Python extension

1. Install [PyGTK](http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/) using an all-in-one installer

1. Install setuptools via these directions: [Install or Upgrade Setuptools](http://www.pip-installer.org/en/latest/installing.html#install-or-upgrade-setuptools)

1. Install pip via these directions: [Install or Upgrade pip](http://www.pip-installer.org/en/latest/installing.html#install-or-upgrade-pip)

1. Install pyjavaproperties via pip: `pip install pyjavaproperties`

1. Install pyinstaller via pip: `pip install pyinstaller`


### Building winmesh.exe

1. ``git clone`` this repo

1. ``cd commotion-winmesh``

1. ``git submodule init``

1. ``git submodule update`` to pull in dependencies

To make a development build with console, run:

``pyinstaller --manifest=manifest.xml winmesh.spec``

To make a release build that hides the console, run:

``build.bat``

Copy the olsrd binary and plugins (if applicable) that were compiled in the first step into commotion-winmesh/olsrd

###olsrd.conf
- Paths to plugins must be specified relative to `olsrd.exe`. We keep `olsrd.exe`
and all the plugin `.dll` files in the `olsrd` subdirectory.
- The main script generates a new `[ssid].olsrd.conf` file locally for each profile.
To make changes for all profiles, edit `templates/olsrd.conf.py`.

###General notes / Issues
- OLSRd will preemptively disable ICMP redirect processing in the registry on first run. It's not an option, and OLSRd doesn't give any advance warning. Afterward, a reboot is required.

- Windows Firewall will try to block olsrd.exe, you might need to restart the app and try connecting again after approving it

- Windows will make you chose home/work/public when you join the network, this might cause issues

- If the app crashes and you joined a mesh that was configured to have a static IP, you will be left in a "broken" network state, to get back online simply manually set your tcp/ip settings to DHCP

- There may be an issue with the Administrator rights not sticking on first run.  If you have trouble bringing up the mesh, try quitting and restarting

###Credits

Commotion Winmesh was developed by [Scal.io](http://scal.io) with the generous support of [Open Technology Institute](http://oti.newamerica.net/).

- [Josh Steiner](https://github.com/vitriolix/)
- [Jonathan Nelson](https://github.com/jnelson/)
