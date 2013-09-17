import os
import sys
import inspect
import win32com.shell.shell as shell
import _winreg # http://docs.python.org/2.7/library/_winreg.html?highlight=winreg#_winreg
import ctypes # http://docs.python.org/2.7/library/ctypes.html#module-ctypes
import wmi # http://timgolden.me.uk/python/wmi/index.html
#import argparse

from ctypes import windll # loads libs exporting via stdcall
from ctypes import wintypes
from ctypes import cdll # loads libs exporting via cdecl

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

ASADMIN = 'asadmin'

#commotion_BSSID = 'CCCCCCCCCCCC' # doesn't work
#commotion_BSSID = 'C2CCCCCCCCCC' # works
commotion_BSSID = '12CAFFEEBABE' # shows up in a few Commotion places
""" Valid BSSID construction notes
	http://social.technet.microsoft.com/Forums/windows/en-US/59e07df3-471c-499e-ad5f-e7cb507595df/cannot-change-mac-address-in-windows-7-driver-has-option-doesnt-work-neither-does-regedit-ms

	MAC address:  "XY-XX-XX-XX-XX-XX"
	"X" can be anything hexadecimal.
	The hexadecimal "Y", written in binary format, is
	Y:  "kmnp",  where "p" is the least significant bit;
		p=0 --> unicast;
		p=1 --> multicast;

		n=0 --> globally assigned MAC;
		n=1 --> locally administered;

	So, actually MAC can be changed not only to 12-XX-...,
	but to any combination in which p=0 and n=1;
	"Y" can be 2, 6, A or E.
"""
commotion_SSID = 'commotion-wireless.net'

WMI = wmi.WMI()

print 'You must run this script as an administrator'

# choose an adapter for Commotion
adapters = WMI.Win32_NetworkAdapter()
for idx, adapter in enumerate(adapters):
    print '#{1.Index:>2} {1.MACAddress:17} {1.Name}'.format(idx, adapter)
target_adapter = int(raw_input("Enter the # of the adapter you want to use for Commotion: "))

# TODO: Is adapters[target_adapter].Index guaranteed to equal target_adapter?
wmi_adapter = adapters[target_adapter]
original_state = {"adapter_MAC": wmi_adapter.MACAddress,
                  "adapter_GUID": wmi_adapter.GUID,
                  "network_SSID": "",
                  "network_BSSID": "",
                  "adapter_enabled": wmi_adapter.NetEnabled}

print ' '.join(['Configuring', wmi_adapter.Name])

# enable or disable adapter
def set_adapter_state(wmi_adapter=None, verb='enable'):
    if (wmi_adapter is not None) and (verb is not None):
        status = {
            'enable': wmi_adapter.Enable,
            'disable': wmi_adapter.Disable
        }[verb]()
        if status[0] != 0:
            print ''.join(['Couldn\'t ', verb, ' adapter (error:', str(status[0]), ')'])
        else:
            print ''.join(['Adapter ', verb, 'd'])
        return status
    else:
        return None

# if adapter is currently disabled, enable it
set_adapter_state(wmi_adapter, 'enable')

# scan for networks with commotion_SSID
# future:
#    1. scan for commotion_BSSID
#    2. scan for commotion_SSID
#    3. if no target net after 1 & 2, then create new net

ifaces = PyWiWi.getWirelessInterfaces()
for idx, iface in enumerate(ifaces):
    print '#{1.Index:>2} {1.MACAddress:17} {1.Name}'.format(idx, adapter)
target_iface = int(raw_input("Enter the # of the adapter you want to use for Commotion: "))
commotions = []
for iface in ifaces:
    #print iface
    networks = PyWiWi.getWirelessAvailableNetworkList(iface)
    print ""
    for network in networks:
            print "SSID ", network.ssid
            print "BSS type ", network.bss_type
            print "signal quality ", network.signal_quality
            print "-" * 20
            #print network
            if network.ssid == commotion_SSID:
                commotions.append({"interface": iface,
                                   "network": network})
    print ""

for iface in ifaces:
    networks = PyWiWi.getWirelessNetworkBssList(iface)
    for network in networks:
        print "BSS\n", network, "\n"

# choose desired network
commotions.sort(key=lambda opt: opt["network"].signal_quality, reverse=True)
for idx, net in enumerate(commotions):
    print '#{0:>2} Quality:{1.signal_quality:3}% {1.ssid}'.format(idx, net["network"])
#target_net = commotions[int(raw_input("Enter the # of the network to join: "))]

#print "target_net", target_net

# disconnect from current network
#PyWiWi.disconnect(target_net["interface"])

# Change MAC of adapter_index to Commotion BSSID/MAC
# The key we need to add (MAC) is named 'NetworkAddress'
def set_MAC(wmi_adapter, new_MAC=original_state["MACAddress"]):
    key = _winreg.HKEY_LOCAL_MACHINE
    subkey = '\\'.join(['SYSTEM',
                        'CurrentControlSet',
                        'Control',
                        'Class',
                        '{4D36E972-E325-11CE-BFC1-08002BE10318}',
                        '{0:0>4}'.format(wmi_adapter.Index)
                        ])
    reg_adapter = _winreg.OpenKey(key, subkey, 0, _winreg.KEY_ALL_ACCESS)
    result = _winreg.SetValueEx(reg_adapter,
                                'NetworkAddress',
                                0,
                                _winreg.REG_SZ, new_MAC)
    reg_adapter.Close() # not strictly necessary
    print "set_MAC result", result
    return result

set_MAC(wmi_adapter, commotion_BSSID)

# cycle adapter (use new settings)
set_adapter_state(wmi_adapter, 'disable')
set_adapter_state(wmi_adapter, 'enable')

# connect to chosen Commotion net
#PyWiWi.WlanConnect(hClientHandle, pInterfaceGuid, pConnectionParameters)

# show current info for adapter


# go back to old configuration when ready
holdup = ''
while holdup != '!':
    holdup = raw_input("Enter ! to go back to previous settings\n")
set_MAC(wmi_adapter, original_state["MACAddress"])
set_adapter_state(wmi_adapter, 'disable')
set_adapter_state(wmi_adapter, 'enable')

