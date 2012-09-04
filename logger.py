import thread
import dzen_time

class Logger:
    def __init__(self, wm):
        pass
    def log(self, text):
        print text


class DzenLogger:
    def __init__(self, wm):
        self.colors = {"fg": "#ffffff", "bg": "#0088cc"}
        self.text_f = ''
        self.wm = wm
        
    def set_norm_colors(self, text):
        color_tag="^fg(%s)^bg(%s)".format(self.colors['fg'], self.colors['bg'])
        return color_tag + text
        
    def set_revse_colors(self, text):
        color_tag="^fg(%s)^bg(%s)" % (self.colors['bg'], self.colors['fg'])
        return color_tag + text
    
    def update(self):
        time = dzen_time.update()
        print ''.join(map(str,[self.wm.current_workspace_num, "  ",self.wm.current_name, "^p(_RIGHT)^p(-170)", time]))
    
    def run(self):
        while 1:
            self.update()

    def start(self):
        thread.start_new_thread(self.run, ())