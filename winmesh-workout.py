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
profile_template_path = "profile_template.xml.py"
arbitrary_profile_path = "arbitrary_profile.xml"

WMI = wmi.WMI()

# http://stackoverflow.com/questions/279237/import-a-module-from-a-folder
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(
		              inspect.currentframe()))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

# Import from subdirectories. (__init__.py works in some envs, not others)
try:
    import PyWiWi.WindowsWifi as WindowsWifi
    import PyWiWi.WindowsNativeWifiApi as PWWnw
except ImportError:
    cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(
                    inspect.getfile(inspect.currentframe()
    ))[0], "PyWiWi")))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)
    import WindowsWifi as WindowsWifi
    import WindowsNativeWifiApi as PWWnw

def make_profile(path, params):
    def load_profile_template(path):
        with open(path, "r") as f_profile:
            profile_template = "".join(line.rstrip() for line in f_profile)
        return profile_template
    def write_profile_xml(path, profile):
        with open(path, "w") as f_profile:
            f_profile.write(profile)
    template = load_profile_template(profile_template_path)
    profile = template.format(**params)
    write_profile_xml(path, profile)

def get_current_net_bssid(PyWiWi_iface):
    def bssid_struct_to_string(dot11Bssid):
        return ":".join(map(lambda x: "%02X" % x, dot11Bssid))
    try:
        cnx = WindowsWifi.queryInterface(PyWiWi_iface, 'current_connection')
        bssid = bssid_struct_to_string(cnx.wlanAssociationAttributes.dot11Bssid)
    except:
        bssid = ""
    return bssid

def iface_has_commotion(PyWiWi_iface):
    return commotion_BSSID == get_current_net_bssid(PyWiWi_iface)

# collect existing networks on wireless interfaces
def collect_networks():
    ifaces = WindowsWifi.getWirelessInterfaces()
    # prepare to get each interface's "common name" for netsh
    wmi_ifaces = wmi.WMI().Win32_NetworkAdapter()
    ifaces_by_guid = {}
    for wmi_iface in wmi_ifaces:
        ifaces_by_guid[wmi_iface.GUID] = wmi_iface
    # collect networks and useful metadata
    nets = []
    for iface in ifaces:
        iface.initial_net = get_current_net_bssid(iface)
        iface.netsh_name = ifaces_by_guid[str(iface.guid)].NetConnectionID
        networks = WindowsWifi.getWirelessNetworkBssList(iface)
        for network in networks:
            nets.append({"interface": iface,
                         "network": network,
                         "commotion": network.bssid == commotion_BSSID})
    return nets

def netsh_add_profile(path):
    subprocess.call("".join(["netsh wlan add profile",
                             " filename=\"",
                             path,
                             "\""]))

def netsh_connect(netsh_spec):
    subprocess.call("".join(["netsh wlan connect",
                             " name=\"",
                             netsh_spec["profile_name"],
                             "\" interface=\"",
                             netsh_spec["iface_name"],
                             "\""]))

# FIXME needs to return a handle to the process
def start_olsrd(iface_name):
    subprocess.call("".join(["olsrd.exe",
                             " -d 2",
                             " -i \"",
                             iface_name,
                             "\" -f olsrd.conf"]))

def make_network(netsh_spec):
    # create a profile for this spec
    make_profile(arbitrary_profile_path, netsh_spec)
    # add a profile
    # if this profile already exists, it will not be added again
    netsh_add_profile(arbitrary_profile_path)
    # connect to the network
    netsh_connect(netsh_spec)
    # start olsrd
    start_olsrd(netsh_spec["iface_name"])
    hold_and_finish(netsh_spec["iface_name"])

def hold_and_finish(netsh_spec):
    # stay connected until done
    holdup = ''
    while holdup != '!':
        holdup = raw_input("Enter ! to disconnect\n")
    # disconnect from current network
    #WindowsWifi.disconnect(target_net["interface"])
    subprocess.call("".join(["netsh wlan disconnect",
                             " interface=\"",
                             netsh_spec["iface_name"],
                             "\""]))
    # show current info for adapter
    # go back to old configuration when ready
    delete_profile = raw_input("Delete this wireless profile? (Y|N)\n")
    if delete_profile == 'Y':
        subprocess.call("".join(["netsh wlan delete profile",
                                 " name=\"",
                                 netsh_spec["profile_name"],
                                 "\" interface=\"",
                                 netsh_spec["iface_name"],
                                 "\""]))

def print_available_networks():
    global net_list
    if net_list is None: refresh_net_list()
    #net_list.sort(key=lambda opt: opt["network"].link_quality, reverse=True)
    print "#   @ CW? Interface     Qual BSSID             SSID"
    for idx, net in enumerate(net_list):
        isCurrent = net["interface"].initial_net == net["network"].bssid
        print "".join(["{0:>2} ",
                       "{4:^3.1}",
                       "{3:^3.3} ",
                       "{1.description:13.13} ",
                       "{2.link_quality:>3}% ",
                       "{2.bssid} ",
                       "{2.ssid}"]).format(idx+1,
                                           net["interface"],
                                           net["network"],
                                           str(net["commotion"]),
                                           str(isCurrent))

def cli_choose_network():
    print_available_networks()
    return int(raw_input("".join(["Enter the # of the network to join,\n",
                               "enter 0 (zero) to start a new network,\n",
                               "or enter Q to quit:\n"])))

def make_netsh_spec(iface, ssid):
    return {"profile_name": ssid,
            "ssid_hex": ssid.encode('hex').upper(),
            "ssid_name": ssid,
            "iface_name": iface.netsh_name}

def cli_choose_iface(ifaces):
    print "#   Interface"
    idx = 0
    for iface in ifaces:
        print "".join(["{0:>2} ",
                       "{1.description}"]).format(idx+1, iface)
        idx = 1 + idx
    iface_choice = raw_input("Enter the # of the interface to use:\n")
    return ifaces[int(iface_choice)-1]

net_list = None
def refresh_net_list():
    global net_list
    net_list = collect_networks()
    net_list.sort(key=lambda opt: opt["network"].link_quality, reverse=True)

def get_ssid_from_net_list(idx):
    global net_list
    if net_list is None: refresh_net_list()
    return net_list[idx]["network"]["SSID"]

if __name__=="__main__":
    refresh_net_list()
    net_choice = cli_choose_network()
    if net_choice > 0 and net_choice <= len(net_list):
        # join an existing network
        target_net = net_list[net_choice-1]
        netsh_spec = make_netsh_spec(target_net["interface"],
                                     target_net["network"].ssid)
        make_network(netsh_spec)
    elif net_choice == 0:
        # start pseudo-commotion network (bad bssid)
        target_iface = cli_choose_iface(ifaces)
        netsh_spec = make_netsh_spec(target_iface, commotion_SSID)
        make_network(netsh_spec)
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
#WindowsWifi.connect(target_net["interface"], cnxp)
