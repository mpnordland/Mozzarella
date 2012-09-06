from window import Window
from xcb import xproto

class WindowStore:
    def __init__(self, conn, wm, win_list):
        self.windows = win_list
        self.retained={}
        self.different = False
        self.conn = conn
        self.wm = wm
    
    def add(self, win):
        if win in self.windows:
            return
        self.windows.append(win)
        self.different = True
    
        
    def remove(self, win):
        if win in self.windows:
            self.windows.remove(win)
            self.different = True
    
    def get_list(self):
        return self.windows
    
    def retain(self, workspace, windows):
        self.retained[workspace] = windows
    
    def get_retained(self, workspace):
        try:
            windows = self.retained[workspace]
            del self.retained[workspace]
            return windows
        except KeyError:
            return []
    
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
            return Window(win, self.conn, self.wm)
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