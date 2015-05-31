import threading
import socket
import re

#
#
# Thread class to handle clients once connected
#
#

class ClientThread(threading.Thread):
    def __init__(self, tid, name, con, addr, so):
        threading.Thread.__init__(self)
        self.tid = tid
        self.name = name
        self.con = con
        self.command_pat = re.compile(r'^([a-zA-Z]+|[0-9]{3})')
        self.param_pat = re.compile(r'((?<= \:)[^\0\n\r]*(?=\r\n)|(?<= )[^ :\0\n\r][^ \0\n\r]*)')
	self.addr = addr
        self.so = so
        self._stop = threading.Event()

    def run(self):
        self.con.settimeout(0.2)

        while(self.isRunning()):
            try:
                recv = self.con.recv(10000)
            except: continue

            if recv == '':
                break

            command = self.command_pat.match(recv)
            params = self.param_pat.findall(recv)
            print repr(recv)
            print command.group(1)
            for p in params:
                print p

        self.con.shutdown(socket.SHUT_RDWR)
        self.con.close()

    def stop(self):
        self._stop.set()

    def isRunning(self):
        return not self._stop.isSet()

#    
#
# Thread class to handle clients connecting to the server
#
#

class ServerThread(threading.Thread):
    def __init__(self, tid, name, soc):
        threading.Thread.__init__(self)
        self.tid = tid
        self.name = name
        self.soc = soc
        self.irc = IrcServer()
        self._stop = threading.Event()
        self.tlist = []
        self.tcount = 0

    def run(self):
        self.soc.settimeout(0.2)

        # Accept connections until stop() is called
        while(self.isRunning()):

            # Cleanup tlist
            for th in self.tlist:
                if (not th.is_alive()):
                    self.tlist.remove(th)

            # Accept connection if pending
            try:
                conn, addr = self.soc.accept()
            except: continue

            # Add new connection to list and start it
            self.tcount += 1
            self.tlist.append(ClientThread(self.tcount, "", conn, addr, self.irc))
            self.tlist[-1].start()

        # Stop each connection then wait for it to finish
        for th in self.tlist:
            th.stop()
            th.join()

    def stop(self):
        self._stop.set()

    def isRunning(self):
        return not self._stop.isSet()

#
#
# 
#
#

class IrcServer:
    def __init__(self):
        self.users = []
        self.rooms = []

    def add_user(name):
        if name in self.users:
            return False
        
        self.users.append(name)
        return True
