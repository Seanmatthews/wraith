#from html.parser import HTMLParser
from bs4 import BeautifulSoup
import curses

class GS3Parser:

    def __init__(self):
        # this is load from file
        #curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        #self.style_color = {'roomDesc': curses.COLOR_WHITE}
        pass
        
    def parse(self, data):
        ret = {}
        soup = BeautifulSoup(data, 'html.parse')
        for child in soup:
            if "dialogdata" == child.name:
                dialogdata(ret, child)
            
        return ret


    def dialogdata(self, data, elem):
        data['text'] = str(elem.attrs)
