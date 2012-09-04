import grid
import atom

from xpybutil import event

class Workspace:
    def __init__(self, screen):
        self.screen = screen
        self.grid = grid.Grid(self.screen)
        self.grid.shown = True
        self.windows = []
        self.shown = False
        
    def add_window(self, win):
        if win.fullscreen:
            self.grid.set_fullscreen(win)
        print win.get_wm_name(), 1
        if not win.get_wm_transient_for():
            print win.get_wm_name(), 2
            if not win.strut and atom._NET_WM_WINDOW_TYPE_DOCK not in win.type:
                    print win.get_wm_name(), 3
                    self.windows.append(win)
                    self.grid.add_window(win)
            else:
                self.screen.set_strut(win.strut)
                self.grid.update()
        else:
            self.windows.append(win)

    
    def remove_window(self, win):
        if win in self.windows:
            if not win.strut:
                self.windows.remove(win)
                self.grid.remove_window(win)
            else:
                self.screen.remove_strut(win.strut)
            if win.fullscreen:
                self.grid.unset_fullscreen()
            
    def update_layout(self):
        self.grid.update()
    
    def hide(self):
        if not self.shown:
            return
        self.grid.hide()
        for win in self.windows:
            win.unmap()
        self.shown = False
    
    def show(self):
        if self.shown:
            return
        self.grid.show()
        for win in self.windows:
            win.map()
        self.shown = True
