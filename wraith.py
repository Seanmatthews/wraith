#!/usr/bin/python3

from collections import deque
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

import json

POLL_INTERVAL = 0.01

class Wraith:
    
    def __init__(self):

        self.cmdbuf = ''
        self.msg = ''
        self.readbuf = ''
        self.cmds = deque()
        self.logfile = open('log.txt', 'w')
        self.parser = GS3Parser(self.logfile)
        self.prevcmds = deque()
        self.cmdidx = 0

    @asyncio.coroutine
    def _user_input(self, scr):
        """
        Monitors user keystrokes and performs actions accordingly.
        """
        
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
                    self.cmdidx -= 1
                    if self.cmdidx < 0:
                        self.cmdidx = 0
                    self.msg = self.prevcmds[self.cmdidx]
                    pass
                elif last == curses.KEY_DOWN:
                    self.cmdidx += 1
                    if self.cmdidx >= len(self.prevcmds):
                        self.cmdidx = len(self.prevcmds) - 1
                    self.msg = self.prevcmds[self.cmdidx]
                elif last == curses.KEY_LEFT:
                    pass
                elif last == curses.KEY_RIGHT:
                    pass
                elif last == curses.KEY_ENTER or last == ord('\n'):
                    self.msg += '\n'
                    self.cmds.append(self.msg)
                    self.msg = ''
                    self.cmdidx = 0
                elif chr(last).isprintable():
                    self.msg += chr(last)

        except KeyboardInterrupt:
            raise

    
    @asyncio.coroutine
    def _server_conn(self, scr):
        """
        The primary connection to the server. Writes incoming data to the read buffer.
        Writes outgoing data to the write stream.

        Note: This function works pretty well, but should eventually be profiled.
        """
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
                if len(self.cmds) > 0:
                    cmd = self.cmds.popleft()
                    writer.write(cmd.encode())
                    self.cmdbuf += '> '
                    self.cmdbuf += cmd + '\n'
                    self.prevcmds.appendleft(cmd)

        except KeyboardInterrupt:
            raise


    def _redraw_main(self, win):
        """
        Redraw main window with supplied data
        """
        if self.cmdbuf:
            win.addstr(self.cmdbuf)
            self.cmdbuf = ''
        if self.parser.text:
            win.addstr(self.parser.text + '\n')
        if (bool(self.parser.spells)):
            win.addstr(json.dumps(self.parser.spells) + '\n')
        if (bool(self.parser.stats)):
            win.addstr(json.dumps(self.parser.stats) + '\n')
        #win.addstr(self.parser.text)
        win.noutrefresh()

        
    def _redraw_cmdline(self, win):
        """
        Redraws the text entry bar as the user types
        """
        h, w = win.getmaxyx()
        win.clear()
        win.border()
        win.addstr(1, 2, self.msg)
        win.noutrefresh()

        
    def _redraw_sidebar(self, win):
        """
        Redraws sidebar elements
        """
        win.noutrefresh()


    @asyncio.coroutine
    def _update_windows(self, scr):
        """
        Triggers redrawing of all window elements
        """

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

                self.logfile.write(self.readbuf)
                #self.parser.text = self.readbuf
                
                for line in self.readbuf.splitlines():
                    self.parser.parse(line)
                        
                # Handle user input
                self._redraw_cmdline(win_cmdline)

                # Update main window
                self._redraw_main(win_main)
                
                # Update sidebar
                self._redraw_sidebar(win_sidebar)

                # Refresh stdscr
                s_h, s_w = win_sidebar.getmaxyx()
                scr.vline(2, sidebar_width, curses.ACS_VLINE, curses.LINES - 5)
                scr.move(chatline_yx[0] + 1, chatline_yx[1] + len(self.msg) + 2)
                scr.noutrefresh()

                # Do update for all noutrefreshed windows here for speed up
                curses.doupdate()

                self.parser.clear_vars()
                self.readbuf = ''
            
        except KeyboardInterrupt:
            raise

        
    def main(self, scr):
        """
        Starts async loops for updating GUI, monitoring for user input, and managing server connection
        """
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

