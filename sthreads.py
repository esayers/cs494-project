import threading

class ClientThread(threading.Thread):
    def __init__(self, tid, name, con, addr):
        threading.Thread.__init__(self)
        self.tid = tid
        self.name = name
        self.con = con
	self.addr = addr
        self._stop = threading.Event()

    def run(self):
        while(self.isRunning()):
            self.con.send(str(self.tid) + ": " + self.con.recv(10000))

    def stop(self):
        self._stop.set()

    def isRunning(self):
        return not self._stop.isSet()

# Thread class to handle clients connecting to the server
class ServerThread(threading.Thread):
    def __init__(self, tid, name, soc):
        threading.Thread.__init__(self)
        self.tid = tid
        self.name = name
        self.soc = soc
        self._stop = threading.Event()
        self.tlist = []

    def run(self):
        self.soc.settimeout(0.2)

        # Accept connections until stop() is called
        while(self.isRunning()):
            try:
                conn, addr = self.soc.accept()
            except: continue

            # Add new connection to list and start it
            self.tlist.append(ClientThread(len(self.tlist) + 1, addr, conn, addr))
            self.tlist[-1].start()

        # Stop each connection then wait for it to finish
        for th in self.tlist:
            th.stop()
            th.join()

    def stop(self):
        self._stop.set()

    def isRunning(self):
        return not self._stop.isSet()

    




        
