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
#sys.path.append('/home/flawless/projects/work/fletcontrol/pySMS/lib/python/')
import fl_models
import peewee
import random
import re
from pytz import reference
import pdu
# SETTINGS
tcp_serv_addr=('', 25111)
serial_ports=['/dev/ttyUSB0', '/dev/ttyUSB3']#, '/dev/ttyACM1', '/dev/ttyACM2']#, ('/dev/ttyACM1','19200'), ('/dev/ttyACM2','19200')]
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
def parse_alarm_mask(alarm_bytes):
    alarm_bytes=int(binascii.hexlify(alarm_bytes),16)
    alarms = {}
    alarms["lightings"]      = alarm_bytes & 0b01000000 > 0
    alarms["gsm"]            = alarm_bytes & 0b00100000 > 0
    alarms["gps"]            = alarm_bytes & 0b00010000 > 0
    alarms["charge"]         = alarm_bytes & 0b00001000 > 0
    alarms["tilt"]           = alarm_bytes & 0b00000100 > 0
    alarms["hit"]            = alarm_bytes & 0b00000010 > 0
    alarms["position_shift"] = alarm_bytes & 0b00000001 > 0
    return alarms
def from_our_format2float(array):
    i = array[:2]
    f = array[2:]
    i = struct.unpack('h', i)[0]
    f = struct.unpack('I', f)[0]
    return i + math.copysign(f*STEP,i)
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
class Device():
    def __init__(self, serial_port, status='crashed'):
        self.serial_port = serial_port
        self.status  = status
        self.thread = ''
        self.sms    = None
        self.check_timestamp = time.time()-1000
        self.sm = []
    def __repr__(self):
        return self.serial_port.port
    def set_sms(self, sms):
        self.sms=sms
    def set_status(self, status):
        if status=='crashed':
            logging.warning('device: %s status: %s'%(self,status))
        else:
            logging.debug('device: %s status: %s'%(self,status))
        self.timestamp=time.time()
        self.status=status
    def initiate(self):
        try:
            logging.debug('serial ..')
            self.serial_port.close()
            self.serial_port.open()
            logging.info('serial .. OK')
            logging.debug('initial settings..')
            if load_initial_settings(self.serial_port):
                logging.info('initial settings .. OK')
            else:
                raise Exception('Init settings failed')
            self.get_sm_size()
            self.set_status('sleep')
        except Exception as e:
            for frame in traceback.extract_tb(sys.exc_info()[2]):
                fname,lineno,fn,text = frame
                logging.error("Error in %s on line %d" % (fname, lineno))
            logging.error('%s %s'%(sys.exc_info()[0], sys.exc_info()[1]))
            self.set_status('crashed')
    def send_sms(self,pdu=True):
        try:
            logging.info('sending %s'%self)
            if pdu:
                data,length=pdu.sms_to_pdu(self.recipient.decode(),self.content.decode())
                if not send_command(self.serial_port, b'AT+CMGS'+length+b'\r'):
                    raise Exception('message was not sended')
                if not send_command(self.serial_port,data +bytes([26])):
                    raise Exception('message was not sended')
            else:
                if not send_command(self.serial_port, b'AT+CMGS="' + self.sms.recipient + b'"\r', b'>'):
                    raise Exception('message was not sended')
                if not send_command(self.serial_port,self.sms.content +bytes([26])):
                    raise Exception('message was not sended')
                logging.info('sended %s sucessful'%self)
                self.set_sms(None)
                self.set_status('sleep')
        except Exception as e:
            for frame in traceback.extract_tb(sys.exc_info()[2]):
                fname,lineno,fn,text = frame
                print("Error in %s on line %d" % (fname, lineno))
            logging.debug('%s %s'%(sys.exc_info()[0], sys.exc_info()[1]))
            self.set_status('crashed')
    def read_sms(self):
        try:
            sm=self.check_sm()
            if not len(sm)==0:
                global recieved_sms_queue
                logging.info('recieved %d new messages'%len(sm))
            else:
                logging.debug('no new messages recieved')
            for i in sm:
                end_of_command=i+b'\r'
                command=b'AT+CMGR='+end_of_command
                answer=send_command(self.serial_port,command,None)
                content=answer.split(b'\r\n')[2]
                content,recipient=pdu.pdu_to_sms(content.decode())
                command=b'AT+CMGD='+end_of_command
                send_command(self.serial_port,command)
                if content == None and recipient == None:
                    continue
                #content=binascii.unhexlify(content)
                sms=SMS(recipient=recipient, content=content, id=i)
                recieved_sms_queue.put(sms)
                logging.info('recieved message %s'%sms)
            self.set_status('sleep')
            self.check_timestamp=time.time()
        except Exception as e:
            for frame in traceback.extract_tb(sys.exc_info()[2]):
                fname,lineno,fn,text = frame
                logging.error("Error in %s on line %d" % (fname, lineno))
            logging.error('%s %s'%(sys.exc_info()[0], sys.exc_info()[1]))
            self.set_status('crashed')
    def get_sm_size(self):
        command=b'AT+CPMS?\r'
        answer=send_command(self.serial_port,command, None)
        sm_size=int(answer.split(b'"SM"')[1].split(b',')[1])
        for i in range(sm_size):
               self.sm.append(None)
        return 0
    def check_sm(self):
        command=b'AT+CMGD=?\r'
        template=b'\n+CMGD: '
        answer=send_command(self.serial_port,command, None)
        answer=answer[1+answer.find(b'(',answer.find(template)):answer.find(b')',answer.find(template))]
        sm=answer.split(b',')
        if sm[0]==b'':
            sm=[]
        return sm
