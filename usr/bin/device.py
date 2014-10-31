
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
