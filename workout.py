import os
import io
import sys
import re
import inspect
import pickle
#import win32com.shell.shell as shell
import _winreg  # http://docs.python.org/2.7/library/_winreg.html
#import ctypes  # http://docs.python.org/2.7/library/ctypes.html
import wmi  # http://timgolden.me.uk/python/wmi/index.html
import subprocess  # for netsh and olsrd

#from ctypes import windll  # loads libs exporting via stdcall
#from ctypes import wintypes
#from ctypes import cdll  # loads libs exporting via cdecl

commotion_BSSID_re = re.compile(r'[01]2:CA:FF:EE:BA:BE')
commotion_SSID = 'commotion-wireless.net'
commotion_profile_name = 'commotion-wireless.net'

WMI = wmi.WMI()

def get_own_path(extends_with=None):
    if extends_with:
        sep = "/"
    else:
        sep = ""
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    ext_path = os.path.abspath("".join([base_path,
                                    sep,
                                    extends_with]))
    return ext_path

commotion_profile_path = get_own_path("commotion_wireless_profile.xml")
profile_template_path = get_own_path("profile_template.xml.py")
arbitrary_profile_path = get_own_path("arbitrary_profile.xml")
netsh_add_connect_template_path = get_own_path("netsh_add_connect.bat.py")
netsh_batch_path = get_own_path("netsh_add_connect.bat")
prev_profile_path = get_own_path(".prevprofile")
netsh_export_path = get_own_path(".prevnet.xml")
olsrd_path = get_own_path("olsrd.exe")
olsrd_conf_path = get_own_path("olsrd.conf")

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
    cmd_subfolder = os.path.realpath(
        os.path.abspath(os.path.join(os.path.split(
            inspect.getfile(inspect.currentframe()
            ))[0], "PyWiWi")))
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)
    import PyWiWi.WindowsWifi as WindowsWifi
    import PyWiWi.WindowsNativeWifiApi as PWWnw


def create_file_from_template(template_path, result_path, params):
    def load_template(template_path):
        with io.open(template_path, mode="rt", newline="\r\n") as f:
            return "".join(line.rstrip() for line in f)

    def write_file(result_path, filestring):
        with io.open(result_path, mode="w", newline="\r\n") as f:
            f.write(unicode(filestring))

    template = load_template(template_path)
    write_file(result_path, template.format(**params))


def make_profile(params):
    create_file_from_template(profile_template_path,
                              "".join([params["profile_name"], ".xml"]),
                              params)


def netsh_add_and_connect(netsh_spec):
    create_file_from_template(netsh_add_connect_template_path,
                              netsh_batch_path,
                              netsh_spec)
    # run the batch file
    netbat = subprocess.Popen(netsh_batch_path)
    return netbat #.wait()


def wlan_dot11bssid_to_string(dot11Bssid):
    return ":".join(map(lambda x: "%02X" % x, dot11Bssid))


def get_wlan_current_connection(PyWiWi_iface):
    ''' Returns connection attributes if connected, None if not. '''
    #TODO: The right way to do this is to query interface_state first.
    try:
        cnx = WindowsWifi.queryInterface(PyWiWi_iface, 'current_connection')
    except:
        cnx = None
    return cnx


def get_current_connection(PyWiWi_iface):
    ''' Returns digested connection attributes if connected, None if not. '''
    cnx = get_wlan_current_connection(PyWiWi_iface)
    if cnx:
        assn_attrs = cnx.wlanAssociationAttributes
        result = {'profile_name': cnx.strProfileName,
                  'bssid': wlan_dot11bssid_to_string(assn_attrs.dot11Bssid)}
    else:
        result = cnx
    return result


def get_current_net_bssid(PyWiWi_iface):
    cnx = get_current_connection(PyWiWi_iface)
    if cnx:
        bssid = cnx["bssid"]
    else:
        bssid = None
    return bssid


def bssid_is_commotion(bssid):
    #NOTE: This is not fault tolerant.
    match = commotion_BSSID_re.match(bssid)
    return match != None


def iface_has_commotion(PyWiWi_iface):
    return bssid_is_commotion(get_current_net_bssid(PyWiWi_iface))


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
        iface.initial_bssid = get_current_net_bssid(iface)
        iface.initial_connection = get_current_connection(iface)
        iface.netsh_name = ifaces_by_guid[str(iface.guid)].NetConnectionID
        networks = WindowsWifi.getWirelessNetworkBssList(iface)
        for network in networks:
            nets.append({"interface": iface,
                         "network": network,
                         "commotion": bssid_is_commotion(network.bssid)})
    return nets, ifaces


