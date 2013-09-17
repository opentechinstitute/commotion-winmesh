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

commotion_BSSID = '12CAFFEEBABE' # shows up in a few Commotion places
commotion_SSID = 'commotion-wireless.net'

WMI = wmi.WMI()

print 'You must run this script as an administrator'

# choose an adapter
adapters = WMI.Win32_NetworkAdapter()
for idx, adapter in enumerate(adapters):
    print '#{1.Index:>2} {1.MACAddress:17} {1.Name}'.format(idx, adapter)
target_adapter = int(raw_input("Enter the # of the adapter you want to use for Commotion: "))
wmi_adapter = adapters[target_adapter]
print ' '.join(['Configuring', wmi_adapter.Name])

original_state = {"MACAddress": wmi_adapter.MACAddress,
                  "SSID": "",
                  "BSSID": "",
                  "enabled": wmi_adapter.NetEnabled}

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
#set_adapter_state(wmi_adapter, 'disable')
#set_adapter_state(wmi_adapter, 'enable')

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

