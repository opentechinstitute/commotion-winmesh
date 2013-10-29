import os
import io
import sys
import socket
import re
import inspect
import pickle
import subprocess  # for netsh and olsrd
try:
    import wmi  # http://timgolden.me.uk/python/wmi/index.html
    from PyWiWi import WindowsWifi
    from PyWiWi import WindowsNativeWifiApi as PWWnw
    WMI = wmi.WMI()
except:
    pass


newline = "\r\n"

commotion_BSSID_re = re.compile(r'[01]2:CA:FF:EE:BA:BE')
commotion_default_SSID = 'commotionwireless.net'
commotion_default_netsh_spec = {
        "profile_name": commotion_default_SSID,
        "ssid_hex": commotion_default_SSID.encode('hex').upper(),
        "ssid": commotion_default_SSID,
        "iface_name": "",
        "bss_type": "IBSS",
        "auth": "WPA2PSK",
        "cipher": "AES"
        }
commotion_default_cnxp = {
        "connectionMode": "wlan_connection_mode_profile",
        "profile": None,  # will generate
        "ssid": commotion_default_SSID,
        "bssidList": ["02:CA:FF:EE:BA:BE"],
        #"bssidList": ["FF:FF:FF:FF:FF:FF"],  # wildcard
        "bssType": "dot11_BSS_type_infrastructure",
        "flags": 0
        }

profile_extension = ".xml"

dot11_to_wlan = {
        "dot11_BSS_type_infrastructure": "ESS",
        "dot11_BSS_type_independent": "IBSS",
        "DOT11_AUTH_ALGO_80211_OPEN": "open",
        "DOT11_AUTH_ALGO_80211_SHARED_KEY": "shared",
        "DOT11_AUTH_ALGO_WPA": "WPA",
        "DOT11_AUTH_ALGO_WPA_PSK": "WPAPSK",
        "DOT11_AUTH_ALGO_RSNA": "WPA2",
        "DOT11_AUTH_ALGO_RSNA_PSK": "WPA2PSK",
        "DOT11_CIPHER_ALGO_NONE": "none",
        "DOT11_CIPHER_ALGO_WEP40": "WEP",
        "DOT11_CIPHER_ALGO_WEP104": "WEP",
        "DOT11_CIPHER_ALGO_WEP": "WEP",
        "DOT11_CIPHER_ALGO_TKIP": "TKIP",
        "DOT11_CIPHER_ALGO_CCMP": "AES"
        }


def get_own_path(extends_with=None):
    if extends_with:
        sep = "/"
    else:
        extends_with = ""
        sep = ""
    base_path = os.path.dirname(os.path.abspath(inspect.getfile(
            inspect.currentframe())))
    ext_path = os.path.abspath("".join([base_path, sep, extends_with]))
    return ext_path

profile_template_path = get_own_path("profile_template.xml.py")
profile_key_template_path = get_own_path("sharedKey.xml.py")
prev_profile_path = get_own_path(".prevprofile")
netsh_export_path = get_own_path(".prevnet.xml")
olsrd_path = get_own_path("olsrd.exe")
olsrd_conf_path = get_own_path("olsrd.conf")


def write_file(path, filestring):
    with io.open(path, mode="w", newline=newline) as f:
        f.write(unicode(filestring))


def load_file(path):
    with io.open(path, mode="rt", newline=newline) as f:
        return "".join(line.rstrip() for line in f)


def apply_template(template_string, params):
    return template_string.format(**params)


def template_file_to_string(template_path, params):
    template = load_file(template_path)
    return apply_template(template, params)


def create_file_from_template(template_path, result_path, params):
    applied_template = template_file_to_string(template_path, params)
    write_file(result_path, applied_template)


def make_wlan_profile(netsh_spec):
    xml_path = get_own_path("".join([netsh_spec["profile_name"],
                                            profile_extension]))
    create_file_from_template(profile_template_path, xml_path, netsh_spec)
    return xml_path


def wlan_dot11bssid_to_string(dot11Bssid):
    return ":".join(map(lambda x: "%02X" % x, dot11Bssid))


def get_wlan_interface_state(PyWiWi_iface):
    s, S = WindowsWifi.queryInterface(PyWiWi_iface, 'interface_state')
    return s, S


