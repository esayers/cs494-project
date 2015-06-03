import socket
import sys
import Queue
import threading
import re


class IrcClient():
    """ Handles client state and implements client functionality
    """
    def __init__(self, con, cmd_q, msg_q):
        self.con = con
        self.cmd_q = cmd_q
        self.msg_q = msg_q
        self.connected = False
        self.name = ''
        self.rooms = []
        self.cmd_pat = re.compile(r'^([a-zA-Z]+|[0-9]{3})')
        self.par_pat = re.compile(r'((?<= \:)[^\0\n\r]*(?=\r\n)|(?<= )[^ :\0\n\r][^ \0\n\r]*)')

    def connect(self, name):
        msg = "CON " + name
        self.cmd_q.put(msg)

    def join(self, room):
        msg = "JOIN " + name
        self.cmd_q.put(msg)

    def process_msg(self, msg):
        cmd = self.cmd_pat.match(msg)
        par = self.par_pat.findall(msg)

        if cmd != None:
            cmd = cmd.group(1)

        if cmd == "301":
            if len(par) < 1:
                return
            
            name = re.findall("Connected as (\w+)", par[0])
            if name != []:
                self.name = name[0]
                self.msg_q.put("Connected as " + self.name)

        elif cmd == "SEND":
            if len(par) != 2:
                return

            self.msg_q.put(par[0] + ": " + par[1])

        elif cmd == "321":
            if len(par) < 1:
                return

            self.msg_q.put("Joined " + par[0])



class CmdThread(threading.Thread):
    """ Processes requsts for outgoing messages
    """
    def __init__(self, con, q):
        super(CmdThread, self).__init__()
        self.q = q
        self.con = con
        self._stop = threading.Event()

    def run(self):
        while (self.isRunning()):
            try:
                cmd = self.q.get(False)
                self.con.send(cmd + "\r\n")
                self.q.task_done()
            except: pass

    def stop(self):
        self._stop.set()

    def isRunning(self):
        return not self._stop.isSet()

class RcvThread(threading.Thread):
    """ Recieves messages from server
    """
    def __init__(self, con, q):
        super(RcvThread, self).__init__()
        self.q = q
        self.con = con
        self._stop = threading.Event()

    def run(self):
        self.con.settimeout(0.2)
        while(self.isRunning()):
            try:
                rcv = self.con.recv(4096)
                self.q.put(rcv)
            except: pass

    def stop(self):
        self._stop.set()

    def isRunning(self):
        return not self._stop.isSet()

class PcsThread(threading.Thread):
    """ Processes the msg and rcv queues
    """
    def __init__(self, msg_q, rcv_q, irc):
        super(PcsThread, self).__init__()
        self.msg_q = msg_q
        self.rcv_q = rcv_q
        self.irc = irc
        self._stop = threading.Event()

    def run(self):
        while(self.isRunning()):
            try:
                msg = self.msg_q.get(False)
                print
                print msg
                sys.stdout.write("Cmd > ")
                sys.stdout.flush()
            except:
                pass
            try:
                rcv = self.rcv_q.get(False)
                self.irc.process_msg(rcv)
                self.rcv_q.task_done()
            except:
                pass

    def stop(self):
        self._stop.set()

    def isRunning(self):
        return not self._stop.isSet()
