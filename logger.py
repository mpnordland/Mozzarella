import thread

class Logger:
    def __init__(self, wm):
        pass
    def log(self, text):
        print text


class DzenLogger:
    def __init__(self, wm):
        self.colors = {"fg": "#0088cc", "bg": "#ffffff"}
        self.text_f = ''
        self.wm = wm
        
    def set_norm_colors(self, text):
        color_tag="^fg(%s)^bg(%s)".format(self.colors['fg'], self.colors['bg'])
        return color_tag + text
        
    def set_revse_colors(self, text):
        color_tag="^fg(%s)^bg(%s)" % (self.colors['bg'], self.colors['fg'])
        return color_tag + text
    
    def update(self):
        text_f = self.set_norm_colors("^p(_LEFT)")
        
        print text_f, 
        print ' '.join(map(str,[self.wm.current_workspace_num, "^p(10)",self.wm.current_name]))
    def run(self):
        while 1:
            self.update()

    def start(self):
        thread.start_new_thread(self.run, ())