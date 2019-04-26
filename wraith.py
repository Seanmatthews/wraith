#!/usr/bin/python3

from bs4 import BeautifulSoup
from gs3parser import GS3Parser
from queue import Queue
from threading import Thread

import asyncio
import concurrent.futures
import curses, curses.panel
import logging
import string
import sys
import time


POLL_INTERVAL = 0.01

class Wraith:
    
    def __init__(self):

        self.msg = ''
        self.readbuf = ''
        self.cmds = Queue()
        self.logfile = open('log.txt', 'w')
        self.parser = GS3Parser()
        
    @asyncio.coroutine
    def _user_input(self, scr):
        
        log = logging.getLogger('_user_input')
        log.info('starting')

        try:
            loop = asyncio.get_event_loop()
        
            while True:
                
                yield from asyncio.sleep(POLL_INTERVAL, loop=loop)
                last = scr.getch()
                if last < 0:
                    pass
                elif last == curses.KEY_BACKSPACE or last == 127:
                    self.msg = self.msg[:-1]
                elif last == curses.KEY_UP:
                    pass
                elif last == curses.KEY_DOWN:
                    pass
                elif last == curses.KEY_LEFT:
                    pass
                elif last == curses.KEY_RIGHT:
                    pass
                elif last == curses.KEY_ENTER or last == ord('\n'):
                    self.msg += '\n'
                    self.cmds.put(self.msg)
                    self.msg = ''
                elif chr(last).isprintable():
                    self.msg += chr(last)

        except KeyboardInterrupt:
            raise

    
    @asyncio.coroutine
    def _server_conn(self, scr):

        try:
            loop = asyncio.get_event_loop()
            reader, writer = yield from asyncio.open_connection('localhost', 8000, loop=loop)
            
            while True:
                yield from asyncio.sleep(POLL_INTERVAL, loop=loop)

                # Read incoming
                try:
                    linegen = reader.readline()
                    line = yield from asyncio.wait_for(linegen, timeout=POLL_INTERVAL)
                    self.readbuf += line.decode()
                except asyncio.TimeoutError:
                    pass

                # Write outgoing & add to main window
                if not self.cmds.empty():
                    cmd = self.cmds.get(block=False)
                    writer.write(cmd.encode())
                    self.readbuf += '> '
                    self.readbuf += cmd + '\n'

        except KeyboardInterrupt:
            raise


    def _redraw_main(self, win, data):
        self.logfile.write(data)
        #for line in self.readbuf.splitlines():
        win.addstr(data + '\n')
        win.noutrefresh()

        
    def _redraw_cmdline(self, win):
        h, w = win.getmaxyx()
        win.clear()
        win.border()
        win.addstr(1, 2, self.msg)
        win.noutrefresh()

        
    def _redraw_sidebar(self, win):
        win.noutrefresh()


    @asyncio.coroutine
    def _update_windows(self, scr):

        # Create windows
        sidebar_width = 15
        chatline_yx = (curses.LINES - 3, 0)
        sidebar_hwyx = (curses.LINES - 3, sidebar_width - 1, 0, 0)
        main_hwyx = (curses.LINES - 5, curses.COLS - sidebar_width - 1,
                     2, sidebar_width + 1)

        win_sidebar = scr.derwin(*sidebar_hwyx)
        win_cmdline = scr.derwin(*chatline_yx)
        win_main = scr.derwin(*main_hwyx)

        # Window properties
        win_main.scrollok(True)
        win_main.idlok(True)

        try:
            loop = asyncio.get_event_loop()
            while True:

                yield from asyncio.sleep(POLL_INTERVAL, loop=loop)
            
                # Check for resize

                # Handle user input
                self._redraw_cmdline(win_cmdline)

                props = self.parse_lines()
                
                if len(props) > 0:
                    # Handle game text
                    #self._redraw_main(win_main, props[0]['text'])
                    self._redraw_main(win_main, self.readbuf.splitlines()[0])

                    # Update sidebar
                    self._redraw_sidebar(win_sidebar)

                # Refresh stdscr
                s_h, s_w = win_sidebar.getmaxyx()
                scr.vline(2, sidebar_width, curses.ACS_VLINE, curses.LINES - 5)
                scr.move(chatline_yx[0] + 1, chatline_yx[1] + len(self.msg) + 2)
                scr.noutrefresh()

                # Do update for all noutrefreshed windows here for speed up
                curses.doupdate()
            
        except KeyboardInterrupt:
            raise

    def parse_lines(self):
        props = []
        for line in self.readbuf.splitlines():
            soup = BeautifulSoup(line, 'html.parser')
            if len(list(soup)) > 0:
                props.append(1)
            #props.append(self.parser.parse(line))
            
        self.readbuf = ''        
        return props
        
    def main(self, scr):
        curses.start_color()
        scr.clear()
        scr.keypad(True)
        scr.nodelay(True)

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.wait([
                asyncio.async(self._update_windows(scr)),
                asyncio.async(self._user_input(scr)),
                asyncio.async(self._server_conn(scr))
            ]))
            loop.close()
        except Exception:
            self.logfile.close()
            

if __name__ == '__main__':

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(threadName)10s %(name)18s: %(message)s',
        stream=sys.stdout,
    )
    
    wraith = Wraith()
    
    # curses auto init
    curses.wrapper(wraith.main)

