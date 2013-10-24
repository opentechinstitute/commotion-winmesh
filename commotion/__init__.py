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
        self.selectInterface = self._selectInterface
        self._generate_ip = self.__generate_ip
        
    def _selectInterface(self, preferred=None):
        return "FIXME NEED REAL INTERFACE NAME" # FIXME need to get real interface name here

    def  __generate_ip(self, ip, netmask, interface):
        return '1.2.3.4'
        # FIXME we need to kimplement this on windows
        #s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #hwiddata = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('32s', interface[:15]))
        #hwip = self._ip_string2int(socket.inet_ntoa(hwiddata[20:24]))
        #ipint = self._ip_string2int(ip)
        #netmaskint = self._ip_string2int(netmask)
        #return self._ip_int2string((hwip & ~netmaskint) + ipint)
    

#    @overrides(CommotionCore)
#    def selectInterface(self, preferred=None):
#         print "monkeypatch overridden method in base class, amazeballs" 

all = ['JsonInfo', 'MeshStatus', 'PortingHacks', 'WindowsCommotionCore']
