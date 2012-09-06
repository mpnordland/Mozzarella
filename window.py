from xcb.xproto import ConfigWindow as cw
import xcb.xproto as xproto
from xpybutil import ewmh, icccm, util, event
import atom

atoms = ["_NET_WM_STATE_FULLSCREEN" , "WM_PROTOCOLS", "WM_TAKE_FOCUS", "WM_DELETE_WINDOW","_NET_WM_WINDOW_TYPE_DOCK", "_NET_WM_STATE_STICKY"]
atom.update_atom_cache(atoms)

class Window:
    def __init__(self, window, conn, wm):
        #The XID for our window, our connection to the 
        #Xserver, and our reference to the Manager object
        self.win = window
        self.conn = conn
        self.wm = wm
        self.workspace = self.wm.current_workspace
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
        self.sticky = False
        if net_state and atom._NET_WM_STATE_FULLSCREEN in net_state:
            self.fullscreen = True
        if net_state and atom._NET_WM_STATE_STICKY in net_state:
            self.sticky = True
            
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
        if protos and atom.WM_TAKE_FOCUS in protos:
            take_focus = True
        if input and take_focus:
            self.local_active = True
        elif input and not take_focus:
            self.passive = True
        elif take_focus and not input:
            self.global_active = True
        else:
            self.no_input = True
        
        #what kind of a window are we?
        self.type = self.get_wm_window_type()
        if not self.type:
            self.type = []
    
    def get_wm_window_type(self):
        return ewmh.get_wm_window_type(self.win).reply()
        
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
        values[1] = y +1
        self.conn.core.ConfigureWindowChecked(self.win, mask, values)
        values[1] = y
        self.conn.core.ConfigureWindowChecked(self.win, mask, values)
        
    def map(self):
        icccm.set_wm_state(self.win, icccm.State.Normal, 0)
        self.conn.core.MapWindow(self.win)
    
    def unmap(self):
        self.conn.core.UnmapWindow(self.win)
        
    def focus(self):
        try:
            if self.passive :
                self.conn.core.SetInputFocus(xproto.InputFocus.PointerRoot, self.win, xproto.Time.CurrentTime)
            elif self.local_active:
                err = self.conn.core.SetInputFocusChecked(xproto.InputFocus.PointerRoot, self.win, xproto.Time.CurrentTime)
                err.check()
                packed = event.pack_client_message(self.win, "WM_PROTOCOLS", atom.WM_TAKE_FOCUS, xproto.Time.CurrentTime)
                event.send_event(self.win, 0,packed)
            elif self.global_active:
                packed = event.pack_client_message(self.win, "WM_PROTOCOLS", atom.WM_TAKE_FOCUS, xproto.Time.CurrentTime)
                event.send_event(self.win, 0,packed)
            else:
                return
            self.wm.current_name = self.get_wm_name()
            self.wm.current_win = self
            ewmh.set_active_window(self.win)

        except (xproto.BadMatch, xproto.BadWindow):
            return
    
    def destroy(self):
        #we need to handle WM_DELETE_window
        try:
            protos = self.get_wm_protocols()
            if protos and atom.WM_DELETE_WINDOW in protos:
                packed = event.pack_client_message(self.win, "WM_PROTOCOLS", atom.WM_DELETE_WINDOW, xproto.Time.CurrentTime)
                event.send_event(self.win, 0,packed)
            else:
                self.conn.core.DestroyWindow(self.win)
        except xproto.BadWindow:
            return
