import grid
import atom
import xcb.xproto as xproto
from xpybutil import event

class Workspace:
    def __init__(self, screen, win_store):
        self.screen = screen
        self.grid = grid.Grid(self.screen, win_store)
        self.grid.shown = True
        self.win_store = win_store
        self.shown = False
        self.hidden = []
                
    def update(self):
        self.screen.reset_struts()
        self.grid.unset_fullscreen()
        win_list = self.win_store.get_list()
        for win in win_list:
            if win.strut:
                self.screen.set_strut(win.strut)
            if win.fullscreen:
                self.grid.set_fullscreen(win)
        self.grid.update()
        
    def hide(self):
        if not self.shown:
            return
        windows = []
        for win in self.win_store.get_list():
            if win.workspace is self and not win.sticky:
                try:
                    print win.get_wm_name()
                    win.unmap()
                    windows.append(win)
                except xproto.BadWindow:
                    continue
        self.hidden = windows
        self.shown = False
        self.update()
    
    def show(self):
        if self.shown:
            return
        for win in self.hidden:
            if win.workspace is self and not win.sticky:
                print win.get_wm_name()
                win.map()
                self.win_store.add(win)
        self.hidden = []
        self.shown = True
        self.update()
