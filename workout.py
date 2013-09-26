import os
import sys
import inspect
#import win32com.shell.shell as shell
import _winreg # http://docs.python.org/2.7/library/_winreg.html
import ctypes # http://docs.python.org/2.7/library/ctypes.html
import wmi # http://timgolden.me.uk/python/wmi/index.html
import subprocess # for netsh and olsrd

from ctypes import windll # loads libs exporting via stdcall
from ctypes import wintypes
from ctypes import cdll # loads libs exporting via cdecl

commotion_BSSID = '12:CA:FF:EE:BA:BE' # shows up in a few Commotion places
commotion_SSID = 'commotion-wireless.net'
commotion_profile_name = 'commotion-wireless.net'
commotion_profile_path = "commotion_wireless_profile.xml"

WMI = wmi.WMI()

# http://stackoverflow.com/questions/279237/import-a-module-from-a-folder
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(
		              inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

# Import from subdirectories. (__init__.py works in some envs, not others)
try:
    import WindowsWifi as PyWiWi
    import WindowsNativeWifiApi as PWWnw
except ImportError:
    print "Enumerating interfaces..." # sneaky indicator
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(
                    inspect.getfile(inspect.currentframe()
    ))[0], "PyWiWi")))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)
    import WindowsWifi as PyWiWi
    import WindowsNativeWifiApi as PWWnw

# collect existing networks on wireless interfaces
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

# get interface "common name" for netsh, etc.
wmi_ifaces = wmi.WMI().Win32_NetworkAdapter()
ifaces_by_guid = {}
for iface in wmi_ifaces:
    ifaces_by_guid[iface.GUID] = iface

def get_netsh_name(pywiwi_iface):
    return ifaces_by_guid[str(pywiwi_iface.guid)].NetConnectionID

def netsh_add_profile():
    subprocess.call("".join(["netsh wlan add profile",
                             " filename=\"",
                             commotion_profile_path,
                             "\""]))

def netsh_connect(netsh_name):
    subprocess.call("".join(["netsh wlan connect",
                             " name=\"",
                             commotion_profile_name,
                             "\" interface=\"",
                             netsh_name,
                             "\""]))

def start_olsrd(netsh_name):
    subprocess.call("".join(["olsrd.exe",
                             " -d 2",
                             " -i \"",
                             netsh_name,
                             "\" -f olsrd.conf"]))

def join_network(target_net):
    target_guid = str(target["interface"].guid)
    target_net["interface"].netsh_name = get_netsh_name(target_net["interface"])
    # TODO:

def make_network():
    # pick an interface to use
    print "#   Interface"
    idx = 0
    for iface in ifaces:
        print "".join(["{0:>2} ",
                       "{1.description}"]).format(idx+1, iface)
        idx = 1 + idx
    iface_choice = raw_input("Enter the # of the interface to use:\n")
    target_iface = ifaces[int(iface_choice)-1]
    target_iface.netsh_name = get_netsh_name(target_iface)
    # add a profile for commotion
    # if this profile already exists, it will not be added again
    netsh_add_profile()
    # connect to the network
    netsh_connect(target_iface.netsh_name)
    # start olsrd
    start_olsrd(target_iface.netsh_name)
    hold_and_finish(target_iface.netsh_name)

def hold_and_finish(netsh_name):
    # stay connected until done
    holdup = ''
    while holdup != '!':
        holdup = raw_input("Enter ! to disconnect\n")

    # disconnect from current network
    #PyWiWi.disconnect(target_net["interface"])
    subprocess.call("".join(["netsh wlan disconnect",
                             " interface=\"",
                             netsh_name,
                             "\""]))

    # show current info for adapter


    # go back to old configuration when ready
    delete_profile = raw_input("Delete Commotion Wireless profile? (Y|N)\n")
    if delete_profile == 'Y':
        subprocess.call("".join(["netsh wlan delete profile",
                                 " name=\"",
                                 commotion_profile_name,
                                 "\" interface=\"",
                                 netsh_name,
                                 "\""]))

#with open(commotion_profile_path, "r") as f_profile:
    #commotion_wlan_profile_xml = "".join(line.rstrip() for line in f_profile)

# choose desired network
net_list.sort(key=lambda opt: opt["network"].link_quality, reverse=True)
print "#   @ CW? Interface     Qual BSSID             SSID"
for idx, net in enumerate(net_list):
    temphandle = PWWnw.WlanOpenHandle()
    a = PyWiWi.WlanQueryInterface(temphandle,
                                                net["interface"].guid,
                                                PWWnw.WLAN_INTF_OPCODE(7))
    b = a.contents.wlanAssociationAttributes.dot11Bssid
    c = ":".join(map(lambda x: "%02X" % x, b))
    net["network"].isCurrent = str(c == net["network"].bssid)
    PWWnw.WlanCloseHandle(temphandle)
    print "".join(["{0:>2} ",
                   "{2.isCurrent:^3.3}",
                   "{3:^3.3} ",
                   "{1.description:13.13} ",
                   "{2.link_quality:>3}% ",
                   "{2.bssid} ",
                   "{2.ssid}"]).format(idx+1,
                                       net["interface"],
                                       net["network"],
                                       net["commotion"])
net_choice = raw_input("".join(["Enter the # of the network to join,\n",
                           "enter 0 (zero) to start a new network,\n",
                           "or enter Q to quit:\n"]))

print net_list[int(net_choice)-1]["interface"].initial_net
print "Selected interface is connected to ^"
exit()

# FIXME:
# TODO:
# Everybody always chooses 0, because not done
net_choice = 0
if net_choice > 0 and net_choice <= len(net_list):
    # join an existing network
    target_net = net_list[int(choice-1)]
    join_network(target_net)
elif net_choice == 0:
    make_network()
else:
    exit()
# connect to chosen network
# http://msdn.microsoft.com/en-us/library/windows/desktop/ms706851(v=vs.85).aspx
#cnxp = {"connectionMode": 0,
        #"profile": commotion_profile_path,
        ##"ssid": target_net["network"].ssid,
        #"ssid": None,
        #"bssidList": [target_net["network"].bssid],
        ## bssType must match type from profile provided
        #"bssType": target_net["network"].bss_type,
        #"flags": 0}
#PyWiWi.connect(target_net["interface"], cnxp)
