#!/usr/bin/python

import socket
import threading
import sys
import myirc

# Get and check command line arguments
if len(sys.argv) < 2:
    print "USAGE: " + sys.argv[0] + " <PORT>"

try:
    port = int(sys.argv[1])
except ValueError:
    print "Invalid port number"
    sys.exit(0)

# Create a TCP socket
try:
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    soc = None

# Try to open start server at given host:port
try:
    soc.bind(('', port))
    soc.listen(5)
except socket.error as msg:
    print msg
    soc.close()
    soc = None
except OverflowError:
    soc.close()
    soc = None
    print "Invalid port number"
    sys.exit(0)

# Print error and exit if unsuccessful
if soc is None:
    print "Could not start server at port " + str(port)
    sys.exit(0)

print "Server started at port " + str(port)

# Start server thread
th = myirc.ServerThread(1, "Server", soc)
th.start()

# User input
while (1):
    com = raw_input("Command: ")
    if (com == "quit"):
        th.stop()
        th.join()
        soc.close()
        sys.exit(0)
