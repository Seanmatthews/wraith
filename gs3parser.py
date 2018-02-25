from html.parser import HTMLParser
import curses

class GS3Parser(HTMLParser):

    def __init__(self, scr):
        super(self).__init__(self) #???
        self.scr = scr
        self.tag = ''
        self.attrs = []

        # this is load from file
        curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.style_color = {'roomDesc': curses.COLOR_WHITE}
#        self.style_format = {'roomDesc': lambda d, a: d, 
#                             'a': lambda d, a: d + ' ' + a}
        
    def handle_starttag(self, tag, attrs):
        self.tag = tag
        self.attrs = attrs

    def handle_endtag(self, tag):
        self.tag = ''
        self.attrs = []

    def handle_data(self, data):
        self.scr.addstr(data,
                        curses.color_pair(self.style_color.get(self.tag, 0)))
