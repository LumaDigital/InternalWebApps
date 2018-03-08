import os
import socket
import threading
import sys
from time import sleep
import json
import ast
import logging


class LumaCommServer:

    data = []
    datadict = {}

    host = "0.0.0.0"
    port = 9091

    def __init__(self, host='0.0.0.0', port=9091):
        self.host = host
        self.port = port
        return

    def send_update(self, msg):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # Connect to server and send data
            sock.connect((self.host, self.port))
            sock.sendall(msg)

            # Receive data from the server and shut down
            received = sock.recv(1024)

            # print "Sent:     {}".format(msg)
            # print "Received: {}".format(received)

        except IOError as e:
            logging.warning("I/O error({0}): {1}".format(e.errno, e.strerror));
        finally:
            sock.close()

    def start_server(self):
        thread = threading.Thread(target=self.server_listen, args=())
        thread.daemon = True
        thread.start()

    def server_listen(self):

        host = '0.0.0.0'
        port = 9091
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(1)

        while True:

            conn, address = s.accept()
            # print 'Connected by', address

            while True:
                data = conn.recv(1024)
                if not data:
                    conn.close()
                    break
                conn.send(data)
                self.update_server_data(data)

    def update_server_data(self, newdata):
        # print newdata
        d = ast.literal_eval(newdata)
        self.datadict[d['IP']] = d

    def format_for_table(self):
        data = []
        # print self.datadict
        for key, value in self.datadict.iteritems():
            data.append(value)
        return data
