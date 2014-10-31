#!/usr/bin/env python3
import serial
import time
import socketserver
import queue
import threading
import logging
import sys
import datetime
import signal
import ast
import traceback
import binascii
import struct
import math
import fl_models
import peewee
import random
import re
from pytz import reference
import pdu
from bouys_func import *
from serial_func import *
from sms import SMS
from device import Device
# SETTINGS
tcp_serv_addr=('', 25112)
serial_ports=['/dev/ttyUSB0', '/dev/ttyUSB4']#, '/dev/ttyACM1', '/dev/ttyACM2']#, ('/dev/ttyACM1','19200'), ('/dev/ttyACM2','19200')]
msg_ok=b'OK'
msg_error=b'ERROR'
period=5
timeout=120
# INIT
STEP = 1.0/2**32
logging.basicConfig(format = '%(levelname)-8s %(process)s %(thread)s: [%(asctime)s] %(message)s', level = logging.DEBUG, filename = '/var/log/pysms.log')
state='idle'
timestamp=time.time()
send_sms_queue=queue.Queue()
recieved_sms_queue=queue.Queue()
tcp_serv_thread=threading.Thread()
devices=[]
def write_hex(bstr):  #hexlify
    try:
        binascii.unhexlify(bstr)
        return bstr
    except binascii.Error:
        return binascii.hexlify(bstr)
def write_hex2(bstr):   #unhexlify
    try:
        binascii.hexlify(bstr)
        return bstr
    except binascii.Error:
        return binascii.unhexlify(bstr)
        
def manage_devices():
    while not recieved_sms_queue.empty():
        sms=recieved_sms_queue.get()
        try:
            logging.info('writing %s to base, good luck...'%sms)
            sms.to_base()
        except Exception as e:
            for frame in traceback.extract_tb(sys.exc_info()[2]):
                fname,lineno,fn,text = frame
                logging.debug("Error in %s on line %d" % (fname, lineno))
            logging.debug('%s %s'%(sys.exc_info()[0], sys.exc_info()[1]))
            recieved_sms_queue.put(sms)
    for dev in devices:
        if dev.status=='crashed' or dev.status=='running' and time.time()-dev.timestamp>300:
            logging.info('Trying to re-initiate device %s'%dev)
            if not dev.sms==None:
                send_sms_queue.put(dev.sms)
                dev.sms=None
            thread=threading.Thread(target=dev.initiate)
            thread.start()
            dev.set_status('running')
        elif dev.status=='sleep':
            if not send_sms_queue.empty():
                sms=send_sms_queue.get(block=False)
                dev.set_sms(sms)
                logging.info('sending sms: %s'%sms)
                thread=threading.Thread(target=dev.send_sms)
                thread.start()
                dev.set_status('running')
            elif time.time()-dev.check_timestamp>30:
                logging.debug('reading sms')
                thread=threading.Thread(target=dev.read_sms)
                thread.start()
                dev.set_status('running')
            
def myexcepthook(exctype, value, traceback):
    if exctype == KeyboardInterrupt:
        logging.info('Terminated by user')
        global state
        state='shutdown'
    else:
        sys.__excepthook__(exctype, value, traceback)
sys.excepthook = myexcepthook

def signal_term_handler(signal, frame):
    global state
    logging.info('recieved sigterm')
    state='shutdown'
signal.signal(signal.SIGTERM, signal_term_handler)

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        logging.info('incoming tcp connection recieved')
        logging.debug('bytes recieved: %s'%self.data)
        sms=SMS(self.data)
        global send_sms_queue
        send_sms_queue.put(sms)
def load_initial_settings(serial_port):
    if not send_command(serial_port, b'ATZ\r'):
        return False 
    if not send_command(serial_port, b'ATE0\r'):
        return False 
    return send_command(serial_port, b'AT+CMGF=0\r')

def idle():
    logging.info('initialization..')
    global state
    global tcp_serv_thread
    global devices
    threading.Thread(target=fl_models.database.connect).start()
    for port in serial_ports:
        try:
            serial_port=serial.Serial(port)
            dev=Device(serial_port)
            devices.append(dev)
            logging.debug('starting init thread')
            dev.set_status('running')
            thread=threading.Thread(target=dev.initiate)
            thread.setDaemon(True)
            thread.start()
            logging.info('device %s initialized'%dev)
        except:
            logging.warning('can not initialize device %s'%serial_port)
    logging.debug('TCP server')
    tcp_serv=socketserver.TCPServer(tcp_serv_addr, MyTCPHandler)
    tcp_serv.allow_reuse_address=True
    tcp_serv_thread=threading.Thread(target=tcp_serv.serve_forever)
    tcp_serv_thread.daemon=True
    tcp_serv_thread.start()
    logging.info('TCP server initialized')
    state='wait'
    while not state=='shutdown':
        manage_devices()
        time.sleep(period)
def shutdown():
    logging.info('shutting down')
    exit()
options={
    'idle':idle,
#    'wait':wait,
    'shutdown':shutdown,
}
#-STATES
def main():
    logging.debug('Current state is: %s'%state)
    options[state]()
if __name__ == "__main__":
    main()


