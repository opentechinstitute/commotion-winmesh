#!/usr/bin/env python

# Commotion Winmesh was developed by Scal.io (http://scal.io) 
# with the generous support of Open Technology Institute
# (http://oti.newamerica.net/).
#
# Josh Steiner (https://github.com/vitriolix/)
# Jonathan Nelson (https://github.com/jnelson/)

import os
import sys
import pyjavaproperties
import core
import socket
import re
from external.commotion_linux_py import commotionc
# commotion-mesh-applet imports commotionc, so we need a reference
sys.modules['commotionc'] = sys.modules['external.commotion_linux_py']
from external.commotion_mesh_applet import commotion_applet_support
JsonInfo = commotion_applet_support.JsonInfo
MeshStatus = commotion_applet_support.MeshStatus
PortingHacks = commotion_applet_support.PortingHacks


def overrides(interface_class):
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider

class WindowsCommotionCore(commotionc.CommotionCore):
# http://stackoverflow.com/questions/1167617/in-python-how-do-i-indicate-im-overriding-a-method

    def __init__(self, src='commotionc',
            olsrdconf='/etc/olsrd/olsrd.conf',
            olsrdpath='/usr/sbin/olsrd',
            profiledir='/etc/commotion/profiles.d/'):

        commotionc.CommotionCore.__init__(self, src, olsrdconf, olsrdpath, profiledir)

        # override selectInterface
        self.selectedInterface = None;
        self.selectInterface = self._selectInterface
        self._generate_ip = self.__generate_ip


    def _selectInterface(self, iface=None):
        if iface:
            self.selectedInterface = iface
        else:
            if not self.selectedInterface:
                self.selectedInterface = core.iface_list[0]
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
            matched_nets = core.find_matching_available_nets(profile["ssid"],
                                                                profile["bssid"])
            if len(matched_nets) > 0:
                #FIXME: This is a bug in a multi-interface environment
                mac = core.nets_dict[matched_nets[0]]["interface"].MAC
            else:
                mac = self.selectInterface().MAC
            profile['ip'] = self._generate_ip(profile['ip'],
                                              profile['netmask'],
                                              mac)
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


all = ['JsonInfo', 'MeshStatus', 'PortingHacks', 'WindowsCommotionCore']
