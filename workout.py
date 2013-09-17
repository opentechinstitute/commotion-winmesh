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

print 'You must run this script as an administrator'

commotion_BSSID = '12CAFFEEBABE' # shows up in a few Commotion places
commotion_SSID = 'commotion-wireless.net'
ASADMIN = 'asadmin'

WMI = wmi.WMI()

# choose an adapter for Commotion
#adapters = WMI.Win32_NetworkAdapter()
#for idx, adapter in enumerate(adapters):
    #print '#{1.Index:>2} {1.MACAddress:17} {1.Name}'.format(idx, adapter)
#target_adapter = int(raw_input("Enter the # of the adapter you want to use for Commotion: "))

# TODO: Is adapters[target_adapter].Index guaranteed to equal target_adapter?
#wmi_adapter = adapters[target_adapter]

# preserve current settings - should write to non-volatile storage
#adapter_old = {"MACAddress": wmi_adapter.MACAddress,
                  #"enabled": wmi_adapter.NetEnabled}
#network_old = {"SSID": "",
               #"BSSID": ""}

#print ' '.join(['Configuring', wmi_adapter.Name])

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
#set_adapter_state(wmi_adapter, 'enable')

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
target_net = net_list[int(raw_input("Enter the # of the network to join or Q to exit: "))]

# disconnect from current network
#PyWiWi.disconnect(target_net["interface"])

# Change MAC of adapter_index to Commotion BSSID/MAC
# The key we need to add (MAC) is named 'NetworkAddress'
#def set_MAC(wmi_adapter, new_MAC=original_state["MACAddress"]):
    #key = _winreg.HKEY_LOCAL_MACHINE
    #subkey = '\\'.join(['SYSTEM',
                        #'CurrentControlSet',
                        #'Control',
                        #'Class',
                        #'{4D36E972-E325-11CE-BFC1-08002BE10318}',
                        #'{0:0>4}'.format(wmi_adapter.Index)
                        #])
    #reg_adapter = _winreg.OpenKey(key, subkey, 0, _winreg.KEY_ALL_ACCESS)
    #result = _winreg.SetValueEx(reg_adapter,
                                #'NetworkAddress',
                                #0,
                                #_winreg.REG_SZ, new_MAC)
    #reg_adapter.Close() # not strictly necessary
    #print "set_MAC result", result
    #return result

#set_MAC(wmi_adapter, commotion_BSSID)

# cycle adapter (use new settings)
#set_adapter_state(wmi_adapter, 'disable')
#set_adapter_state(wmi_adapter, 'enable')

# connect to chosen Commotion net
#PyWiWi.WlanConnect(hClientHandle, pInterfaceGuid, pConnectionParameters)

# show current info for adapter


# go back to old configuration when ready
holdup = ''
while holdup != '!':
    holdup = raw_input("Enter ! to go back to previous settings\n")
#set_MAC(wmi_adapter, original_state["MACAddress"])
#set_adapter_state(wmi_adapter, 'disable')
#set_adapter_state(wmi_adapter, 'enable')

