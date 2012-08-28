class Logger:
    def log(self, text):
        print text


class DzenLogger(Logger):
    def __init__(self):
        self.colors = {"fg": "#0088cc", "bg": "#ffffff"}
        self.text_f = ''
        
    def set_norm_colors(self, text):
        color_tag="^fg(%s)^bg(%s)".format(self.colors['fg'], self.colors['bg'])
        return color_tag + text
        
    def set_revse_colors(self, text):
        color_tag="^fg(%s)^bg(%s)".format(self.colors['bg'], self.colors['fg'])
        return color_tag + text

    def log(self, text, revse = True):
        if revse:
            text_f = self.set_revse_colors(text)
        else:
            text_f = self.set_norm_colors(text)
        self.text_f = text_f
        print text_f
    
    def repeat(self):
        print self.text_f