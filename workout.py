import os
import sys
import inspect
#import win32com.shell.shell as shell
import _winreg # http://docs.python.org/2.7/library/_winreg.html?highlight=winreg#_winreg
import ctypes # http://docs.python.org/2.7/library/ctypes.html#module-ctypes
import wmi # http://timgolden.me.uk/python/wmi/index.html

from ctypes import windll # loads libs exporting via stdcall
from ctypes import wintypes
from ctypes import cdll # loads libs exporting via cdecl

commotion_BSSID = '12CAFFEEBABE' # shows up in a few Commotion places
commotion_SSID = 'commotion-wireless.net'
ASADMIN = 'asadmin'
xml_profile_path = "commotion_wireless_profile.xml"

WMI = wmi.WMI()

# via http://stackoverflow.com/questions/279237/import-a-module-from-a-folder
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(
		inspect.currentframe()
))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(
                inspect.getfile(inspect.currentframe()
))[0], "PyWiWi")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

import WindowsWifi as PyWiWi

print 'You must run this script as an administrator'

with open(xml_profile_path, "r") as f_profile:
    commotion_wlan_profile_xml = "".join(line.rstrip() for line in f_profile)

# scan for existing Commotion wireless networks
ifaces = PyWiWi.getWirelessInterfaces()
net_list = []
for iface in ifaces:
    networks = PyWiWi.getWirelessNetworkBssList(iface)
    for network in networks:
        net_list.append({"interface": iface,
                         "network": network,
                         "commotion": "+" if (network.bssid ==
                                      commotion_BSSID) else
                                      "-"})

# choose desired network
net_list.sort(key=lambda opt: opt["network"].link_quality, reverse=True)
print "#  CW? Interface     Qual BSSID             SSID"
for idx, net in enumerate(net_list):
    print "".join(["{0:>2} ",
                   "{3:^3.3} ",
                   "{1.description:13.13} ",
                   "{2.link_quality:>3}% ",
                   "{2.bssid} ",
                   "{2.ssid}"]).format(idx,
                                       net["interface"],
                                       net["network"],
                                       net["commotion"])
# FIXME: below will just exit due to int if Q or other letter entered
target_net = net_list[int(raw_input("Enter the # of the network to join or Q to exit: "))]

print "network", target_net["network"]
print "interface", target_net["interface"]

# connect to chosen network
cnxp = {"connectionMode": 1,
        "profile": commotion_wlan_profile_xml,
        "ssid": target_net["network"].ssid,
        "bssidList": target_net["network"].bssid,
        "bssType": target_net["network"].bss_type,
        "flags": 0x00000000}
PyWiWi.connect(target_net["interface"], cnxp)

# stay connected until done
holdup = ''
while holdup != '!':
    holdup = raw_input("Enter ! to disconnect\n")

# disconnect from current network
PyWiWi.disconnect(target_net["interface"])



# show current info for adapter


# go back to old configuration when ready
holdup = ''
while holdup != '!':
    holdup = raw_input("Enter ! to go back to previous settings\n")

