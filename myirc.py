import threading
import socket

class ClientThread(threading.Thread):
    def __init__(self, tid, name, con, addr, so):
        threading.Thread.__init__(self)
        self.tid = tid
        self.name = name
        self.con = con
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

            self.con.send(str(self.tid) + ": " + recv + "\n\r")

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
    def __init__(self, tid, name, soc, so):
        threading.Thread.__init__(self)
        self.tid = tid
        self.name = name
        self.soc = soc
        self.so = so
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
            self.tlist.append(ClientThread(self.tcount, str(addr) + ":" + str(self.tcount), conn, addr, self.so))
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
class IrcServer:
    def __init__(self):
        self.users = []



class IrcUser:
    def __init__(self):


        
