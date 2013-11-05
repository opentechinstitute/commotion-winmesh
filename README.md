## Development environment setup

Platform: Debian Wheezy.

### Cross-compiling olsrd for Windows on Debian

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

### Building winmesh.exe

On a windows machine, run:

``pyinstaller winmesh.spec``

To build a release build that hides the console, run:

``pyinstaller --noconsole winmesh.spec``


__TODO__

### Preparing the Windows development environment

Platform: Windows 7 Professional

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
