#!/usr/bin/python
# USAGE:   echo_client_sockets.py <HOST> <PORT> <MESSAGE>
#
# EXAMPLE: echo_client_sockets.py localhost 8000 Hello
import socket
import sys
import time

if len(sys.argv) < 4:
    print "USAGE: echo_client_sockets.py <HOST> <PORT> <USERNAME>";
    sys.exit(0)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host = sys.argv[1]
port = int(sys.argv[2])
s.connect((host,port))

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

