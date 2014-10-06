#!/usr/bin/env python
import socket
import sys
server=('localhost',25111)
print(sys.argv)
if len(sys.argv)<2:
    print('please, define message recipient')
    exit()
recipient=sys.argv[1]
content=sys.stdin.read()
message=b'sms'+recipient.encode()+content.encode()
print('sending: %s'%message)
sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
def send(server,message):
    try:
        sock.connect(server)
        #sock.sendall(b'sms+79313583162'+content)
        #sock.sendall(b'sms+79218654765jabyi')
        #sock.sendall(b'sms+79217544311jabui')
        sock.sendall(message)
        print('success')
    finally:
        sock.close()

send(server,message)

#import struct

#content = bytes([35]) + bytes([1]) + bytes([42]) + struct.pack('I',5)  + struct.pack('I',345) + bytes([1]) + struct.pack("Q",1000000000) + struct.pack('d',61.12414) + struct.pack('d',60.3123) + struct.pack('H',99) + struct.pack('H', 50) + struct.pack('B', 5) + bytes([00]) + bytes([00]) + bytes([00]) + bytes([00]) # '#' + version + length (11 byte) + receiver id + sender id + body + salttry:
#content=struct.pack('i',452961536)*35
#print(content)
#print(len(content))
