from peewee import *

database = MySQLDatabase('fleetcontrol', **{'host': 'fleetcontrol.ru', 'passwd': 'password', 'port': 3306, 'user': 'flawless'})

class UnknownField(object):
    pass

class BaseModel(Model):
    class Meta:
        database = database

class NsControlCompany(BaseModel):
    email = CharField(max_length=30)
    name = CharField(max_length=90)
    reports_time = TimeField()

    class Meta:
        db_table = 'ns_control_company'

class NsControlBouy(BaseModel):
    bouy_type = CharField(max_length=30)
    company = ForeignKeyField(db_column='company_id', rel_model=NsControlCompany)
    name = CharField(max_length=30)
    sim_number = CharField(max_length=30)

    class Meta:
        db_table = 'ns_control_bouy'

class NsControlBouyblinkmode(BaseModel):
    name = CharField(max_length=30)

    class Meta:
        db_table = 'ns_control_bouyblinkmode'

class NsControlBouymessage(BaseModel):
    blink_mode = ForeignKeyField(db_column='blink_mode_id', rel_model=NsControlBouyblinkmode)
    bouy = ForeignKeyField(db_column='bouy_id', rel_model=NsControlBouy)
    brightness = IntegerField()
    charge = FloatField()
    drift_alarm = IntegerField()
    gps_problem = IntegerField()
    hit_sensor = IntegerField()
    inclination = FloatField()
    lat = FloatField()
    lon = FloatField()
    message_type = CharField(max_length=30)
    send_period = IntegerField()
    shift = FloatField()
    time = DateTimeField()

    class Meta:
        db_table = 'ns_control_bouymessage'

class NsControlBouylaststate(BaseModel):
    bouy = ForeignKeyField(db_column='bouy_id', rel_model=NsControlBouy)
    message = ForeignKeyField(db_column='message_id', rel_model=NsControlBouymessage)

    class Meta:
        db_table = 'ns_control_bouylaststate'