class SMS():
    def __init__(self, *args, **kwargs):
        self.byte_message=[]
        if 'recipient' in kwargs and 'content' in kwargs:
            self.recipient=kwargs.get('recipient')
            self.content=kwargs.get('content')
            if 'id' in kwargs:
                self.id=kwargs.get('id')
            else:
                self.id=None
        elif args[0][:3]==b'sms':
            self.recipient=args[0][3:15]
            self.content=args[0][15:]
        else:
            logging.debug('can not construct message from %s'%args[0])
        logging.info('message constructed: %s'%self)
    def __repr__(self):
        return '%s %s'%(self.recipient,self.content)
    def __str__(self):
        return 'recipient: %s\n content: %s'%(self.recipient,self.content)    
    def to_base(self):
        logging.debug(self.content)
        try:
            data=binascii.unhexlify(self.content)
            length=data[2]
            proto=[data[0],data[1],data[2],data[3:7],data[7:11],data[11:3+length]]#data[11:3+length-2],data[3+length-2:3+length]]
            logging.debug(proto)
            if not proto[0]==35:
                raise Exception('Proto error')
            if not proto[1]==1:
                raise Exception('Proto error')
            #sender=struct.unpack('I',proto[3])[0]
            sender=fl_models.NsControlBouy.get(fl_models.NsControlBouy.sim_number==binascii.unhexlify(self.recipient).decode()).id
            #reciver=struct.unpack('I',proto[4])[0]
            body=[proto[5][0],proto[5][1:]]
            logging.debug(body)
            mes_id=body[0]
            mes_content=body[1]
            if mes_id==1:
                logging.debug('Recieved #1 mesage')
                data=[mes_content[:8],mes_content[8:14],mes_content[14:20],mes_content[20:22],mes_content[22:24],mes_content[24],mes_content[25],mes_content[26:28]]
                logging.debug(data)
                time=datetime.datetime.fromtimestamp(struct.unpack('q',data[0])[0])
                lon=from_our_format2float(data[1])
                lat=from_our_format2float(data[2])
                #lon=struct.unpack('d',data[1])[0]
                #lat=struct.unpack('d',data[2])[0]
                brightness=struct.unpack('H',data[3])[0]
                bat_charge=struct.unpack('H',data[4])[0]
                inclination=data[5]
                temp=data[6]
                alarm_reg=data[7]
                alarms=parse_alarm_mask(alarm_reg)
                logging.info(alarms)
                logging.info('sender %s time %s lat %s lon %s brightness %s bat_charge %s inclination %s temp %s alarm_reg %s'%(sender,time,lat,lon,brightness,bat_charge,inclination,temp,alarm_reg))
                new_data=fl_models.NsControlBouymessage(blink_mode=1,bouy=sender,time=time,lat=lat,lon=lon,brightness=brightness,charge=bat_charge,inclination=inclination,gps_problem=alarms['gps'],drift_alarm=alarms['position_shift'],hit_sensor=alarms['hit'],lighting_alarm=alarms['lightings'])
                try:
                    res=new_data.save()
                except peewee.OperationalError:
                    logging.warning('Connection to base broken..reconnecting')
                    fl_models.database.close()
                    fl_models.database.connect()
                logging.debug(res==1)
                try:
                    last_message=fl_models.NsControlBouylaststate.get(fl_models.NsControlBouylaststate.bouy==sender)
                    last_message.message=new_data.id
                except fl_models.NsControlBouylaststate.DoesNotExist:
                    logging.warning('no previus messages from bouy %s'%sender)
                    last_message=fl_models.NsControlBouylaststate(bouy=sender,message=new_data.id)
                #logging.debug(last_message)
                try:
                    res=last_message.save()
                except peewee.IntegrityError:
                    logging.warning("Integrity error peewee")
                    time.sleep(3)
                logging.debug(res==1)
            elif mes_id==4:
                logging.debug('Recieved #4 mesage')
                data=[mes_content[:6],mes_content[6:12]]
                lon=from_our_format2float(data[0])
                lat=from_our_format2float(data[1])
                logging.info('sender %s base_lat %s base_lon %s'%(sender,lat,lon))
                new_data=fl_models.NsControlBouy.get(fl_models.NsControlBouy.id==sender)
                new_data.base_lat=lat
                new_data.base_lon=lon
                logging.debug(new_data.base_lat)
                try:
                    res=new_data.save()
                    logging.debug(res==1)
                except peewee.OperationalError:
                    logging.warning('Connection to base broken..reconnecting')
                    fl_models.database.close()
                    fl_models.database.connect()
            else:
                logging.debug('message id not 1')
        except Exception as e:
            for frame in traceback.extract_tb(sys.exc_info()[2]):
                fname,lineno,fn,text = frame
                print("Error in %s on line %d" % (fname, lineno))
            logging.error('%s %s'%(sys.exc_info()[0], sys.exc_info()[1]))

    # def make_pdu(self):
    #     # http://hardisoft.ru/soft/otpravka-sms-soobshhenij-v-formate-pdu-teoriya-s-primerami-na-c-chast-1/
    #     PDU_type=b'\x11'
    #     TP_MR=b'\x00'
    #     TP_DA=bytes([len(self.recipient)-1])+b'\x91'+self.get_pdu_recipient()
    #     TP_PID=b'\x00'
    #     TP_DCS=b'\x00'
    #     TP_VP=b'\xaa'
    #     # TP_SCTS=self.get_pdu_timestamp()
    #     TP_UD=binascii.unhexlify(b'E8329BFD4697D9EC37')#self.content
    #     TP_UDL=b'\x0a'#bytes([len(TP_UD)])
    #     TPDU=PDU_type + TP_MR + TP_DA + TP_PID + TP_DCS + TP_VP + TP_UDL + TP_UD
    #     SCA=b'\x00'
    #     SMS=SCA+TPDU
    #     return binascii.hexlify(SMS)
    # def get_pdu_timestamp(self):
    #     date=datetime.datetime.today()
    #     year=  bytes([date.year%100])
    #     month= bytes([date.month])
    #     day=   bytes([date.day])
    #     hour=  bytes([date.hour])
    #     minute=bytes([date.minute])
    #     second=bytes([date.second])
    #     tz=    bytes([reference.LocalTimezone().utcoffset(datetime.datetime.today()).seconds//3600])
    #     pdu_date=year+month+day+hour+minute+second+tz
    #     pdu_date=self.shuffle(binascii.hexlify(pdu_date).decode()).encode()
    #     return binascii.unhexlify(pdu_date)
    # def shuffle(self,string):
    #     if len(string)%2 == 1:
    #         raise Exception('string length must be even')
    #     return string
    # def get_pdu_recipient(self):
    #     recipient=re.sub("\D", "", self.recipient.decode())
    #     if len(recipient)%2 == 1:
    #         recipient=recipient+'f'
    #     recipient=self.shuffle(recipient).encode()
    #     return binascii.unhexlify(recipient)
