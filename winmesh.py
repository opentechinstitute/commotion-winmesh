#!/usr/bin/env python

import gobject
import glib
import pygtk
pygtk.require('2.0')
import gtk
import workout
import threading
import sys
import time
import strings
import urllib
import traceback
from commotion import *

class OlsrdThread(threading.Thread):
    def __init__(self, olsrd_proc):
        threading.Thread.__init__(self)
        self.olsrd_proc = olsrd_proc
        print "OlsrdThread olsrd_proc is", self.olsrd_proc
        self.stop = False
        self.i = 0

    def run(self):
        while True:
            exitcode = self.olsrd_proc.poll()
            if exitcode != None:
                self.stop = True  #TODO: right now this is redundant
                print "olsrd exited with code", exitcode
            else:
                if self.i % 10 == 0:
                    self.get_json_info()
                    print "next JSONInfo refresh in 10 seconds..."
                self.i += 1
            if self.stop: 
                print "time to stop olsrd watch thread..."
                self.olsrd_proc.terminate()
                break
            time.sleep(1)

    def get_json_info(self):
        try: 
            url = "http://localhost:9090/"
            f = urllib.urlopen(url)
            print f.read()
        except:
            traceback.print_exc()

class ConsoleOutput:  
    def __init__(self, source, console):
        self.source=source
        self.buf = []
        self.c = console

    def update_buffer(self):
        self.c.textbuffer.insert(self.c.textbuffer.get_end_iter(), ''.join(self.buf))
        self.c.textview.scroll_mark_onscreen(self.c.textbuffer.get_insert())
        self.buf = []

    def write(self, data):
        self.buf.append(data)
        if data.endswith('\n'):
            gobject.idle_add(self.update_buffer)

    def __del__(self):
        if self.buf != []:
            gobject.idle_add(self.update_buffer)

# FIXME move to workout.py
def get_netsh_name(network_idx):
    return workout.net_list[network_idx]["interface"].netsh_name

class WinMeshUI:

    def __init__(self, portinghacks=None):
        self.portinghacks = portinghacks
        imgdir = 'external/commotion-mesh-applet/'
        self.mesh_status = MeshStatus(self.portinghacks, imagedir=imgdir)

        self.init_ui()

    def main(self):
        gtk.gdk.threads_init()
        gtk.main()

    def toggle_start(self, button, textview):
        if button.get_active():
            button.set_label(strings.TOGGLE_TEXT_STOP)
            network_idx = int(self.entryNetworkId.get_text()) # FIXME scrub input
            self.target_net = workout.net_list[network_idx-1]

            self.olsrd_proc = workout.connect_or_start_network(network_idx)
            print "WinMesh olsrd_proc is", self.olsrd_proc

            #bssid = workout.get_ssid_from_net_list(network_idx-1)
            #print "selected network bssid: %s, starting olsrd on interface: '%s'" % (bssid, netsh_name)

