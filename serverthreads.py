import threading

class clientThread (threading.Thread):
    def __init__(self, tid, name, socket):
        threading.Thread.__init__(self)
        self.tid = tid
        self.name = tname
        self.socket = socket
    def run(self):