class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        logging.info('incoming tcp connection recieved')
        logging.debug('bytes recieved: %s'%self.data)
        sms=SMS(self.data)
        global send_sms_queue
        send_sms_queue.put(sms)
def send_command(serial_port, command_b, answer=msg_ok, timeout=timeout):
    #serial_port.flushInput()
    serial_port.read(serial_port.inWaiting())
    serial_port.write(command_b)
    return wait_for(serial_port, answer, timeout)
def wait_for(serial_port, template, timeout=timeout):
    if template==None:
        template=msg_ok
        return_answer=True
    else:
        template=template
        return_answer=False
    answer=(b'')
    timestamp=time.time()
    while time.time()-timestamp<timeout and not template in answer and not msg_error in answer:
        answer+=serial_port.read(serial_port.inWaiting())
        time.sleep(0.1)
    logging.debug('Recieved from: *** %s ***: %s'%(serial_port.port,answer))
    if return_answer:
        return answer
    else:
        return template in answer
def check_power_on(serial_port):
    return send_command(serial_port, b'AT\r')
def power_on(serial_port):
    serial_port.write(b'+++')
def load_initial_settings(serial_port):
    if not send_command(serial_port, b'ATZ\r'):
        return False 
    if not send_command(serial_port, b'ATE0\r'):
        return False 
    # if not send_command(serial_port, b'AT+CSMP=17,167,0,4\r'):
    #     return False
    # if not send_command(serial_port, b'AT+CSCS="HEX"\r'):
    #     return False
    return send_command(serial_port, b'AT+CMGF=0\r')

# STATE MACHINE
# +STATES
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


