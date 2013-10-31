import os
import pyjavaproperties
import workout
import socket
import re
from commotion_applet_support import JsonInfo, MeshStatus, PortingHacks
from commotionc import CommotionCore

def overrides(interface_class):
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider

class WindowsCommotionCore(CommotionCore):
# http://stackoverflow.com/questions/1167617/in-python-how-do-i-indicate-im-overriding-a-method

    def __init__(self, src='commotionc',
            olsrdconf='/etc/olsrd/olsrd.conf',
            olsrdpath='/usr/sbin/olsrd',
            profiledir='/etc/commotion/profiles.d/'):

        CommotionCore.__init__(self, src, olsrdconf, olsrdpath, profiledir)

        # override selectInterface
        self.selectedInterface = None;
        self.selectInterface = self._selectInterface
        self._generate_ip = self.__generate_ip


    def _selectInterface(self, iface=None):
        if iface:
            self.selectedInterface = iface
        else:
            if not self.selectedInterface:
                self.selectedInterface = workout.iface_list[0]
        return self.selectedInterface

    def __generate_ip(self, ip, netmask, mac):
        # adapted from commotion-linux-py/commotionc.py
        netmaskaddr = socket.inet_aton(netmask)
        baseaddr = socket.inet_aton(ip)
        hwaddr = "".join([mac[12], mac[13], mac[15], mac[16]])
        finaladdr = []
        for i in range(4):
            finaladdr.append((ord(hwaddr[i]) & ~ord(netmaskaddr[i])) |
                    (ord(baseaddr[i]) & ord(netmaskaddr[i])))
        return socket.inet_ntoa("".join([chr(item) for item in finaladdr]))


    def readProfile(self, profname):
        f = os.path.join(self.profiledir, profname + '.profile')
        p = pyjavaproperties.Properties()
        p.load(open(f))
        profile = dict()
        profile['filename'] = f
        profile['mtime'] = os.path.getmtime(f)
        for k,v in p.items():
            profile[k] = v
        for param in ('ssid', 'channel', 'ip', 'netmask', 'dns', 'ipgenerate'):
            ##Also validate ip, dns, bssid, channel?
            if param not in profile:
                self.log('Error in ' + f + ': missing or malformed ' +
                        param + ' option') ## And raise some sort of error?
        if profile['ipgenerate'] in ('True', 'true', 'Yes', 'yes', '1'):
            # and not profile['randomip']
            self.log('Generating static ip with base ' +
                    profile['ip'] + ' and subnet ' + profile['netmask'])
            # If this profile is detected on an interface, use that interface;
            #   otherwise use the default.
            # FIXME we should try to not mix network code into the file loader code
            matched_nets = workout.find_matching_available_nets(profile["ssid"],
                                                                profile["bssid"])
            if len(matched_nets) > 0:
                #FIXME: This is a bug in a multi-interface environment
                mac = workout.nets_dict[matched_nets[0]]["interface"].MAC
            else:
                mac = self.selectInterface().MAC
            profile['ip'] = self._generate_ip(profile['ip'],
                                              profile['netmask'],
                                              mac)
            self.updateProfile(profname, {'ipgenerate': 'false',
                                          'ip': profile['ip']})
        if not 'bssid' in profile:
            # Include note in default config file that bssid parameter is allowed,
            #   but should almost never be used
            self.log('Generating BSSID from hash of ssid and channel')
            bssid = hashlib.new('md4', ssid).hexdigest()[-8:].upper() \
                    + '%02X' %int(profile['channel']) #or 'md5', [:8]
            profile['bssid'] = ':'.join(a+b for a,b in zip(bssid[::2], bssid[1::2]))
        conf = re.sub('(.*)\.profile', r'\1.conf', f) #TODO: this is now wrong
        if os.path.exists(conf):
            self.log('profile has custom olsrd.conf: "' + conf + '"')
            profile['conf'] = conf
        else:
            self.log('using built in olsrd.conf: "' + self.olsrdconf + '"')
            profile['conf'] = self.olsrdconf
        return profile


#    @overrides(CommotionCore)
#    def selectInterface(self, preferred=None):
#         print "monkeypatch overridden method in base class, amazeballs" 

all = ['JsonInfo', 'MeshStatus', 'PortingHacks', 'WindowsCommotionCore']
