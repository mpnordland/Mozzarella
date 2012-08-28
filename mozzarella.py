import xcb
from xcb import xproto
from xcb.xproto import ConfigWindow as cw
import xpybutil
from xpybutil import event, ewmh, icccm, mousebind, keybind, util, cursor
import os, traceback, sys, time
import grid
from window import Window
from screen import Screen
import config
from config import bind_launcher_keys, spawn


Event = event.Event
exit = False



class Manager():
    def __init__ (self, conn) :
        self.conn = conn
        setup = self.conn.get_setup()
        self.screen = Screen(self.conn, setup.roots[0], self)
        self.root = self.screen.root
        self.windows = []
        self.swap_win = None
        self.swaps = 0
        self.default_cursor= cursor.create_font_cursor(cursor.FontCursor.LeftPtr)
        self.move_cursor = cursor.create_font_cursor(cursor.FontCursor.Fleur)
        self.grids = []
        self.current_grid = None
        self.logger = config.logger
        
        atomstrs = ["_NET_WM_STRUT_PARTIAL", "_NET_WM_STATE_FULLSCREEN", "_NET_NUMBER_OF_DESKTOPS",
                            "_NET_CURRENT_DESKTOP"]
        atoms = []
        for atom in atomstrs:
            atoms.append(util.get_atom(atom))

        ewmh.set_supported(atoms)
        
        self.no_window_events = [xproto.MappingNotifyEvent, 
                                                    xproto.MapRequestEvent, 
                                                    xproto.ConfigureRequestEvent]
                                                    
        eventmask = [xproto.EventMask.SubstructureRedirect | xproto.EventMask.SubstructureNotify | xproto.EventMask.EnterWindow]
        err = self.conn.core.ChangeWindowAttributesChecked(self.root.win, xproto.CW.EventMask, eventmask)
        err.check()
        
        self.conn.core.ChangeWindowAttributesChecked(self.root.win, xproto.CW.Cursor, [self.default_cursor])
        
        
        
        self.scan_windows()
        self.do_grids(self.screen)

    def scan_windows(self):
        q = self.conn.core.QueryTree(self.root.win).reply()
        for item in q.children:
            win = Window(item, self.conn, self)
            attrs = win.get_attributes()
            state = win.get_wm_state()
            if attrs and attrs.map_state == xproto.MapState.Unmapped or attrs.overide_redirect:
               continue
            if state and state['state'] == icccm.State.Withdrawn:
                continue
            if win.fullscreen:
                self.current_grid.set_fullscreen(win)
            self.windows.append(win)
            if not win.get_wm_transient_for():
                if not win.strut:
                    self.current_grid.add_window(win)
                else:
                    self.screen.set_strut(win.strut)
                event.connect('DestroyNotify', win.win, self.handle_unmap_event)
                event.connect('UnmapNotify', win.win, self.handle_unmap_event)
                event.connect('EnterNotify', win.win, self.handle_enter_event)
                
    def do_grids(self, screen):
        for x in range(config.grids):
            self.grids.append(grid.Grid(screen))
        self.current_grid = self.grids[0]
        self.current_grid.shown = True
        ewmh.set_number_of_desktops(config.grids)
        ewmh.set_current_desktop(0)
            
    def get_window(self, win):
        '''
        A method to get a Window object for an X window ID
        If it exists in the Manager object's list of windows, that will be returned.
        otherwise a new Window object is created and returned
        '''
        for window in self.windows:
            if window.win ==win:
                return window
        try:
            return Window(win, self.conn, self)
        except xproto.BadWindow:
            return None
    
    def get_window_by_pos(self, x, y):
        '''
        A method to get a Window object by where it is
        '''
        for window in self.windows:
            if (x >= window.x and x <= window.x +window.w) and (y >= window.y and y <= window.y + window.h):
                return window
        return None
        
    def grab_mouse(self):
        mods, button = mousebind.parse_buttonstring(config.mouse_move_string)
        mousebind.grab_button(self.root.win, mods, button)
        event.connect('ButtonPress', self.root.win, self.handle_mouse_press)
        event.connect('ButtonRelease', self.root.win, self.handle_mouse_release)                
    
    def register_handlers(self):
        print "Registering Handlers"
        event.connect('MapRequest', None, self.handle_map_event)
        event.connect('ConfigureRequest', None, self.handle_configure_event)
        keybind.bind_global_key('KeyRelease', 'Mod4-Right', self.next_grid)
        keybind.bind_global_key('KeyRelease', 'Mod4-Left', self.prev_grid)
        self.grab_mouse()

    def handle_map_event(self, evt):
        win = Window(evt.window, self.conn, self)
        print "mapping:", win
        state = win.get_wm_state()
        if state and state['state'] == icccm.State.Withdrawn:
            return
        win.map()
        
        self.windows.append(win)
        
        if win.fullscreen:
            self.current_grid.set_fullscreen(win)
        
        if not win.get_wm_transient_for():
            if not win.strut:
                self.current_grid.add_window(win)
                self.logger.log( "adding window" + str(win))
            else:
                self.screen.set_strut(win.strut)
                self.current_grid.update_panes()
            event.connect('DestroyNotify', win.win, self.handle_unmap_event)
            event.connect('UnmapNotify', win.win, self.handle_unmap_event)
        event.connect('EnterNotify', win.win, self.handle_enter_event)
        
    
    def handle_unmap_event(self, evt):
        event.disconnect('DestroyNotify', evt.window)
        event.disconnect('UnmapNotify', evt.window)
        win = self.get_window(evt.window)
        if not win:
            return
        if not win.strut:
            self.current_grid.remove_window(win)
        else:
            self.screen.remove_strut(win.strut)
            self.current_grid.update_panes()
            #self.windows.remove(win)
        if win.fullscreen:
            self.current_grid.unset_fullscreen()
    
    def handle_configure_event(self, evt):
        '''
        This is where ConfigureRequstEvents and ConfigureNotifyEvents get handled
        Transient windows are floated, and others are not
        '''
        win = self.get_window(evt.window)
        if not win:
            return
        
        if win.get_wm_transient_for():
            y = x = w = h = bw = 0
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
            win.configure(x, y, w, h, bw)
        else:
            self.current_grid.update_panes()
            
    def handle_mouse_press(self, evt):
        self.swap_win = None
        err = self.conn.core.ChangeWindowAttributesChecked(self.root.win, xproto.CW.Cursor, [self.move_cursor])
        dwin = self.get_window_by_pos(evt.root_x, evt.root_y)
        self.swap_win = dwin
         
    def handle_mouse_release(self, evt):
        owin = self.get_window_by_pos(evt.root_x, evt.root_y)
        self.current_grid.switch_windows(self.swap_win, owin)
        err = self.conn.core.ChangeWindowAttributesChecked(self.root.win, xproto.CW.Cursor, [self.default_cursor])
        self.swap_win = None 
        
    def handle_enter_event(self, evt):
        window =  self.get_window(evt.window)
        if evt.mode != xproto.NotifyMode.Normal:
            return
        window.focus()
    
    def next_grid(self):
        grid_n = self.grids.index(self.current_grid) + 1
        if grid_n > len(self.grids)-1:
            grid_n = 0
        self.logger.log("hiding grid:"+str(self.grids.index(self.current_grid)))
        self.current_grid.hide()
        self.current_grid = self.grids[grid_n]
        self.logger.log( "showing grid:" + str(grid_n))
        self.current_grid.show()
        ewmh.set_current_desktop(grid_n)
        
    def prev_grid(self):
        grid_p = self.grids.index(self.current_grid) - 1
        self.logger.log("hiding grid:"+str(self.grids.index(self.current_grid)))
        self.current_grid.hide()
        self.current_grid = self.grids[grid_p]
        self.logger.log( "showing grid:" + str(grid_p))
        self.current_grid.show()
        if grid_p < 0:
            grid_p = len(self.grids)-1
        ewmh.set_current_desktop(grid_p)
    
    def no_window(self, evt):
        for event in self.no_window_events:
            if isinstance(evt, event):
                return True
        return False
    
    def remap(self):
        for window in self.windows:
            try:
                attrs = window.get_attributes()
                state = window.get_wm_state()
                if (state and state['state'] == icccm.State.Withdrawn) or (attrs and attrs.map_state == xproto.MapState.Unmapped):
                    if not window.strut:
                        self.current_grid.remove_window(window)
                    else:
                        self.screen.remove_strut(win.strut)
                        self.update_panes()
                    self.windows.remove(window)
            except xproto.BadWindow:
                self.current_grid.remove_window(window)
                self.windows.remove(window)
            except xproto.BadMatch, e:
                self.logger.log( "BadMatch")
        self.current_grid.update_panes()

def quit():
        global exit
        exit = True
      
def mainloop():
    wm = Manager(xpybutil.conn)
    wm.logger.log('Starting Mozzarella!')
    wm.register_handlers()
    wm.logger.log("Binding keys, Mod4-x to quit, Mod4-r to remap, whatever good that does")
    bind_launcher_keys()
    keybind.bind_global_key('KeyRelease', 'Mod4-x', quit)
    keybind.bind_global_key('KeyRelease', 'Mod4-r', wm.remap)
    try:
        while True:
            if exit:
                break
            event.read()
            for e in event.queue():
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
                wm.remap()
                #wm.logger.repeat()
    except xcb.Exception:
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    
    mainloop()
    print "Quitting Mozzarella"
