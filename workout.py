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

WMI = wmi.WMI()

if sys.argv[-1] != ASADMIN:
    print 'You must run this script as an administrator'

# choose an adapter for Commotion
adapters = WMI.Win32_NetworkAdapter()
for idx, adapter in enumerate(adapters):
    print '#{1.Index:>2} {1.MACAddress:17} {1.Name}'.format(idx, adapter)
target_adapter = int(raw_input("Enter the # of the adapter you want to use for Commotion: "))

# TODO: Is adapters[target_adapter].Index guaranteed to equal target_adapter?
adapter = adapters[target_adapter]
print ' '.join(['Configuring', adapter.Name])

# disable adapter
def set_adapter_state(adapter=None, verb='enable'):
    if (adapter is not None) and (verb is not None):
        status = {
            'enable': adapter.Enable,
            'disable': adapter.Disable
        }[verb]()
        if status[0] != 0:
            print ''.join(['Couldn\'t ', verb, ' adapter (error:', str(status[0]), ')'])
        else:
            print ''.join(['Adapter ', verb, 'd'])
        return status
    else:
        return None

set_adapter_state(adapter, 'disable')

# change MAC of adapter_index to Commotion BSSID/MAC CC:CC:CC:CC:CC:CC
reg_adapter = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
        '\\'.join(['SYSTEM',
                    'CurrentControlSet',
                    'Control',
                    'Class',
                    '{4D36E972-E325-11CE-BFC1-08002BE10318}',
                    '{0:0>4}'.format(adapter.Index)
                ])
        )


# set adapter_index configuration to ad-hoc


# enable adapter_index
set_adapter_state(adapter, 'enable')

# show current info for adapter_index


# go back to old configuration when ready
holdup = ''
while holdup != '!':
    holdup = raw_input("Enter ! to go back to previous settings\n")