#            self.olsr_proc = workout.start_olsrd(get_netsh_name(network_idx))

            #glib.io_add_watch(self.olsr_proc.stdout, # FILE DESCRIPTOR
            #                  glib.IO_IN,  # CONDITION
            #                  self.write_to_buffer ) # CALLBACK

            # TODO start olsrd process watchdog thread
            # TODO start olsrd.jsoninfo plugin poller thread
            self.olsrd_thread = OlsrdThread(self.olsrd_proc)
            self.olsrd_thread.setDaemon(True)
            self.olsrd_thread.start()
        else:
            button.set_label(strings.TOGGLE_TEXT_START)
            self.shutdown()

    def kill_olsrd(self):
        try: 
            self.olsrd_proc.terminate()
        except:
            pass

        try: 
            self.olsrd_thread.stop = True
        except: 
            pass

    def write_to_buffer(self, fd, condition):
        if condition == glib.IO_IN: #IF THERE'S SOMETHING INTERESTING TO READ
            char = fd.read(1) # WE READ ONE BYTE PER TIME, TO AVOID BLOCKING
            print char           
            #buf = self.get_buffer()
            #buf.insert_at_cursor(char) # WHEN RUNNING DON'T TOUCH THE TEXTVIEW!!
            return True # FUNDAMENTAL, OTHERWISE THE CALLBACK ISN'T RECALLED
        else:
            return False # RAISED AN ERROR: EXIT AND I DON'T WANT TO SEE YOU ANYMORE


    def shutdown(self):
        self.kill_olsrd()
        workout.restore_previous_profile()
        #workout.shutdown_and_cleanup_network_gui()

    def close_application(self, widget):
        self.shutdown()
        gtk.main_quit()

    def show_mesh_status(self, widget):
        self.mesh_status.show()

    def print_directions(self):
        print "\n\nTo join a network enter it's number below.  To create a network, enter 0 below."

    def probe_network(self):
        #self.net_list = workout.collect_networks()
        workout.print_available_networks()

    def init_ui(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request (750, 550)
        window.set_resizable(True)  
        window.connect("destroy", self.close_application)
        window.set_title("Commotion Wireless for Windows (prototype 1)")
        window.set_border_width(0)

        box1 = gtk.VBox(False, 0)
        window.add(box1)
        box1.show()

        box2 = gtk.VBox(False, 10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textview = gtk.TextView()
        self.textview.set_sensitive(False)
        self.textbuffer = self.textview.get_buffer()
        sw.add(self.textview)
        sw.show()
        self.textview.show()

        box2.pack_start(sw)

        string = "Available networks:\n\n"
        self.textbuffer.set_text(string)

        hbox = gtk.HButtonBox()
        box2.pack_start(hbox, False, False, 0)
        hbox.show()

        vbox = gtk.VBox()
        vbox.show()
        hbox.pack_start(vbox, False, False, 0)

        # check button to start up commotion
        check = gtk.ToggleButton(strings.TOGGLE_TEXT_START)
        vbox.pack_start(check, False, False, 0)
        check.connect("toggled", self.toggle_start, self.textview)
        check.set_active(False)
        check.show()

        self.entryNetworkId = gtk.Entry(max=2)
        vbox.pack_start(self.entryNetworkId, False, False, 0)
        self.entryNetworkId.set_text("0")
        self.entryNetworkId.show()


        separator = gtk.HSeparator()
        box1.pack_start(separator, False, True, 0)
        separator.show()

        box2 = gtk.VBox(False, 10)
        box2.set_border_width(10)
        box1.pack_start(box2, False, True, 0)
        box2.show()

        button = gtk.Button("close")
        button.connect("clicked", self.close_application)
        box2.pack_start(button, True, True, 0)
        button.set_flags(gtk.CAN_DEFAULT)
        button.grab_default()
        button.show()
        
        button = gtk.Button("mesh status")
        button.connect("clicked", self.show_mesh_status)
        box2.pack_start(button, True, True, 0)
        button.show()

        window.show()

def get_portinghacks():
    port = PortingHacks()
    port.BUTTONS_CLOSE = gtk.BUTTONS_CLOSE
    port.FILE_CHOOSER_ACTION_SAVE = gtk.FILE_CHOOSER_ACTION_SAVE
    port.MESSAGE_ERROR = gtk.MESSAGE_ERROR
    port.MESSAGE_OTHER = gtk.MESSAGE_OTHER
    port.RESPONSE_CANCEL = gtk.RESPONSE_CANCEL
    port.RESPONSE_OK = gtk.RESPONSE_OK
    port.DIALOG_DESTROY_WITH_PARENT = gtk.DIALOG_DESTROY_WITH_PARENT
    port.SELECTION_NONE = gtk.SELECTION_NONE
    port.STOCK_ABOUT = gtk.STOCK_ABOUT
    port.pixbuf_new_from_file = gtk.gdk.pixbuf_new_from_file
    return port

if __name__ == "__main__":
    app = WinMeshUI(get_portinghacks())
    co = ConsoleOutput(None, app)
    sys.stdout = co
    sys.stderr = co
    #t = WorkoutThread()
    #t.setDaemon(True)
    #t.start()
    app.probe_network()
    app.print_directions()
    app.main()
    #t.stop()

