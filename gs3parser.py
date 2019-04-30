from bs4 import BeautifulSoup
import curses
import re

class GS3Parser:

    def __init__(self, styles, logger):
        # this is load from file
        #curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        #self.style_color = {'roomDesc': curses.COLOR_WHITE}
        self.styles = styles
        self.logger = logger
        self.spells = {}
        self.stats = {}
        self.hands = {'left': '', 'right': ''}
        self.injuries = []
        self.bold = 0
        self.style = 'default'
        self.text = []

    def clear_vars(self):
        self.bold = 0
        self.spells = {}
        self.stats = {}
        self.style = 'default'
        self.injuries = []
        self.text = []
        
    def parse(self, data):
        """
        """
        soup = BeautifulSoup(data, 'html.parser')
        for child in soup:

            name = child.name
            if not name:
                self._text(child)
            elif 'a' == name:
                if 'noun' in child.attrs:
                    self._noun(child)
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
                self.bold = curses.A_BOLD
            elif 'popbold' == name:
                self.bold = 0
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
                self._style(child)
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

    def _noun(self, elem):
        """
        """
        self.text.append(self.styles['noun'])
        self.text.append(elem.text)
        self.text.append(self.styles['default'])
        
    def _progressbar(self, elem):
        """Parses the progressbar tag
        """
        if 'text' in elem.attrs:
            self.stats[elem.attrs['id']] = elem.attrs['text']

    def _style(self, elem):
        """Parses the style tag
        """
        if 'id' not in elem.attrs:
            return

        # Accesses color pair by styles.ini value
        if elem.attrs['id'].lower() in self.styles:
            self.text.append(self.styles[elem.attrs['id'].lower()])
        else:
            self.text.append(self.styles['default'])

    def _text(self, elem):
        """
        """
        if re.match('---', elem) or re.match(';', elem):
            self.text.append(self.styles['lnet'])
        self.text.append(elem)
