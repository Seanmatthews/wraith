from bs4 import BeautifulSoup
import curses
import re

class GS3Parser:

    def __init__(self, logger):
        # this is load from file
        #curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        #self.style_color = {'roomDesc': curses.COLOR_WHITE}
        self.logger = logger
        self.spells = {}
        self.stats = {}
        self.injuries = []
        self.bold = False
        self.text = ""

    def clear_vars(self):
        self.spells = {}
        self.stats = {}
        self.injuries = []
        self.text = ""
        
    def _is_xml(self, line):
        return re.search('<.+?>', line) is not None
        
    def parse(self, data):
        """
        """
        if not self._is_xml(data):
            self.text = str(data)
            return
        
        soup = BeautifulSoup(data, 'html.parser')
        for child in soup:
            # TODO check if plain text
            name = child.name
            if 'dialogdata' == name:
                self.dialogdata(child)
            elif 'progressbar' == name:
                self.progressbar(child)
            elif 'pushbold' == name:
                self.bold = True
            elif 'popbold' == name:
                self.bold = False

    def dialogdata(self, elem):
        """Parse the dialogdata tag & children
        """
        attrs = elem.attrs

        # If this doesn't exist, no point
        if 'id' not in attrs:
            return

        # Active spells
        if 'activespells' == attrs['id'].lower():
            if 'clear' in attrs and attrs['clear'].lower() == 't':
                self.spells.clear()
            else:
                for child in elem:
                    if child.name == 'label':
                        self.spells[child.attrs['id']] = child.attrs['value']
                        self.spells['testspell'] = '4:01'

    def progressbar(self, elem):
        """
        """
        if 'text' in elem.attrs:
            self.stats[elem.attrs['id']] = elem.attrs['text']
