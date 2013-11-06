#!/usr/bin/env python

# Commotion Winmesh was developed by Scal.io (http://scal.io) 
# with the generous support of Open Technology Institute
# (http://oti.newamerica.net/).
#
# Josh Steiner (https://github.com/vitriolix/)
# Jonathan Nelson (https://github.com/jnelson/)

import gobject
import glib
import pygtk
pygtk.require('2.0')
import gtk
import core
import threading
import os
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

class WinMeshUI:
    def __init__(self, portinghacks=None):
        self.profiles = None
        self.selected_profile = None
        self.dirty = False
        self.portinghacks = portinghacks
        self.imagedir = 'external/commotion-mesh-applet/'
        self.mesh_status = MeshStatus(self.portinghacks, imagedir=self.imagedir)
        self.commotion = WindowsCommotionCore(
                profiledir="".join([core.get_own_path('/profiles/'), "/"]),
                #TODO: are these even needed?
                olsrdpath=core.olsrd_exe_path,
                olsrdconf=core.olsrd_conf_path
                )
        if not is_ui_test_mode(): core.refresh_net_list()
        self.profiles = self.read_profiles()
        self.init_ui()
        

    def main(self):
        gtk.gdk.threads_init()
        gtk.main()

    def toggle_start(self, button, textview):
        if button.get_active():
            if self.selected_profile is not None:
                button.set_label(strings.TOGGLE_TEXT_STOP)

                self.olsrd_proc = core.connect_or_start_profiled_mesh(
                        self.selected_profile)

                #glib.io_add_watch(self.olsr_proc.stdout, # FILE DESCRIPTOR
                #                  glib.IO_IN,  # CONDITION
                #                  self.write_to_buffer ) # CALLBACK

                self.olsrd_thread = OlsrdThread(self.olsrd_proc)
                self.olsrd_thread.setDaemon(True)
                #self.olsrd_thread.start()
        else:
            button.set_label(strings.TOGGLE_TEXT_START)
            self.shutdown()

    def _profile_selection_made(self, clist, row, col, event, data=None):
        text = clist.get_text(row, 1)  #FIXME: hard coded column for name
        print "profile selection made: %s" % text
        self.selected_profile = self.profiles[text]
        self.display_profile_in_editor(self.profiles[text])
        self.set_dirty_state(False)
        
    def profile_selection_made(self, clist, row, col, event, data=None):
        #if (self.dirty):
        #    print "WARN USER: you will lose changes if you click away"
        #    message = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
    	#    message.set_markup("You will lose changes if you click away.")
    	#    message.run()
        #    pass # FIXME warn the user they will lose changes
        # TODO how do i reset the selection to the previous if they cancel?
        #       probably we just have to call clist.select_row?
        #else:
            self._profile_selection_made(clist, row, col, event, data)
            
    def save_profile_clicked(self, button):
        # FIXME update profile object and call updateProfile in commotionc
        self.update_profile_from_editor(self.selected_profile)
        self.commotion.updateProfile(self.get_selected_profile_name(), self.selected_profile)
        self.set_dirty_state(False)

    def undo_changes_clicked(self, button):
        self.display_profile_in_editor(self.selected_profile)
        self.set_dirty_state(False)

    def display_profile_in_editor(self, profile):
        self.tbSSID.set_text(profile["ssid"])
        self.tbBSSID.set_text(profile["bssid"])
        self.tbChannel.set_text(profile["channel"])
        self.tbIP.set_text(profile["ip"])
        self.cbIPGenerate.set_active((profile["ipgenerate"] == "true"))
        self.tbNetmask.set_text(profile["netmask"])
        self.tbDNS.set_text(profile["dns"])

    def update_profile_from_editor(self, profile):
        profile["ssid"] = self.tbSSID.get_text()
        profile["bssid"] = self.tbBSSID.get_text()
        profile["channel"] = self.tbChannel.get_text()
        profile["ip"] = self.tbIP.get_text()
        profile["ipgenerate"] = "true" if self.cbIPGenerate.get_active() else "false"
        profile["netmask"] = self.tbNetmask.get_text()
        profile["dns"] = self.tbDNS.get_text()

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
        core.apply_rollback_params()
        #core.shutdown_and_cleanup_network_gui()

    def close_application(self, widget):
        self.shutdown()
        gtk.main_quit()

    def show_mesh_status(self, widget):
        self.mesh_status.show()

    def show_jsoninfo(self, widget):
        try: 
            url = "http://localhost:9090/"
            f = urllib.urlopen(url)
            print f.read()
        except:
            traceback.print_exc()

    # FIXME move this into the profile manager
    def clear_profiles(self):
        self.profiles = None

    def annotate_profiles(self, profiles):
        for k,v in profiles.iteritems():
            matches = core.find_matching_available_nets(v["ssid"], v["bssid"])
            if len(matches) > 0:
                v["available"] = True
            else:
                v["available"] = False
            v["available_nets"] = matches
        return profiles

    def read_profiles(self):
        profiles = self.commotion.readProfiles()
        profiles = self.annotate_profiles(profiles)
        return profiles

    def refresh_profiles(self):
        self.clear_profiles()
        self.profiles = self.read_profiles()
        
    def get_selected_profile_name(self):
        file_name = self.selected_profile['filename']
        profile_name = os.path.split(re.sub('\.profile$', '', file_name))[1]
        return profile_name

    def get_profile_names(self):
        if self.profiles is None:
            self.profiles = self.read_profiles()

        profile_names = []
        for k,v in self.profiles.iteritems():
            profile_names.append(k)
            #print "profile %s: %s" % (k, v)
        return profile_names


    def print_profiles(self):
        if self.profiles is None:
            self.profiles = self.read_profiles()

        for k,v in self.profiles.iteritems():
            print "profile %s: %s" % (k, v)

    def print_directions(self):
        print "\n\nTo join a network enter it's number below.  To create a network, enter 0 below."

    def changed(self, changedtext):
        self.set_dirty_state(True)

    def set_dirty_state(self, state):
        self.dirty = state
        self.update_buttons_state()

    def update_buttons_state(self):
        self.save_button.set_sensitive(self.dirty)
        self.undo_changes_button.set_sensitive(self.dirty)

    def init_ui(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request (750, 700)
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

        notebook = gtk.Notebook()
        notebook.set_tab_pos(gtk.POS_TOP)
        notebook.show_all()
        self.show_tabs = True
        self.show_border = True

        def add_page(notebook, title, image, page):
            label = gtk.Label(title)
            vbox = gtk.VBox(False, 0)
            vbox.set_size_request(60, 60)
            image.set_size_request(46, 46)
            vbox.pack_start(image, False, True, 0)
            vbox.pack_start(label, False, True, 0)
            label.show()
            vbox.show()
            notebook.append_page(page, vbox)

        self.textview = gtk.TextView()
        self.textview.set_sensitive(False)
        self.textbuffer = self.textview.get_buffer()
        self.textview.show()

        hbox = gtk.HBox(False, 10)
        
        # FIXME replace with TreeView: http://www.pygtk.org/pygtk2tutorial/ch-TreeViewWidget.html
        clist = gtk.CList(2)
        for k,v in self.profiles.iteritems():
            clist.append(["@" if v["available"] else "", k])
        clist.set_column_width(0, 10)
        clist.set_column_width(1, 190)
        clist.set_shadow_type(gtk.SHADOW_OUT)
        clist.connect("select_row", self.profile_selection_made)
        clist.show()
        hbox.pack_start(clist, expand=False, fill=False, padding=0)
        hbox.show()

        def get_profile_editor_controls():
            def add_item(b, l, t):
                l.set_alignment(0, 0)
                b.pack_start(l, expand=False, fill=False, padding=0)
                b.pack_start(t, expand=False, fill=False, padding=0)

            vbox = gtk.VBox(False, 10)

            label = gtk.Label("Mesh Netword Name (SSID):")
            self.tbSSID = gtk.Entry()
            self.tbSSID.connect("changed", self.changed)
            add_item(vbox, label, self.tbSSID)

            label = gtk.Label("BSSID:")
            self.tbBSSID = gtk.Entry()
            self.tbBSSID.connect("changed", self.changed)
            add_item(vbox, label, self.tbBSSID)

            label = gtk.Label("Channel:")
            self.tbChannel = gtk.Entry()
            self.tbChannel.connect("changed", self.changed)
            add_item(vbox, label, self.tbChannel)

            label = gtk.Label("IP:")
            self.tbIP = gtk.Entry()
            self.tbIP.connect("changed", self.changed)
            add_item(vbox, label, self.tbIP)

            label = gtk.Label("IPGenerate:")
            self.cbIPGenerate = gtk.CheckButton()
            self.cbIPGenerate.connect("toggled", self.changed)
            add_item(vbox, label, self.cbIPGenerate)

            label = gtk.Label("Netmask:")
            self.tbNetmask = gtk.Entry()
            self.tbNetmask.connect("changed", self.changed)
            add_item(vbox, label, self.tbNetmask)

            label = gtk.Label("DNS:")
            self.tbDNS = gtk.Entry()
            self.tbDNS.connect("changed", self.changed)
            add_item(vbox, label, self.tbDNS)
            
            hbox = gtk.HBox(False, 10)
            self.save_button = gtk.Button("Save Profile")
            self.save_button.set_sensitive(False)
            self.save_button.connect("clicked", self.save_profile_clicked)
            hbox.pack_start(self.save_button)

            self.undo_changes_button = gtk.Button("Undo Changes")
            self.undo_changes_button.set_sensitive(False)
            self.undo_changes_button.connect("clicked", self.undo_changes_clicked)
            hbox.pack_start(self.undo_changes_button)

            vbox.pack_end(hbox, expand=False, fill=False, padding=0)

            vbox.show_all()
            
            # load first profile        
            clist.select_row(0, 0)

            return vbox

        vbox_profile_controls = get_profile_editor_controls()
        hbox.pack_start(vbox_profile_controls, expand=True, fill=True, padding=10)
        hbox.show()

        TAB_IMAGE_WIDTH = 40
        TAB_IMAGE_HEIGHT = 40

        pixbuf = gtk.gdk.pixbuf_new_from_file(
                core.get_own_path(os.path.join('images', 'tabProfiles.png')))
        pixbuf = pixbuf.scale_simple(TAB_IMAGE_WIDTH, TAB_IMAGE_HEIGHT, gtk.gdk.INTERP_BILINEAR)
        image = gtk.image_new_from_pixbuf(pixbuf)
        image.show()
        
        add_page(notebook, "Profiles", image, hbox)

        pixbuf = gtk.gdk.pixbuf_new_from_file(
                core.get_own_path(os.path.join('images', 'tabLog.png')))
        pixbuf = pixbuf.scale_simple(TAB_IMAGE_WIDTH, TAB_IMAGE_HEIGHT, gtk.gdk.INTERP_BILINEAR)
        image = gtk.image_new_from_pixbuf(pixbuf)
        image.show()

        """
        vbox = gtk.VBox(False, 10)
        vbox.pack_start(self.textview, True, True, 0)
        button = gtk.Button("show jsoninfo")
        button.connect("clicked", self.show_jsoninfo)
        vbox.pack_start(button, True, True, 0)
        button.show()
        vbox.show()
        add_page(notebook, "Logs", image, vbox)
        """
        add_page(notebook, "Logs", image, self.textview)

        pixbuf = gtk.gdk.pixbuf_new_from_file(
                core.get_own_path(os.path.join('images', 'tabStatus.png')))
        pixbuf = pixbuf.scale_simple(TAB_IMAGE_WIDTH, TAB_IMAGE_HEIGHT, gtk.gdk.INTERP_BILINEAR)
        image = gtk.image_new_from_pixbuf(pixbuf)
        image.show()
        label = gtk.Label("Status goes here...")
        label.show()
        add_page(notebook, "Status", image, label)

        pixbuf = gtk.gdk.pixbuf_new_from_file(
                core.get_own_path(os.path.join('images', 'tabHelp.png')))
        pixbuf = pixbuf.scale_simple(TAB_IMAGE_WIDTH, TAB_IMAGE_HEIGHT, gtk.gdk.INTERP_BILINEAR)
        image = gtk.image_new_from_pixbuf(pixbuf)
        image.show()

        vbox = gtk.VBox(False, 10)

        logo_pixbuf = gtk.gdk.pixbuf_new_from_file(
                core.get_own_path(os.path.join('images', 'commotion_logo.png')))
        logo = gtk.image_new_from_pixbuf(logo_pixbuf)
        logo.show()
        vbox.pack_start(logo)

        blurb = gtk.Label("Commotion is an open-source communication tool that uses mobile phones, computers, and other wireless devices to create decentralized mesh networks.")
        blurb.set_line_wrap(True)
        blurb.show()
        vbox.pack_start(blurb)

        link = gtk.LinkButton("https://commotionwireless.net/", "commotionwireless.net") 
        link.show()
        vbox.pack_start(link)

        vbox.show()
            
        add_page(notebook, "About", image, vbox)

        vbox = gtk.VBox(False, 10)

        box2.pack_start(notebook)

        string = "\n"
        self.textbuffer.set_text(string)

        hbox = gtk.HButtonBox()
        box2.pack_start(hbox, False, False, 0)
        hbox.show()

        vbox = gtk.VBox()
        vbox.show()
        hbox.pack_start(vbox, expand=False, fill=False, padding=0)

        # check button to start up commotion
        check = gtk.ToggleButton(strings.TOGGLE_TEXT_START)
        vbox.pack_start(check, expand=False, fill=False, padding=0)
        check.connect("toggled", self.toggle_start, self.textview)
        check.set_active(False)
        check.show()

        separator = gtk.HSeparator()
        box1.pack_start(separator, False, True, 0)
        separator.show()

        box2 = gtk.HBox(False, 10)
        box2.set_border_width(10)
        box1.pack_start(box2, False, True, 0)
        box2.show()
        
        button = gtk.Button("show mesh status")
        button.connect("clicked", self.show_mesh_status)
        box2.pack_start(button, True, True, 0)
        button.show()
        
        button = gtk.Button("show jsoninfo")
        button.connect("clicked", self.show_jsoninfo)
        box2.pack_start(button, True, True, 0)
        button.show()

        button = gtk.Button("quit winmesh")
        button.connect("clicked", self.close_application)
        box2.pack_start(button, True, True, 0)
        button.set_flags(gtk.CAN_DEFAULT)
        button.grab_default()
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

def is_ui_test_mode():
    return len(sys.argv) > 1 and sys.argv[1] == 'testui'

if __name__ == "__main__":
    app = WinMeshUI(get_portinghacks())

    if not is_ui_test_mode():
        co = ConsoleOutput(None, app)
        sys.stdout = co
        sys.stderr = co

        core.refresh_net_list()

    # TODO cli mode
    #app.print_directions()
    #core.print_available_networks()

    app.main()
