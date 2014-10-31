    
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
