from xcb.xproto import ConfigWindow as cw
import xcb.xproto as xproto
from xpybutil import ewmh, icccm, util, event

class Window:
    def __init__(self, window, conn, wm):
        #The XID for our window, our connection to the 
        #Xserver, and our reference to the Manager object
        self.win = window
        self.conn = conn
        self.wm = wm
        
        #these are set later, and I
        #haven't had a problem with it yet.
        self.x = 0
        self.y = 0
        self.w =0
        self.h = 0
        
        #do we have a strut?
        strut = self.get_wm_strut_partial()
        if strut:
            self.strut = strut
        else:
           self.strut = None
           
        #are we a fullscreen window ?
        net_state = self.get_net_wm_state()
        self.fullscreen = False
        if net_state and util.get_atom("_NET_WM_STATE_FULLSCREEN") in net_state:
            self.fullscreen = True
            
        #Define Default values for focus modals
        self.no_input = False
        self.passive = False
        self.local_active =False
        self.global_active = False
        
        
        #What is our focus modal?
        protos = self.get_wm_protocols()
        hints = self.get_wm_hints()
        input = False
        take_focus = False
        if hints and hints['input']:
            input = True
        if protos and util.get_atom("WM_TAKE_FOCUS") in protos:
            take_focus = True
        if input and take_focus:
            print self.get_wm_name()
            print "local_active"
            self.local_active = True
        elif input and not take_focus:
            print self.get_wm_name()
            print "passive"
            self.passive = True
        elif take_focus and not input:
            print self.get_wm_name()
            print "global_active"
            self.global_active = True
        else:
            print "no_input"
            self.no_input = True
        
        
    def get_wm_state(self):
        return icccm.get_wm_state(self.win).reply()
        
    def get_wm_hints(self):
        return icccm.get_wm_hints(self.win).reply()
    
    def get_wm_protocols(self):
        return icccm.get_wm_protocols(self.win).reply()
    
    def get_wm_name(self):
        return icccm.get_wm_name(self.win).reply()
        
    def get_wm_transient_for(self):
        return icccm.get_wm_transient_for(self.win).reply()
        
    def get_wm_strut_partial(self):
        try:
            strut = ewmh.get_wm_strut_partial(self.win).reply()
        except xproto.BadWindow:
            return None
        return strut
    
    def get_net_wm_state(self):
        return ewmh.get_wm_state(self.win).reply()
        
    def get_attributes(self):
        return self.conn.core.GetWindowAttributes(self.win).reply()
    
    def get_geometry(self):
        return self.conn.core.GetGeometry(self.win).reply()
    
    def configure(self, x, y, w, h, bw = 1):
        mask = cw.X | cw.Y |  cw.Width | cw.Height | cw.BorderWidth
        values = [x, y, w, h, bw]
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        return self.conn.core.ConfigureWindowChecked(self.win, mask, values)
    
    def map(self):
        icccm.set_wm_state(self.win, icccm.State.Normal, 0)
        self.conn.core.MapWindow(self.win)
    
    def unmap(self):
        self.conn.core.UnmapWindow(self.win)
        
    def focus(self):
        if self.passive :
            self.conn.core.SetInputFocus(xproto.InputFocus.PointerRoot, self.win)
        elif self.local_active:
            err = self.conn.core.SetInputFocusChecked(xproto.InputFocus.PointerRoot, self.win)
            err.check()
            packed = event.pack_client_message(self.win, "WM_PROTOCOLS", util.get_atom("WM_TAKE_FOCUS"), xproto.Time.CurrentTime)
            err = event.send_event_checked(self.win, 0,packed)
            err.check()
        elif self.global_active:
            packed = event.pack_client_message(self.win, "WM_PROTOCOLS", util.get_atom("WM_TAKE_FOCUS"), xproto.Time.CurrentTime)
            err = event.send_event_checked(self.win, 0,packed)
            err.check()
        else:
            return
        
        ewmh.set_active_window(self.win)