def netsh_add_profile_cmd(path):
    return "".join(["netsh wlan add profile",
                    " filename=\"",
                    path,
                    "\""])


# FIXME do we need to capture stderr?
def netsh_add_profile(path):
    add = subprocess.call(netsh_add_profile_cmd(path))
    return add.wait()


def netsh_connect_cmd(netsh_spec):
    return "".join(["netsh wlan connect",
                    " name=\"",
                    netsh_spec["profile_name"],
                    "\" interface=\"",
                    netsh_spec["iface_name"],
                    "\""])


# FIXME do we need to capture stderr?
def netsh_connect(netsh_spec):
    conn = subprocess.call(netsh_connect_cmd(netsh_spec))
    return conn.wait()


def netsh_export_profile_cmd(path, profile_name, iface_name):
    return "".join(["netsh wlan export profile",
                    " folder=\"",
                    path,
                    "\"",
                    " name=\"",
                    profile_name,
                    "\"",
                    " interface=\"",
                    iface_name,
                    "\""])


def netsh_export_profile(profile_name, iface_name):
    netsh = subprocess.call(netsh_export_profile_cmd(netsh_export_path,
                                                     profile_name,
                                                     iface_name))
    return netsh.wait()


def save_current_profile(iface):
    cnx = get_current_connection(iface)
    fname = prev_profile_path
    if cnx:
        connectable = {"profile_name": cnx["profile_name"],
                       "iface_name": iface.netsh_name}
        pickle.dump(connectable, open(fname, "w"))
        print "saved at", fname
    else:
        #remove any existing profile to avoid unforeseen problems
        if os.path.isfile(fname):
            os.remove(fname)

def netsh_export_current_profile(iface):
    cnx = get_current_connection(iface)
    netsh_export_profile(cnx.profile_name, iface.netsh_name)


def start_olsrd_cmd(iface_name):
    print "olsrd_path", olsrd_path
    return "".join([olsrd_path,
                    #" -d 2",
                    " -i \"",
                    iface_name,
                    "\"",
                    " -f \"",
                    olsrd_conf_path,
                    "\""])


# FIXME needs to return a handle to the process
def start_olsrd(iface_name):
    olsrd = subprocess.Popen(start_olsrd_cmd(iface_name),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    return olsrd

def make_network(netsh_spec):
    make_profile(netsh_spec)
    netsh_add_and_connect(netsh_spec) # no longer starts olsrd
    olsrd = start_olsrd(netsh_spec["iface_name"])
    return olsrd


def holdup():
    # stay connected until done
    holdup = ''
    while holdup != '!':
        holdup = raw_input("Enter ! to disconnect\n")


def shutdown_and_cleanup_network_cmd(netsh_spec):
    return "".join(["netsh wlan disconnect",
                    " interface=\"",
                    netsh_spec["iface_name"],
                    "\""])


def shutdown_and_cleanup_network_cmd2(netsh_spec):
    return "".join(["netsh wlan delete profile",
                    " name=\"",
                    netsh_spec["profile_name"],
                    "\" interface=\"",
                    netsh_spec["iface_name"],
                    "\""])


def restore_previous_profile():
    fname = prev_profile_path
    if os.path.isfile(fname):
        try:
            connectable = pickle.load(open(fname, "r"))
            netsh_connect(connectable)
            print "restored from", fname
        except:
            #raise Exception(
                    #"""Profile restore file exists but restore failed.""")
            print "Profile restore file exists but restore failed."


def shutdown_and_cleanup_network(netsh_spec):
    # disconnect from current network
    #WindowsWifi.disconnect(target_net["interface"])
    sd = subprocess.call(shutdown_and_cleanup_network_cmd(netsh_spec))
    sd.wait()

    # show current info for adapter
    # go back to old configuration when ready
    sd2 = subprocess.call(shutdown_and_cleanup_network_cmd2(netsh_spec))
    sd2.wait()

    restore_previous_profile()

def shutdown_and_cleanup_network_gui():
    refresh_net_list()
    if idx > 0 and idx <= len(net_list):
        # join an existing network
        target_net = net_list[idx - 1]
        netsh_spec = make_netsh_spec(target_net["interface"],
                                     target_net["network"].ssid)
    shutdown_and_cleanup_network(netsh_spec["iface_name"])


def shutdown_and_cleanup_network_cli(netsh_spec):
    # disconnect from current network
    #WindowsWifi.disconnect(target_net["interface"])
    sd = subprocess.call(shutdown_and_cleanup_network_cmd(netsh_spec))
    sd.wait()

    # show current info for adapter
    # go back to old configuration when ready
    delete_profile = raw_input("Delete this wireless profile? (Y|N)\n")
    if delete_profile == 'Y':
        sd2 = subprocess.call(shutdown_and_cleanup_network_cmd2(netsh_spec))
        sd2.wait()

    restore_previous_profile()


def print_available_networks():
    global net_list
    if net_list is None:
        refresh_net_list()
    #net_list.sort(key=lambda opt: opt["network"].link_quality, reverse=True)
    print "#   @ CW? Interface     Qual BSSID             SSID"
    for idx, net in enumerate(net_list):
        is_current = net["interface"].initial_bssid == net["network"].bssid
        print "".join(["{0:>2} ",
                       "{4:^3.1}",
                       "{3:^3.1} ",
                       "{1.description:13.13} ",
                       "{2.link_quality:>3}% ",
                       "{2.bssid} ",
                       "{2.ssid}"]).format(idx + 1,
                                           net["interface"],
                                           net["network"],
                                           str(net["commotion"]),
                                           str(is_current))


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
                       "{1.description}"]).format(idx + 1, iface)
        idx = 1 + idx
    iface_choice = raw_input("Enter the # of the interface to use:\n")
    return ifaces[int(iface_choice) - 1]


