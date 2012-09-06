from window import Window

class Screen :
    def __init__(self, conn, screen, wm):
        self.conn = conn
        self.screen = screen
        self.wm = wm
        self.root = Window(self.screen.root, self.conn, self.wm)
        rg = self.root.get_geometry()
        self.width =rg.width
        self.height = rg.height
        self.x = rg.x
        self.y = rg.y
        self.real_y =rg.y
        self.real_x = rg.x
        self.real_w = rg.width
        self.real_h = rg.height
        self.v_strut = False
    
    def set_strut(self, strut):
        print "set_strut", strut
        if self.y < strut :
            strut_diff = strut['top'] - self.y
            self.y += strut_diff
            self.height = self.height - strut_diff
        
        if self.x < strut['left']:
            self.x += strut['left'] - self.x
            self.width = self.width - strut['left']
        self.v_strut = True
    
    def remove_strut(self, strut):
        print "remove_strut", strut
        if self.y >= strut['top']:
            self.y -= strut['top']
        self.x -= strut['left']
        self.height = (self.height + strut['top']) + strut['bottom']
        self.width = (self.width + strut['right']) + strut['left']
        self.v_strut = False
    
    def reset_struts(self):
        print "reset_struts"
        self.x = self.real_x
        self.y = self.real_y
        self.height = self.real_h
        self.width = self.real_w