def get_wlan_profile_xml(PyWiWi_iface, profile_name):
    return WindowsWifi.getWirelessProfileXML(PyWiWi_iface, profile_name)


def get_wlan_current_connection(PyWiWi_iface):
    ''' Returns connection attributes if connected, None if not. '''
    #try:
    iface_state = get_wlan_interface_state(PyWiWi_iface)[1]
    print "current iface state", iface_state
    if iface_state == "wlan_interface_state_connected":
        cnx, CNX = WindowsWifi.queryInterface(PyWiWi_iface,
                                              'current_connection')
    else:
        cnx, CNX = None, None
    #except:
        #cnx, CNX = None, None
    return cnx, CNX


def get_current_connection(PyWiWi_iface):
    ''' Returns digested connection attributes if connected, None if not. '''
    cnx, CNX = get_wlan_current_connection(PyWiWi_iface)
    if CNX:
        CNXaa = CNX["wlanAssociationAttributes"]
        result = {"profile_name": CNX["strProfileName"],
                  "bssid": CNXaa["dot11Bssid"],
                  "mode": CNX["wlanConnectionMode"],
                  "dot11_bss_type": CNXaa["dot11BssType"],
                  "phy_type": CNXaa["dot11PhyType"],
                  "ssid": CNXaa["dot11Ssid"]}
    else:
        result = CNX
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
    def is_commotion_in_bssList(bssList):
        for bss in bssList:
            if commotion_BSSID_re.match(bss.bssid):
                return True
        return False
    ifaces = WindowsWifi.getWirelessInterfaces()
    # prepare to get each interface's "common name" and MAC address
    wmi_ifaces = wmi.WMI().Win32_NetworkAdapter()
    ifaces_by_guid = {}
    for wmi_iface in wmi_ifaces:
        ifaces_by_guid[wmi_iface.GUID] = wmi_iface
    # collect networks and useful metadata
    nets = []
    nets_dict = {}
    for iface in ifaces:
        wmi_iface = ifaces_by_guid[iface.guid_string]
        wmi_iface_conf = wmi.WMI().Win32_NetworkAdapterConfiguration(
                InterfaceIndex=wmi_iface.InterfaceIndex)[0]
        print "wmi_iface", wmi_iface
        print "wmi_iface_conf", wmi_iface_conf
        iface.initial_bssid = get_current_net_bssid(iface)
        iface.initial_connection = get_current_connection(iface)
        iface.netsh_name = wmi_iface.NetConnectionID
        iface.MAC = wmi_iface.MACAddress
        iface.IPs = wmi_iface_conf.IPAddress
        iface.subnet_masks = wmi_iface_conf.IPSubnet
        iface.gateways = wmi_iface_conf.DefaultIPGateway
        iface.DHCP_enabled = wmi_iface_conf.DHCPEnabled
        # SSID<one-many>BSSID
        # WW.gWNBL gives BSSIDs with SSID each
        nets_bss = WindowsWifi.getWirelessNetworkBssList(iface)
        # WW.gWANL gives SSIDs with BSSID count and sec info
        nets_avail = WindowsWifi.getWirelessAvailableNetworkList(iface)
        # need SSID and sec info to construct profile
        # need SSID, profile, and preferred BSSIDs for WW.connect()
        for net_avail in nets_avail:
            net = {"interface": iface,
                   "auth": net_avail.auth,
                   "cipher": net_avail.cipher,
                   "bss_list": [],
                   "commotion": False}
            for bss in nets_bss:
                if bss.ssid == net_avail.ssid:
                    net["bss_list"].append(bss)
                    if not net["commotion"]:
                        # one commotion BSSID marks the SSID as commotion
                        net["commotion"] = bool(
                                commotion_BSSID_re.match(bss.bssid))
                    nets_dict[(iface.netsh_name, bss.ssid, bss.bssid)] = {
                            "interface": iface,
                            "ssid": bss.ssid,
                            "bssid": bss.bssid,
                            "dot11_bss_type": bss.bss_type,
                            "bss_type": dot11_to_wlan[bss.bss_type],
                            "auth": net_avail.auth,
                            "cipher": net_avail.cipher,
                            "quality": bss.link_quality
                            }
            nets.append(net)
    #nets = [net for net in nets if net["commotion"]]
    return nets, ifaces, nets_dict


