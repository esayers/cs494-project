import threading
import socket
import re
from collections import defaultdict

#
#
# Thread class to handle clients once connected
#
#

class ClientThread(threading.Thread):
    """ Thread handles the connection to a single client and responds to
        commands from it. 
    """
    def __init__(self, tid, con, addr, irc):
        """ Constructor 
        """
        super(ClientThread, self).__init__()
        self.tid = tid
        self.name = ''
        self.con = con
        self.command_pat = re.compile(r'^([a-zA-Z]+|[0-9]{3})')
        self.param_pat = re.compile(r'((?<= \:)[^\0\n\r]*(?=\r\n)|(?<= )[^ :\0\n\r][^ \0\n\r]*)')
	self.addr = addr
        self.irc = irc
        self._stop = threading.Event()

    def run(self):
        """ Runs when the thread is started, handles communication between
            server and a single client.
        """

        self.con.settimeout(0.2)

        while(self.isRunning()):
            try:
                recv = self.con.recv(4096)
            except: continue

            if recv == '':
                break

            command = self.command_pat.match(recv)
            params = self.param_pat.findall(recv)

            if (command != None):
                command = command.group(1)

            if command == "CON":
                if len(params) < 1:
                    try:
                        raise MissingParam()
                    except MissingParam as e:
                        self.con.send(e.retStr)
                try:
                    if self.name != '':
                        self.irc.rename_user(self.name, params[0])
                    else:
                        self.irc.add_user(params[0], self.con)
                    self.con.send("301 :Connected as " + params[0] + "\r\n")
                    self.name = params[0]
                except (NameUnavailable, NameInvalid, ServerFull, MissingParam) as e:
                    self.con.send(e.retStr)

            elif command == "QUIT":
                break

            elif command == "JOIN":
                if len(params) < 1:
                    try:
                        raise MissingParam()
                    except MissingParam as e:
                        self.con.send(e.retStr)

                for room in params:
                    try:
                        self.irc.join_room(self.name, room)
                        self.con.send("321 :" + room + "\r\n")
                    except (MissingParam, RoomInvalid, RoomUnavailable, NotConnected) as e:
                        self.con.send(e.retStr)
            elif command == "LEAVE":
                if len(params) < 1:
                    try:
                        raise MissingParam()
                    except MissingParam as e:
                        self.con.send(e.retStr)

                for room in params:
                    try:
                        self.irc.leave_room(self.name, room)
                        self.con.send("322 :Left " + room + "\r\n")
                    except (RoomInvalid, RoomUnknown) as e:
                        self.con.send(e.retStr)
            elif command == "LIST":
                rooms = self.irc.list()
                reply = "221"

                for room in rooms:
                        reply += " " + room
                reply += "\r\n"
                self.con.send(reply)
            elif command == "WHOROOM":
                if len(params) < 1:
                    try:
                        raise MissingParam()
                    except MissingParam as e:
                        self.con.send(e.retStr)

                try:
                    names = self.irc.who_room(params[0])
                    reply = "212 " + params[0]
                    for name in names:
                        reply += " " + name
                    reply += "\r\n"
                    self.con.send(reply)
                except (RoomInvalid, RoomUnknown) as e:
                    self.con.send(e.retStr)
            elif command == "SEND":
                if len(params) < 2:
                    try:
                        raise MissingParam()
                    except MissingParam as e:
                        self.con.send(e.retStr)

                if self.name == '':
                    try:
                        raise NotConnected
                    except NotConnected as e:
                        self.con.send(e.retStr)

                for dst in params[0:-1]:
                    try:
                        self.irc.send(self.name, dst, params[-1])
                    except (RoomInvalid, NameInvalid, NameUnknown, RoomUnknown) as e:
                        self.con.send(e.retStr)
            else:
                self.con.send("432 :Command not valid\r\n")

        self.irc.rem_user(self.name)
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
        super(ServerThread, self).__init__()
        self.tid = tid
        self.name = name
        self.soc = soc
        self.irc = IrcServer(2,2)
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
            self.tlist.append(ClientThread(self.tcount, conn, addr, self.irc))
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
    """ Maintains server state and performs related functions
    """
    def __init__(self, maxusers, maxrooms):
        """ Constructor
        """
        self.users = defaultdict()
        self.rooms = defaultdict()
        self.lock = threading.RLock()
        self.maxusers = maxusers
        self.maxrooms = maxrooms

    def add_user(self, name, con):
        """ Adds a user to the server or throws an exception if unable to do so.
        """
        if re.match("^[a-zA-Z]\w{0,8}$", name) == None:
            raise NameInvalid(name)

        with self.lock:
            if name in self.users:
                raise NameUnavailable

            if len(self.users) >= self.maxusers:
                raise ServerFull
        
            self.users[name] = con

    def rem_user(self, name):
        """ Removes a user from the server
        """
        with self.lock:
            for room in self.rooms:
                try:
                    self.rooms[room].remove(name)
                except:
                    pass
            try:
                self.users.pop(name, None)
            except:
                pass

    def rename_user(self, old_name, new_name):
        """ Renames a user or throws an exception if unable to do so.
        """
        if re.match("^[a-zA-Z]\w{0,8}$", new_name) == None:
            raise NameInvalid(new_name)

        with self.lock:
            if new_name in self.users:
                raise NameUnavailable

            con = self.users.pop(old_name, None)
            if con == None:
                raise NotConnected

            self.users[new_name] = con
            
            # Re-join rooms as new name
            for room in self.rooms:
                if old_name in self.rooms[room]:
                    self.rooms[room].remove(old_name)
                    self.rooms[room].append(new_name)

    def join_room(self, name, room):
        """ Adds a user to a single room.
        """

        # room must start with # and be no more than 9 characters
        if re.match("^#\w{0,8}$", room) == None:
            raise RoomInvalid(room)

        with self.lock():
            if name not in self.users:
                raise NotConnected
        
            if room not in self.rooms:
                if len(self.rooms) >= self.maxrooms:
                    raise RoomUnavailable(room)
                self.rooms[room] = []

            if name not in self.rooms[room]:
                self.rooms[room].append(name)
        
    def leave_room(self, name, room):
        """ Removes a user from a single room.
        """
        with self.lock():
            if name not in self.users:
                raise NotConnected

            if room not in self.rooms:
                raise RoomUnknown(room)

            # No difference if user was removed or if user was never in the room.
            try:
                self.rooms[room].remove(name)
            except:
                pass
            
            # Remove room if it is empty
            if len(self.rooms[room]) == 0:
                self.rooms.pop(room, None)

    def list(self):
        """ Returns a list of all the rooms on the server
        """

        rooms = []
        with self.lock:
            for room in self.rooms:
                rooms.append(room)

        return rooms

    def who_room(self, room):
        """ Returns a list of users in the given room
        """
        
        # room must start with # and be no more than 9 characters
        if re.match("^#\w{0,8}$", room) == None:
            raise RoomInvalid(room)

        with self.lock:
            if room not in self.rooms:
                raise RoomUnknown(room)

            if room in self.rooms:
                return self.rooms[room]
            else:
                return []

    def send(self, src, dst, msg):
        if dst[0] == '#':
            if re.match("^#\w{0,8}$", dst) == None:
                raise RoomInvalid(dst)
            with self.lock:
                if dst not in self.rooms:
                    raise RoomUnknown(dst)
                for name in self.rooms[dst]:
                    self.users[name].send("SEND " + src + " :" + msg + "\r\n")
        else:
            if re.match("^[a-zA-Z]\w{0,8}$", dst) == None:
                raise NameInvalid(dst)
            with self.lock:
                if dst not in self.users:
                    raise NameUnknown(dst)
                self.users[dst].send("SEND " + src + " :" + msg + "\r\n")


#
# Custom Exceptions
#

class NameUnavailable(Exception):
    def __init__(self):
        self.retStr = "412 :Name already in use\r\n"

class NameInvalid(Exception):
    def __init__(self, name):
        self.retStr = "411 :" + name + " is not a valid username\r\n"

class NameUnknown(Exception):
    def __init__(self, name):
        self.retStr = "413 :User " + name + " not found\r\n"

class MissingParam(Exception):
    pass

class ServerFull(Exception):
    def __init__(self):
        self.retStr = "404 :Server Full\r\n"

class MissingParam(Exception):
    def __init__(self):
        self.retStr = "431 : Not enough parameters were provided\r\n"

class RoomInvalid(Exception):
    def __init__(self, name):
        self.retStr = "421 :" + name + " is not a valid room name\r\n"

class RoomUnavailable(Exception):
    def __init__(self, name):
        self.retStr = "422 :Unable to create room " + name + "\r\n"

class RoomUnknown(Exception):
    def __init__(self, name):
        self.retStr = "423 :There is no room named " + name + " on this server\r\n"

class NotConnected(Exception):
    def __init__(self):
        self.retStr = "401 :Not connected\r\n"
