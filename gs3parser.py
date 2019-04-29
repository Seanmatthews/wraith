from bs4 import BeautifulSoup
import curses
import re

class GS3Parser:

    def __init__(self, config, logger):
        # this is load from file
        #curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        #self.style_color = {'roomDesc': curses.COLOR_WHITE}
        self.config = {} #config
        self.logger = logger
        self.spells = {}
        self.stats = {}
        self.hands = {'left': '', 'right': ''}
        self.injuries = []
        self.bold = False
        self.style = 'default'
        self.text = ""

    def clear_vars(self):
        self.bold = False
        self.spells = {}
        self.stats = {}
        self.style = 'default'
        self.injuries = []
        self.text = ""
        
    def parse(self, data):
        """
        """
        #if not self._is_xml(data):
        #    self.text = str(data)
        #    self.logger.write(self.text)
        #    return
        
        soup = BeautifulSoup(data, 'html.parser')
        for child in soup:

            name = child.name
            if not name:
                self.text += child
            elif 'a' == name:
                #TODO
                pass
            elif 'compass' == name:
                pass
            elif 'dialogdata' == name:
                self._dialogdata(child)
            elif 'image' == name:
                #TODO
                pass
            elif 'indicator' == name:
                pass
            elif 'left' == name:
                self.hands['left'] = ''
            elif 'nav' == name:
                pass
            elif 'popstream' == name:
                pass
            elif 'pushstream' == name:
                pass
            elif 'progressbar' == name:
                self._progressbar(child)
            elif 'pushbold' == name:
                self.bold = True
            elif 'popbold' == name:
                self.bold = False
            elif 'preset' == name:
                pass
            elif 'prompt' == name:
                pass
            elif 'resource' == name:
                #TODO
                pass
            elif 'right' == name:
                self.hands['right'] = ''
            elif 'spell' == name:
                #TODO
                pass
            elif 'style' == name:
                self.style = child.attrs['id']
            else:
                if name is not None:
                    self.logger.write('unrecognized tag: ' + name + '\n') 

    def _is_xml(self, line):
        """Determine whether a string contains XML-like tags
        """
        return re.search('<.+?>', line) is not None
        
    def _dialogdata(self, elem):
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

    def _progressbar(self, elem):
        """Parses the progressbar tag
        """
        if 'text' in elem.attrs:
            self.stats[elem.attrs['id']] = elem.attrs['text']

    def _style(self, elem):
        """Parses the style tag
        """
        if 'id' not in elem:
            return

        self.style = self.config[elem['id']]
