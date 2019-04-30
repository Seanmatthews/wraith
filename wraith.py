#!/usr/bin/python3

from collections import deque
from gs3parser import GS3Parser
from queue import Queue
from threading import Thread

import asyncio
import concurrent.futures
import configparser
import curses, curses.panel
import logging
import signal
import string
import sys
import time

import json # FOR DEBUGGING

POLL_INTERVAL = 0.01

class Wraith:
    
    def __init__(self):

        self.cmdbuf = ''
        self.config = configparser.ConfigParser()
        self.msg = ''
        self.readbuf = ''
        self.cmds = deque()
        self.logfile = open('log.txt', 'w')
        self.parser = None
        self.prevcmds = deque()
        self.cmdidx = 0
        self.styles = {}

    async def _user_input(self, scr):
        """
        Monitors user keystrokes and performs actions accordingly.
        """        
        log = logging.getLogger('_user_input')
        log.info('starting')

        try:
            loop = asyncio.get_event_loop()
        
            while True:
                
                await asyncio.sleep(POLL_INTERVAL, loop=loop)
                last = scr.getch()
                if last < 0:
                    pass
                elif last == curses.KEY_BACKSPACE or last == 127:
                    self.msg = self.msg[:-1]
                elif last == curses.KEY_DOWN:
                    self.cmdidx -= 1
                    if self.cmdidx < -1:
                        self.cmdidx = -1
                    if len(self.prevcmds) > 0 and self.cmdidx > -1:
                        self.msg = self.prevcmds[self.cmdidx]
                    else:
                        self.msg = ''
                elif last == curses.KEY_UP:
                    self.cmdidx += 1
                    if self.cmdidx >= len(self.prevcmds):
                        self.cmdidx = len(self.prevcmds) - 1
                    self.msg = self.prevcmds[self.cmdidx]
                elif last == curses.KEY_LEFT:
                    pass
                elif last == curses.KEY_RIGHT:
                    pass
                elif last == curses.KEY_ENTER or last == ord('\n'):
                    self.cmds.append(self.msg)
                    self.msg = ''
                    self.cmdidx = -1
                elif chr(last).isprintable():
                    self.msg += chr(last)

        except KeyboardInterrupt:
            raise

    
    async def _server_conn(self, scr):
        """
        The primary connection to the server. Writes incoming data to the read buffer.
        Writes outgoing data to the write stream.

        Note: This function works pretty well, but should eventually be profiled.
        """
        try:
            loop = asyncio.get_event_loop()
            reader, writer = await asyncio.open_connection('localhost', 8000, loop=loop)
            
            while True:
                await asyncio.sleep(POLL_INTERVAL, loop=loop)

                # Read incoming
                try:
                    linegen = reader.readline()
                    line = await asyncio.wait_for(linegen, timeout=POLL_INTERVAL)
                    self.readbuf += line.decode()
                except asyncio.TimeoutError:
                    pass

                # Write outgoing & add to main window
                if len(self.cmds) > 0:
                    cmd = self.cmds.popleft() + '\n'
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
        #if len(self.parser.text) > 0:
        #    self.logfile.write(str(self.parser.text))
        
        if self.cmdbuf:
            win.addstr(self.cmdbuf)
            self.cmdbuf = ''

        style = self.styles['default']
        for t in self.parser.text:
            if type(t) == int:
                style = t
            else:
                win.addstr(str(t), style)
                #win.attroff(curses.A_BOLD)
                
        if len(self.parser.text) > 0:
            win.addstr('\n')
            
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


    async def _update_windows(self, scr):
        """
        Triggers redrawing of all window elements
        """
        # Create windows
        sidebar_width = 25
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

                await asyncio.sleep(POLL_INTERVAL, loop=loop)
            
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

        
    async def handle_exception(self, coro, loop):
        try:
            await coro
        except Exception:
            self.logfile.write('Exception')
            loop.stop()

            
    def _curses_setup(self):
        """
        """
        self.config.read('styles.ini')

        curses.start_color()
        curses.use_default_colors()

        # Colors
        for key,color in self.config._sections['NORMAL'].items():
            curses.init_pair(int(color), int(color), -1)
            self.styles[key] = curses.color_pair(int(color))

        for key,color in self.config._sections['BOLD'].items():
            curses.init_pair(int(color), int(color), -1)
            self.styles[key] = curses.color_pair(int(color)) | curses.A_BOLD

        # Account for empty string key, which occurs often
        if 'default' in self.styles:
            self.styles[''] = self.styles['default']

        self.parser = GS3Parser(self.styles, self.logfile)

            
    def main(self, scr):
        """
        Starts async loops for updating GUI, monitoring for user input, and managing server connection
        """
        self._curses_setup()
        scr.clear()
        scr.keypad(True)
        scr.nodelay(True)

        try:
            loop = asyncio.get_event_loop()
            update_windows_coro = self.handle_exception(self._update_windows(scr), loop)
            user_input_coro = self.handle_exception(self._user_input(scr), loop)
            server_conn_coro = self.handle_exception(self._server_conn(scr), loop)

            loop.create_task(update_windows_coro)
            loop.create_task(user_input_coro)
            loop.create_task(server_conn_coro)
            loop.run_forever()
        except Exception:
            self.logfile.close()
        #finally:
        #    loop.stop()
            

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

