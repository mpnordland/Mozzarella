import xcb
from xcb import xproto
from xpybutil import event, ewmh, icccm, mousebind, keybind, cursor, conn as Xconn
import os, traceback, sys, time
import grid
from window import Window
from screen import Screen
from workspaces import Workspace
from window_store import WindowStore
import config
from config import bind_launcher_keys, spawn
import atom
import logger

#This variable handles exiting from the mainloop()
#Don't remove it
exit = False

cw = xproto.ConfigWindow

class OtherWindowManagerRunning(Exception):
    pass


class Manager():
    def __init__ (self, conn) :
        self.conn = conn
        setup = self.conn.get_setup()
        self.current_workspace = None
        self.screen = Screen(self.conn, setup.roots[0], self)
        self.root = self.screen.root
        self.win_store = WindowStore(self.conn, self, [])
        self.swap_win = None
        self.swaps = 0
        self.default_cursor= cursor.create_font_cursor(cursor.FontCursor.LeftPtr)
        self.move_cursor = cursor.create_font_cursor(cursor.FontCursor.Fleur)
        self.workspaces = []
        self.current_workspace_num = 1
        self.current_name = 'Desktop'
        self.current_win = None
        self.logger = logger.DzenLogger(self)
        #Proclaim to all just what we support
        atoms = ["_NET_WM_STRUT_PARTIAL", "_NET_WM_STATE_FULLSCREEN", "_NET_NUMBER_OF_DESKTOPS",
                            "_NET_CURRENT_DESKTOP", "_NET_ACTIVE_WINDOW"]
        atom.update_atom_cache(atoms)
        ewmh.set_supported(atom.atom_cache)
        
        #this is a list of the events that we don't want/need to filter by window.
        #Some such as MapRequest and ConfigureRequest we usually don't have a reference 
        #for the window yet
        self.no_window_events = [xproto.MappingNotifyEvent, 
                                                    xproto.MapRequestEvent, 
                                                    xproto.ConfigureRequestEvent]
                                                    
        # set substructure redirect on the root window.
        eventmask = [xproto.EventMask.SubstructureRedirect | xproto.EventMask.SubstructureNotify]
        err = self.conn.core.ChangeWindowAttributesChecked(self.root.win, xproto.CW.EventMask, eventmask)
        try:
            err.check()
        except xproto.BadAccess:
            print "We can't grab window manager status!, is there something else running?"
            raise OtherWindowManagerRunning
        
        self.conn.core.ChangeWindowAttributesChecked(self.root.win, xproto.CW.Cursor, [self.default_cursor])
        
        self.do_workspaces(self.screen)
        self.scan_windows()
        self.logger.start()

    def scan_windows(self):
        q = self.conn.core.QueryTree(self.root.win).reply()
        for item in q.children:
            win = Window(item, self.conn, self)
            attrs = win.get_attributes()
            state = win.get_wm_state()
            if attrs and attrs.map_state == xproto.MapState.Unmapped: #or attrs.overide_redirect:
               continue
            if state and state['state'] == icccm.State.Withdrawn:
                continue
            eventmask = [xproto.EventMask.EnterWindow]
            self.conn.core.ChangeWindowAttributes(win.win, xproto.CW.EventMask, eventmask)
            if not win.get_wm_transient_for():
                event.connect('DestroyNotify', win.win, self.handle_unmap_event)
                event.connect('UnmapNotify', win.win, self.handle_unmap_event)
            if win.strut:
                self.screen.set_strut(win.strut)
            self.win_store.add(win)
            event.connect('EnterNotify', win.win, self.handle_enter_event)
                
    def do_workspaces(self, screen):
        for x in range(config.workspaces):
            self.workspaces.append(Workspace(screen, self.win_store))
            
        self.current_workspace = self.workspaces[0]
        self.current_workspace.shown = True
        ewmh.set_number_of_desktops(config.workspaces)
        ewmh.set_current_desktop(0)
        
    def grab_mouse(self):
        '''
        This method grabs a button and binds to press and realease events
        '''
        mods, button = mousebind.parse_buttonstring(config.mouse_move_string)
        mousebind.grab_button(self.root.win, mods, button)
        event.connect('ButtonPress', self.root.win, self.handle_mouse_press)
        event.connect('ButtonRelease', self.root.win, self.handle_mouse_release)                
    
    def register_handlers(self):
        '''
        Adds handlers for no_window_events, binds workspace moving
        keys and grabs the mouse actions we care about
        '''
        print "Registering Handlers"
        event.connect('MapRequest', None, self.handle_map_event)
        event.connect('ConfigureRequest', None, self.handle_configure_event)
        keybind.bind_global_key('KeyRelease', 'Mod4-Right', self.next_workspace)
        keybind.bind_global_key('KeyRelease', 'Mod4-Left', self.prev_workspace)
        keybind.bind_global_key('KeyRelease',   'Mod4-k', self.destroy_window)
        self.grab_mouse()

    def handle_map_event(self, evt):
        '''
        window mapping operations occur here
        '''
        win = self.win_store.get_window(evt.window)
        if not win:
            return
        try:
            state = win.get_wm_state()
            if state and state['state'] == icccm.State.Withdrawn:
                return
            win.map()
        except xproto.BadWindow:
            return
        self.win_store.add(win)
        self.current_workspace.update()
        event.connect('DestroyNotify', win.win, self.handle_unmap_event)
        event.connect('UnmapNotify', win.win, self.handle_unmap_event)
        eventmask = [xproto.EventMask.EnterWindow]
        self.conn.core.ChangeWindowAttributes(win.win, xproto.CW.EventMask, eventmask)
        event.connect('EnterNotify', win.win, self.handle_enter_event)
        pointer_pos = self.conn.core.QueryPointer(self.root.win).reply()
        ifwin = self.win_store.get_window_by_pos(pointer_pos.root_x, pointer_pos.root_y)
        if ifwin:
            ifwin.focus()
        
    
    def handle_unmap_event(self, evt):
        '''
        This method handles both DestroyNotify and UnmapNotify
        because they both seem to indicate the same thing:
        We no longer need this window.
        '''
        event.disconnect('DestroyNotify', evt.window)
        event.disconnect('UnmapNotify', evt.window)
        win = self.win_store.get_window(evt.window)

        self.win_store.remove(win)
        self.current_workspace.update()

    def handle_configure_event(self, evt):
        '''
        This is where ConfigureRequstEvents and ConfigureNotifyEvents get handled
        Transient windows are floated, and others are not
        '''
        win = self.win_store.get_window(evt.window)
        #if we don't have a window, we're stuck:
        if not win:
            return
        try:
            
            if win.get_wm_transient_for():
                y = x = w = h = 0
                bw = 2
                if evt.value_mask & cw.X:
                    x = evt.x
                if evt.value_mask & cw.Y:
                    y = evt.y
                if evt.value_mask & cw.Height:
                    h = evt.height
                if evt.value_mask & cw.Width:
                    w = evt.width
                if evt.value_mask & cw.BorderWidth:
                    bw = evt.border_width
                bw = 2
                win.configure(x, y, w, h, bw)
            else:
                self.current_workspace.update()
        except (xproto.BadWindow, xproto.BadMatch):
            self.win_store.remove(win)
            return
            
    def handle_mouse_press(self, evt):
        '''
        Mouse button presses are handled here.
        Basically set the swap window to None, change the cursor, get the window to be swapped
        and set swap_win to that
        '''
        self.swap_win = None
        err = self.conn.core.ChangeWindowAttributesChecked(self.root.win, xproto.CW.Cursor, [self.move_cursor])
        dwin = self.win_store.get_window_by_pos(evt.root_x, evt.root_y)
        self.swap_win = dwin
         
    def handle_mouse_release(self, evt):
        '''
        Mouse button releases are handled here. we get the second window,
        switch it with the first, revert the cursor back to normal, and set swap_win to None
        '''
        owin = self.win_store.get_window_by_pos(evt.root_x, evt.root_y)
        self.current_workspace.grid.switch_windows(self.swap_win, owin)
        err = self.conn.core.ChangeWindowAttributesChecked(self.root.win, xproto.CW.Cursor, [self.default_cursor])
        self.swap_win = None 
        
    def handle_enter_event(self, evt):
        '''
        This event is used for setting the focus based on where the mouse is.
        Most of the work occurs in Window.focus()
        '''
        window =  self.win_store.get_window(evt.event)
        if evt.mode != xproto.NotifyMode.Normal:
            return
        if window:
            window.focus()
    
    def next_workspace(self):
        '''
        Part of Mozzarella's primative workspaces
        this switches to the next grid
        '''
        work_n = self.workspaces.index(self.current_workspace) + 1
        print "workspace num is:", work_n
        self.current_workspace_num += 1
        if self.current_workspace_num > config.workspaces:
            self.current_workspace_num = 1
        if work_n > len(self.workspaces)-1:
            work_n = 0
        self.current_workspace.hide()
        self.current_workspace = self.workspaces[work_n]
        self.current_workspace.show()
        ewmh.set_current_desktop(work_n)
        
    def prev_workspace(self):
        '''
        Part of Mozzarella's primative workspaces
        this switches to the previous grid
        '''
        work_p = self.workspaces.index(self.current_workspace) - 1
        print "workspace num is:", work_p
        self.current_workspace.hide()
        self.current_workspace = self.workspaces[work_p]
        self.current_workspace.show()
        if work_p < 0:
            work_p = len(self.workspaces)
        self.current_workspace_num -= 1
        if self.current_workspace_num <= 0:
            self.current_workspace_num = config.workspaces
            
        ewmh.set_current_desktop(work_p)
    
    def destroy_window(self):
        #will delete the currently focused
        #window
        if self.current_win:
            self.current_win.destroy()
        
        
    
    def no_window(self, evt):
        '''
        This method makes the event loop a little nicer to read, and shorter.
        '''
        for event in self.no_window_events:
            if isinstance(evt, event):
                return True
        return False


def quit():
        '''
        Allows using a keypress (release actually) to 
        quit the window manager, and thus, usually, the X session
        '''
        global exit
        exit = True
      
def mainloop():
    wm = Manager(Xconn)
    wm.register_handlers()
    bind_launcher_keys()
    #Should move these to Manager.register_handlers()
    keybind.bind_global_key('KeyRelease', 'Mod4-x', quit)
    try:
        while True:
            if exit:
                break
            event.read()
            for e in event.queue():
                #print e
                w = None
                if wm.no_window(e):
                    w = None
                elif hasattr(e, 'window'):
                    w = e.window
                elif hasattr(e, 'event'):
                    w = e.event
                elif hasattr(e, 'requestor'):
                    w = e.requestor
                key = (e.__class__, w)
                for cb in event.__callbacks.get(key, []):
                    cb(e)
                wm.conn.flush()
    except xcb.Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    mainloop()
    print "Quitting Mozzarella"
