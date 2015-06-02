#!/usr/bin/python
# USAGE:   echo_client_sockets.py <HOST> <PORT> <MESSAGE>
#
# EXAMPLE: echo_client_sockets.py localhost 8000 Hello
import socket
import sys
import time

if len(sys.argv) < 3:
    print "USAGE: echo_client_sockets.py <HOST> <PORT>";
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
        data = s.recv(1000000)
    except:
        print "No response before timeout"
        continue

    print repr(data)


#s.send(sys.argv[3] + "\r\n")
#data = s.recv(10000000)
#print data
#print 'received', len(data), ' bytes'
#s.close()
