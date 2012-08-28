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
    
    def set_strut(self, strut):
        self.y += strut['top']
        self.x += strut['left']
        self.height = (self.height - strut['top']) - strut['bottom']
        self.width = (self.width - strut['right']) - strut['left']
    
    def remove_strut(self, strut):
        self.y -= strut['top']
        self.x -= strut['left']
        self.height = (self.height + strut['top']) + strut['bottom']
        self.width = (self.width + strut['right']) + strut['left']