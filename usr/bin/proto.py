#!/usr/bin/env python
import socket
import sys
from struct import pack
import argparse

def createParser():
    parser=argparse.ArgumentParser()
    parser.add_argument('-r','--reciver', type=int, required=True)
    parser.add_argument('-s','--sender', type=int, default=0)

    return parser

def proto(data, namespace):
    sender=namespace.sender
    reciver=namespace.reciver

    length=len(data)+4+4
    proto=bytes([35])+bytes([1])+pack('B',length)+pack('I',sender)+pack('I',reciver)+data    

    return proto

if __name__=='__main__':
    parser = createParser()
    namespace = parser.parse_args()
    data=sys.stdin.buffer.read()

    proto=proto(data, namespace)

    sys.stdout.buffer.write(proto)
