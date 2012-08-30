import xcb
import xcb.xproto


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
            err = win.configure(x, y, w, h)
            try:
                err.check()
            except xcb.xproto.BadWindow, xcb.xproto.BadMatch:
                self.grid.remove_window(win)
                break
                
            if x < self.width:
                x = x + w
            
    
class Grid():
    def __init__(self, screen):
        self.windows = []
        self.panes = []
        self.shown = False
        self.screen = screen
        self.fullscreen = False
        
    def remove_window(self, window):
        if not self.shown:
            return
        if window in self.windows:
            self.windows.remove(window)
        self.update()
        
    def add_window(self, window, pos=0):
        if not self.shown:
            return
        self.windows.insert(0,window)
        self.update()
        
    def hide(self):
        '''
        This is the beginning of multiple workspaces
        '''
        if not self.shown:
            return
        for win in self.windows:
            win.unmap()
        self.shown = False
    
    def show(self):
        if self.shown:
            return
        for win in self.windows:
            win.map()
        self.shown =True
    
    def switch_windows(self, win1, win2):
        if self.fullscreen:
            return
        
        if win1 in self.windows and win2 in self.windows:
            ind1 = self.windows.index(win1)
            ind2 = self.windows.index(win2)
            if ind1 == ind2:
                return
            print "swapping windows:", win1, win2
            self.windows.remove(win1)
            self.windows.remove(win2)
            self.windows.insert(ind2, win1)
            self.windows.insert(ind1, win2)
            self.update()
    
    def set_fullscreen(self, win):
        x = self.screen.real_x
        y = self.screen.real_y 
        w = self.screen.real_w
        h = self.screen.real_h
        self.windows.insert(0, win)
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
            
        self.panes =[]
        win_num = len(self.windows)
        #print "we have this many windows: ", win_num
        x = self.screen.x
        y = self.screen.y
        w = self.screen.width
        h = self.screen.height
        
        if win_num == 1:
            pane = Pane(self, x, y, w, h, self.windows)
            self.panes.append(pane)
      
        elif win_num == 2:
            w = w/2
            for win in self.windows: 
               pane = Pane(self, x, y, w, h, [win])
               self.panes.append(pane)
               x = x + w
               
               

        elif win_num > 2:
            #print "more than 2 windows"
            pane = 0
            for win in self.windows:
                if win == self.windows[0]:
                    h=h - (h/3)
                    #print "main pane has y and h:", y, h
                    pane = Pane(self, x,y, w, h, [win])
                    self.panes.append(pane)
                    y = h
                    h = h/2
                elif len(self.panes) == 1 :
                    pane = Pane(self, x, y, w, h, [win])
                    self.panes.append(pane)
                else:
                    pane.windows.append(win)
        for pane in self.panes:
                pane.reconfigure()
                
            