def find_matching_available_nets(ssid, bssid):
    return [n for n in nets_dict if (n[1] == ssid and n[2] == bssid)]


def netsh_add_profile_cmd(path):
    return "".join(["netsh wlan add profile",
                    " filename=\"",
                    path,
                    profile_extension,
                    "\""])


def netsh_connect_cmd(netsh_spec):
    return "".join(["netsh wlan connect",
                    " name=\"",
                    netsh_spec["profile_name"],  # *not* full path, just name
                    "\" interface=\"",
                    netsh_spec["iface_name"],
                    "\""])


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


def netsh_disconnect_cmd(netsh_spec):
    return "".join(["netsh wlan disconnect",
                    " interface=\"",
                    netsh_spec["iface_name"],
                    "\""])


def netsh_add_profile(path):
    cmd =  netsh_add_profile_cmd(get_own_path(path))
    print cmd
    add = subprocess.Popen(cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    return add.wait()


def netsh_connect(netsh_spec):
    cmd = netsh_connect_cmd(netsh_spec)
    print cmd
    conn = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    return conn.wait()


def netsh_export_profile(profile_name, iface_name):
    netsh = subprocess.call(netsh_export_profile_cmd(netsh_export_path,
                                                     profile_name,
                                                     iface_name))
    return netsh.wait()


def start_olsrd(iface_name):
    olsrd = subprocess.Popen(start_olsrd_cmd(iface_name),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    return olsrd


def netsh_export_current_profile(iface):
    cnx = get_current_connection(iface)
    netsh_export_profile(cnx.profile_name, iface.netsh_name)


def save_rollback_params(iface, mesh_net):
    fname = prev_profile_path
    connectable = get_current_connection(iface)
    if connectable:
        connectable["interface"] = iface
        connectable["delete_mesh_after_restore"] = True
        if connectable["mode"] == "wlan_connection_mode_profile":
            connectable["restore"] = True
        elif connectable["mode"] == "wlan_connection_mode_temporary_profile":
            connectable["restore"] = True
        else:
            # "wlan_connection_mode_discovery_secure"
            # "wlan_connection_mode_discovery_unsecure"
            connectable["restore"] = False
    else:
        connectable = {
                "restore": False
                }
    connectable["mesh_wlan_name"] = mesh_net["ssid"]
    pickle.dump(connectable, open(fname, "w"))
    print "saved at", fname


def wlan_connect(spec):
    # PyWiWi.WindowsWifi.connect() only works reliably in profile mode.
    #   So we use that. We need it because the netsh wlan connect doesn't
    #   allow BSSID specification.
    cnxp = {"connectionMode": "wlan_connection_mode_profile",
            "profile": spec["profile_name"],
            "ssid": spec["ssid"],
            "bssidList": [spec["bssid"]],
            "bssType": spec["dot11_bss_type"],
            "flags": 0}
    print "about to connect", cnxp
    result = WindowsWifi.connect(spec["interface"], cnxp)


def make_network(netsh_spec):
    make_wlan_profile(netsh_spec)
    netsh_add_profile(netsh_spec["ssid"])
    netsh_connect(netsh_spec)
    olsrd = start_olsrd(netsh_spec["iface_name"])
    return olsrd


def make_network2(netsh_spec):
    make_wlan_profile(netsh_spec)
    netsh_add_profile(netsh_spec["ssid"])
    wlan_connect(netsh_spec)
    olsrd = start_olsrd(netsh_spec["interface"].netsh_name)
    return olsrd


def holdup():
    # stay connected until done
    holdup = ''
    while holdup != '!':
        holdup = raw_input("Enter ! to disconnect\n")


def netsh_delete_profile_cmd(wlan_profile_name, interface_name):
    return "".join(["netsh wlan delete profile",
                    " name=\"",
                    wlan_profile_name,
                    "\"",
                    " interface=\"",
                    interface_name,
                    "\""])

def netsh_delete_profile(wlan_profile_name, interface_name):
    p = subprocess.Popen(netsh_delete_profile_cmd(wlan_profile_name,
                                                  interface_name),
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    return p.wait()


def apply_rollback_params():
    fname = prev_profile_path
    if os.path.isfile(fname):
        try:
            connectable = pickle.load(open(fname, "r"))
            print "restoring", connectable
            if connectable["restore"]:
                wlan_connect(connectable)
                print "restored from", fname
            else:
                print "restore not requested"
        except:
            print "Profile restore file exists but restore failed."
    else:
        print "No restore file found"
    # delete wlan profile store entry for current mesh
    if "connectable" in locals():
        netsh_delete_profile(connectable["mesh_wlan_name"],
                             connectable["interface"].netsh_name)


def shutdown_and_cleanup_network(netsh_spec):
    # disconnect from current network
    #WindowsWifi.disconnect(target_net["interface"])
    sd = subprocess.call(netsh_disconnect_cmd(netsh_spec))
    sd.wait()

    # show current info for adapter
    # go back to old configuration when ready
    #sd2 = subprocess.call(netsh_delete_profile_cmd(netsh_spec))
    #sd2.wait()

    apply_rollback_params()

def shutdown_and_cleanup_network_gui():
    refresh_net_list()
    if idx > 0 and idx <= len(net_list):
        # join an existing network
        target_net = net_list[idx - 1]
        netsh_spec = make_netsh_spec(target_net)
    shutdown_and_cleanup_network(netsh_spec["iface_name"])


def shutdown_and_cleanup_network_cli(netsh_spec):
    # disconnect from current network
    #WindowsWifi.disconnect(target_net["interface"])
    sd = subprocess.call(netsh_disconnect_cmd(netsh_spec))
    sd.wait()

    # show current info for adapter
    # go back to old configuration when ready
    #delete_profile = raw_input("Delete this wireless profile? (Y|N)\n")
    #if delete_profile == 'Y':
        #sd2 = subprocess.call(netsh_delete_profile_cmd(netsh_spec))
        #sd2.wait()

    apply_rollback_params()


def print_available_networks():
    global net_list
    if net_list is None:
        refresh_net_list()
    print "#   @ CW? Interface     Qual BSSID             SSID"
    for idx, net in enumerate(net_list):
        is_current = net["interface"].initial_bssid == net["bss_list"][0].bssid
        print "".join(["{0:>2} ",
                       "{4:^3.1}",
                       "{3:^3.1} ",
                       "{1.description:13.13} ",
                       "{2.link_quality:>3}% ",
                       "{2.bssid} ",
                       "{2.ssid}"]).format(idx + 1,
                                           net["interface"],
                                           net["bss_list"][0],
                                           str(net["commotion"]),
                                           str(is_current))


def cli_choose_network():
    print_available_networks()
    return int(raw_input("".join(["Enter the # of the network to join,\n",
                                  "enter 0 (zero) to start a new network,\n",
                                  "or enter Q to quit:\n"])))


def make_netsh_spec(net):
    wlan = dot11_to_wlan
    netsh_spec = {
            "interface": net["interface"],
            "iface_name": net["interface"].netsh_name,
            "MAC": net["interface"].MAC,
            "profile_name": net["bss_list"][0].ssid,
            "ssid_hex": net["bss_list"][0].ssid.encode('hex').upper(),
            "ssid": net["bss_list"][0].ssid,
            "bssid": net["bss_list"][0].bssid,
            "dot11_bss_type": net["bss_list"][0].bss_type,
            "bss_type": wlan[net["bss_list"][0].bss_type],
            "auth": wlan[net["auth"]],
            "cipher": wlan[net["cipher"]],
            "key_material": net.get("key_material", None),
            "key_type": ("keyType" if \
                    wlan[net["auth"]] == "WEP" else "passPhrase")
            }
    if netsh_spec["key_material"] is not None:
        netsh_spec["shared_key"] = apply_template(profile_key_template_path,
                                                  netsh_spec)
    else:
        netsh_spec["shared_key"] = ""
    print "netsh_spec", netsh_spec
    return netsh_spec


def make_netsh_spec2(net):
    wlan = dot11_to_wlan
    netsh_spec = {
            "interface": net["interface"],
            "iface_name": net["interface"].netsh_name,
            "MAC": net["interface"].MAC,
            "profile_name": net["ssid"],
            "ssid_hex": net["ssid"].encode('hex').upper(),
            "ssid": net["ssid"],
            "bssid": net["bssid"],
            "dot11_bss_type": net["dot11_bss_type"],
            "bss_type": wlan[net["dot11_bss_type"]],
            "auth": wlan[net["auth"]],
            "cipher": wlan[net["cipher"]],
            "key_material": net.get("key_material", None),
            "key_type": ("keyType" if \
                    wlan[net["auth"]] == "WEP" else "passPhrase")
            }
    if netsh_spec["key_material"] is not None:
        netsh_spec["shared_key"] = template_file_to_string(
                profile_key_template_path,
                netsh_spec)
    else:
        netsh_spec["shared_key"] = ""
    print "netsh_spec", netsh_spec
    return netsh_spec


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
    global nets_dict
    net_list, iface_list, nets_dict = collect_networks()
    net_list.sort(key=lambda opt: opt["bss_list"][0].link_quality, reverse=True)


def get_ssid_from_net_list(idx):
    global net_list
    if net_list is None: refresh_net_list()
    return net_list[idx]["bss_list"][0]["SSID"]


def connect_or_start_mesh(idx):
    #refresh_net_list()
    if idx > 0 and idx <= len(net_list):
        # join an existing network
        target_net = net_list[idx - 1]
        save_rollback_params(target_net["interface"])
        netsh_spec = make_netsh_spec(target_net)
    elif idx == 0:
        # start pseudo-commotion network (bad bssid)
        #ifaces = WindowsWifi.getWirelessInterfaces()
        target_iface = iface_list[0] #cli_choose_iface(ifaces)
        save_rollback_params(target_iface)
        netsh_spec = commotion_default_netsh_spec
        netsh_spec["iface_name"] = target_iface.netsh_name
    olsrd = make_network(netsh_spec)
    return olsrd


def generate_ip(ip, netmask, interface):
    # adapted from commotion-linux-py/commotionc.py
    netmaskaddr = socket.inet_aton(netmask)
    baseaddr = socket.inet_aton(ip)
    m = interface.MAC
    hwaddr = "".join([m[12], m[13], m[15], m[16]])
    finaladdr = []
    for i in range(4):
        finaladdr.append((ord(hwaddr[i]) & ~ord(netmaskaddr[i])) |
                (ord(baseaddr[i]) & ord(netmaskaddr[i])))
    return socket.inet_ntoa("".join([chr(item) for item in finaladdr]))


def connect_or_start_profiled_mesh(profile):
    print "selected mesh", profile["ssid"]
    #FIXME: Until interface selection in UI, just use first available
    if len(profile["available_nets"]) > 0:
        print "connecting to existing mesh"
        print profile
        target_net = nets_dict[profile["available_nets"][0]]  # hack
        save_rollback_params(target_net["interface"], profile)
        target_net["key_material"] = profile["psk"]
        netsh_spec = make_netsh_spec2(target_net)
    else:
        print "creating new mesh"
        target_iface = iface_list[0]  # hack
        dummy_net = {
                "interface": target_iface,
                "profile_name": profile["ssid"],
                "ssid": profile["ssid"],
                "bssid": profile["bssid"],
                "dot11_bss_type": "dot11_BSS_type_independent",
                "bss_type": "IBSS",
                "auth": "DOT11_AUTH_ALGO_RSNA_PSK",  #WPA2PSK
                "cipher": "DOT11_CIPHER_ALGO_CCMP",  #AES
                "key_material": profile["psk"]
                }
        save_rollback_params(target_iface, dummy_net)
        netsh_spec = make_netsh_spec2(dummy_net)
        netsh_spec["iface_name"] = target_iface.netsh_name
    olsrd = make_network2(netsh_spec)
    return olsrd


if __name__ == "__main__":
    refresh_net_list()
    net_choice = cli_choose_network()
    if net_choice > 0 and net_choice <= len(net_list):
        # join an existing network
        target_net = net_list[net_choice - 1]
        netsh_spec = make_netsh_spec(target_net)
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
        netsh_spec = make_netsh_spec(target_net)
        make_network(netsh_spec)
    else:
        exit()


