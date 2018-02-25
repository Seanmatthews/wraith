#!/usr/bin/python3

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
            return

    
    @asyncio.coroutine
    def _server_conn(self, scr):

        # With border below, the refresh is writing the border over text at 0,0
        # because they occupy the same space.
        #    win_chatline.addstr(5, 5, 'helllooooo\n')
        #    win_chatbuffer.addstr(5, 5, 'amd me\n')
        
        #    win_chatline.border()
        #    win_chatbuffer.border()
        #    win_chatline.refresh()
        #    win_chatbuffer.refresh()
        
        try:
            loop = asyncio.get_event_loop()
#            reader, writer = yield from asyncio.open_connection('localhost', 8000, loop=loop)
            
            while True:
                yield from asyncio.sleep(POLL_INTERVAL, loop=loop)

                # Read incoming
 #               line = reader.readline()
#                line = ''
#                if line:
#                    self.readbuf += line.decode()
#                else:
#                    self.readbuf += 'no input this time\n'
                    
                # Write outgoing & add to main window
                if not self.cmds.empty():
                    cmd = self.cmds.get(block=False)
#                    writer.write(cmd.encode())
                    self.readbuf += '> '
                    self.readbuf += cmd
#                    self.readbuf += '\n'

        except KeyboardInterrupt:
            return


    @asyncio.coroutine
    def _update_windows(self, scr):

        # Create windows
#        win_cmdline = scr.derwin(1, 88, 25, 0)
        win_main = scr.derwin(10, 50, 10, 0)

        # Window properties
        win_main.scrollok(True)
        win_main.idlok(True)
        
        try:
            loop = asyncio.get_event_loop()
            while True:

                yield from asyncio.sleep(POLL_INTERVAL, loop=loop)
            
                # Check for resize
                
                # Handle user input
                #                scr.clear()
                #                scr.addstr(self.msg)
                #                scr.refresh()
                #                win_cmdline.clear()
                #                win_cmdline.addstr(self.msg)
                
                # Handle game text
                win_main.addstr(self.readbuf)
                self.readbuf = ''

                # Refresh all
                scr.refresh()
#                win_cmdline.refresh()
                win_main.refresh()
#                scr.move(0, 0)
            
        except KeyboardInterrupt:
            return

        
    def main(self, scr):
        curses.start_color()
        scr.clear()
        scr.keypad(True)
        scr.nodelay(True)
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait([
            asyncio.async(self._update_windows(scr)),
            asyncio.async(self._user_input(scr)),
            asyncio.async(self._server_conn(scr))
        ]))
        loop.close()
    

        # Start threads
#        executor = concurrent.futures.ThreadPoolExecutor(max_workers=3,)
#        loop = asyncio.get_event_loop()
#        try:
#            loop.run_until_complete(self._server_daemon(executor, scr))
#        finally:
#            loop.close()

    
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

