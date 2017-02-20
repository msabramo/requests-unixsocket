#!/usr/bin/env python

# Example of interacting with a [abstract namespace
# socket](https://utcc.utoronto.ca/~cks/space/blog/python/AbstractUnixSocketsAndPeercred)
#
# Since abstract namespace sockets are specific to Linux, this program will
# only work on Linux.

import os
import socket

import requests_unixsocket


def handle_response():
    # Listens on an abstract namespace socket and sends one HTTP response
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind('\0test_socket')
    sock.listen(1)
    client_sock, addr = sock.accept()
    client_sock.recv(1024)
    client_sock.sendall(b'HTTP/1.0 200 OK\r\n')
    client_sock.sendall(b'Content-Type: text/plain\r\n\r\n')
    client_sock.sendall(b'Hello world!')


if os.fork() == 0:        # child
    handle_response()
else:                     # parent
    try:
        session = requests_unixsocket.Session()
        res = session.get('http+unix://\0test_socket/get')
        print(res.text)
    finally:
        os.wait()
