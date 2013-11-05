import core
import time

class NetStatusWatcher:
    def __init__(self, cb_set_status, iface):
        self.cb_set_status = cb_set_status
        self.iface = iface
        self.status = False

    def run(self):
        while True
            new_status = core.iface_has_commotion(self.iface)
            if (new_status != self.status) :
                self.cb_set_status(new_status)
                self.status = new_status
            time.sleep(1)
