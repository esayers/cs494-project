#!/usr/bin/python
# USAGE:   echo_client_sockets.py <HOST> <PORT> <MESSAGE>

# EXAMPLE: echo_client_sockets.py localhost 8000 Hello
import socket
import sys
import time
import Queue 
import myircclient
import time
import re

if len(sys.argv) < 4:
    print "USAGE: echo_client_sockets.py <HOST> <PORT> <USERNAME>";
    sys.exit(0)

host = sys.argv[1]
name = sys.argv[3]

try:
    port = int(sys.argv[2])
except ValueError:
    print "Invalid port number"
    sys.exit(0)

# Create a TCP socket
try:
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    soc = None

soc.settimeout(3.0)

try:
    soc.connect((host,port))
except:
    print "Unable to connect to server"
    sys.exit(0)

cmd_q = Queue.Queue(maxsize=0)
msg_q = Queue.Queue(maxsize=0)
rcv_q = Queue.Queue(maxsize=0)

irc = myircclient.IrcClient(soc, cmd_q, msg_q)
cmdTh = myircclient.CmdThread(soc, cmd_q)
cmdTh.setDaemon(True)
rcvTh = myircclient.RcvThread(soc, rcv_q)
rcvTh.setDaemon(True)
pcsTh = myircclient.PcsThread(msg_q, rcv_q, irc)
pcsTh.setDaemon(True)
cmdTh.start()
rcvTh.start()
pcsTh.start()

irc.connect(name)

while(1):
    raw_cmd = raw_input("Cmd > ")
    
    cmd = re.match("^/(\w+)", raw_cmd)
    par = re.findall("(?<= )([^-\\s]+)", raw_cmd)

    if cmd == None:
        continue

    
    cmd = cmd.group(1).lower()

    if cmd == "quit":
        cmd_q.put("QUIT")
        soc.close()
        break
    elif cmd == "join":
        cmd_q.put("JOIN " + par[0])

"""
while(1):
    command = raw_input("Send: ")
    if (command == "quit"):
        s.close
        break
    s.send(command + "\r\n")
    s.settimeout(1.0)
    try:
        data = s.recv(4096)
    except:
        print "No response before timeout"
        continue
"""