net_list = None


def refresh_net_list():
    global net_list
    global iface_list
    net_list, iface_list = collect_networks()
    net_list.sort(key=lambda opt: opt["network"].link_quality, reverse=True)


def get_ssid_from_net_list(idx):
    global net_list
    if net_list is None: refresh_net_list()
    return net_list[idx]["network"]["SSID"]


def connect_or_start_network(idx):
    #refresh_net_list()
    if idx > 0 and idx <= len(net_list):
        # join an existing network
        target_net = net_list[idx - 1]
        netsh_spec = make_netsh_spec(target_net["interface"],
                                     target_net["network"].ssid)
        save_current_profile(target_net["interface"])
    elif idx == 0:
        # start pseudo-commotion network (bad bssid)
        #ifaces = WindowsWifi.getWirelessInterfaces()
        target_iface = iface_list[0] #cli_choose_iface(ifaces)
        netsh_spec = make_netsh_spec(target_iface, commotion_SSID)
        save_current_profile(target_iface)
    olsrd = make_network(netsh_spec)
    return olsrd


if __name__ == "__main__":
    refresh_net_list()
    net_choice = cli_choose_network()
    if net_choice > 0 and net_choice <= len(net_list):
        # join an existing network
        target_net = net_list[net_choice - 1]
        netsh_spec = make_netsh_spec(target_net["interface"],
                                     target_net["network"].ssid)
        make_network(netsh_spec)
        holdup()  # pause waiting for the kill key
        shutdown_and_cleanup_network_cli(netsh_spec["iface_name"])
    elif net_choice == 0:
        # start pseudo-commotion network (bad bssid)

        # FIXME a bunch of code badly ripped from collect_networks()
        wmi_ifaces = wmi.WMI().Win32_NetworkAdapter()
        ifaces = WindowsWifi.getWirelessInterfaces()
        ifaces_by_guid = {}
        for wmi_iface in wmi_ifaces:
            ifaces_by_guid[wmi_iface.GUID] = wmi_iface

        for iface in ifaces:
            iface.initial_bssid = get_current_net_bssid(iface)
            iface.initial_connection = get_current_connection(iface)
            iface.netsh_name = ifaces_by_guid[str(iface.guid)].NetConnectionID
            # FIXME /a bunch of code badly ripped from collect_networks()

        target_iface = cli_choose_iface(ifaces)
        netsh_spec = make_netsh_spec(target_iface, commotion_SSID)
        make_network(netsh_spec)
    else:
        exit()

    # connect to chosen network
    # http://msdn.microsoft.com/en-us/library/windows/desktop/ms706851(v=vs
    # .85).aspx
    #cnxp = {"connectionMode": 0,
    #"profile": commotion_profile_path,
    ##"ssid": target_net["network"].ssid,
    #"ssid": None,
    #"bssidList": [target_net["network"].bssid],
    ## bssType must match type from profile provided
    #"bssType": target_net["network"].bss_type,
    #"flags": 0}
#WindowsWifi.connect(target_net["interface"], cnxp)
