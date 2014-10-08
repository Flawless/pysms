#!/usr/bin/env python
import socket
import sys
import argparse

def createParser():
    parser=argparse.ArgumentParser()
    parser.add_argument('-H','--host', default='mine.dnouglublenie.ru')
    parser.add_argument('-P','--port', default=25111, type=int)
    parser.add_argument('recipient')

    return parser

def send(content,namespace):
    server=(namespace.host,namespace.port)
    recipient = namespace.recipient
    message=b'sms'+recipient.encode()+content
    sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(server)
        sock.sendall(message)
    finally:
        sock.close()

if __name__=='__main__':
    parser = createParser()
    namespace = parser.parse_args()
    content=sys.stdin.buffer.read()

    send(content,namespace)
