import xcb
import xcb.xproto as xproto
import atom


class Pane():
    def __init__(self, grid, x, y, width, height, windows):
        self.x =x
        self.y = y
        self.width = width
        self.height = height
        self.windows = windows
        self.grid = grid
        
    def reconfigure(self):
        win_num = len(self.windows)
        w = self.width/win_num  
        h = self.height
        x = self.x
        y = self.y
        for win in self.windows:
            win.configure(x, y, w, h)
                
            if x < self.width:
                x = x + w
            
    
class Grid():
    def __init__(self, screen, win_store):
        self.win_store = win_store
        self.panes = []
        self.shown = False
        self.screen = screen
        self.fullscreen = False
        
    def hide(self):
        if self.shown:
            self.shown = False
    
    def show(self):
        if not self.shown:
            self.shown =True
    
    def switch_windows(self, win1, win2):
        if self.fullscreen:
            return
        win_list = self.win_store.get_list()
        if win1 in win_list and win2 in win_list:
            ind1 = win_list.index(win1)
            ind2 = win_list.index(win2)
            if ind1 == ind2:
                return
            print "swapping windows:", win1, win2
            win_list.remove(win1)
            win_list.remove(win2)
            win_list.insert(ind2, win1)
            win_list.insert(ind1, win2)
            self.update()
    
    def set_fullscreen(self, win):
        x = self.screen.real_x
        y = self.screen.real_y 
        w = self.screen.real_w
        h = self.screen.real_h
        pane = Pane(self, x, y, w, h, [win])
        pane.reconfigure()
        self.fullscreen = True
        
    def unset_fullscreen(self):
        self.fullscreen = False
        
        
    def update(self):
        if not self.shown:
            return
        if self.fullscreen:
            return
        
        windows = []
        win_store_list = self.win_store.get_list()
        for win in win_store_list:
            try:
                if not win.get_wm_transient_for():
                    if not win.strut and atom._NET_WM_WINDOW_TYPE_DOCK not in win.type:
                        if win.wm.current_workspace == win.workspace:
                            windows.append(win)
            except xproto.BadWindow:
                pass
        win_num = len(windows)
        self.panes =[]
        x = self.screen.x
        y = self.screen.y
        w = self.screen.width
        h = self.screen.height
        
        if win_num == 1:
            pane = Pane(self, x, y, w, h, windows)
            self.panes.append(pane)
      
        elif win_num == 2:
            w = w/2
            for win in windows: 
               pane = Pane(self, x, y, w, h, [win])
               self.panes.append(pane)
               x = x + w
               
               

        elif win_num > 2:
            #print "more than 2 windows"
            pane = 0
            for win in windows:
                if win == windows[0]:
                    h=h - (h/3)
                    #print "main pane has y and h:", y, h
                    pane = Pane(self, x,y, w, h, [win])
                    self.panes.append(pane)
                    if self.screen.v_strut:
                        y=h+self.screen.y
                    else:
                        y = h
                    h = h/2
                elif len(self.panes) == 1 :
                    pane = Pane(self, x, y, w, h, [win])
                    self.panes.append(pane)
                else:
                    pane.windows.append(win)
        for pane in self.panes:
                pane.reconfigure()
                
            
