import os
import sys
import win32com.shell.shell as shell
import _winreg # http://docs.python.org/2.7/library/_winreg.html?highlight=winreg#_winreg
import ctypes # http://docs.python.org/2.7/library/ctypes.html#module-ctypes
import wmi # http://timgolden.me.uk/python/wmi/index.html
#import argparse

from ctypes import windll # loads libs exporting via stdcall
from ctypes import wintypes
from ctypes import cdll # loads libs exporting via cdecl

ASADMIN = 'asadmin'
#commotion_BSSID = 'CCCCCCCCCCCC' # doesn't work
commotion_BSSID = 'C2CCCCCCCCCC' # works
""" Why '12CCCCCCCCCC' works (according to the Internets)
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

WMI = wmi.WMI()

if sys.argv[-1] != ASADMIN:
    print 'You must run this script as an administrator'

# choose an adapter for Commotion
adapters = WMI.Win32_NetworkAdapter()
for idx, adapter in enumerate(adapters):
    print '#{1.Index:>2} {1.MACAddress:17} {1.Name}'.format(idx, adapter)
target_adapter = int(raw_input("Enter the # of the adapter you want to use for Commotion: "))

# TODO: Is adapters[target_adapter].Index guaranteed to equal target_adapter?
wmi_adapter = adapters[target_adapter]
original_MAC = wmi_adapter.MACAddress
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

# Change MAC of adapter_index to Commotion BSSID/MAC
# The key we need to add (MAC) is named 'NetworkAddress'
def set_MAC(wmi_adapter, new_MAC=original_MAC):
	key = _winreg.HKEY_LOCAL_MACHINE
	subkey = '\\'.join(['SYSTEM',
						'CurrentControlSet',
						'Control',
						'Class',
						'{4D36E972-E325-11CE-BFC1-08002BE10318}',
						'{0:0>4}'.format(wmi_adapter.Index)
						])
	reg_adapter = _winreg.OpenKey(key, subkey, 0, _winreg.KEY_ALL_ACCESS)
	result = _winreg.SetValueEx(reg_adapter, 'NetworkAddress', 0, _winreg.REG_SZ, new_MAC)
	reg_adapter.Close() # not strictly necessary
	print result
	return result

set_MAC(wmi_adapter, commotion_BSSID)

# set adapter_index configuration to ad-hoc


# cycle adapter (use new settings)
set_adapter_state(wmi_adapter, 'disable')
set_adapter_state(wmi_adapter, 'enable')

# show current info for adapter_index


# go back to old configuration when ready
holdup = ''
while holdup != '!':
    holdup = raw_input("Enter ! to go back to previous settings\n")
set_MAC(wmi_adapter, original_MAC)
set_adapter_state(wmi_adapter, 'disable')
set_adapter_state(wmi_adapter, 'enable')

