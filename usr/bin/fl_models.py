from peewee import *

database = MySQLDatabase('fleetcontrol', **{'user': 'flawless', 'passwd': 'password', 'host': 'fleetcontrol.ru', 'port': 3306})

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
    base_lat = FloatField()
    base_lon = FloatField()
    bouy_type = CharField(max_length=30)
    company = ForeignKeyField(db_column='company_id', rel_model=NsControlCompany, to_field='id')
    name = CharField(max_length=30)
    sim_number = CharField(max_length=30)

    class Meta:
        db_table = 'ns_control_bouy'

class NsControlBouyblinkmode(BaseModel):
    name = CharField(max_length=30)

    class Meta:
        db_table = 'ns_control_bouyblinkmode'

class NsControlBouymessage(BaseModel):
    blink_mode = ForeignKeyField(db_column='blink_mode_id', rel_model=NsControlBouyblinkmode, to_field='id')
    bouy = ForeignKeyField(db_column='bouy_id', rel_model=NsControlBouy, to_field='id')
    brightness = IntegerField()
    charge = FloatField()
    drift_alarm = IntegerField()
    gps_problem = IntegerField()
    hit_sensor = IntegerField()
    inclination = FloatField()
    lat = FloatField()
    lighting_alarm = IntegerField()
    lon = FloatField()
    message_type = CharField(max_length=30)
    send_period = IntegerField()
    time = DateTimeField()

    class Meta:
        db_table = 'ns_control_bouymessage'

class NsControlBouylaststate(BaseModel):
    bouy = ForeignKeyField(db_column='bouy_id', rel_model=NsControlBouy, to_field='id')
    message = ForeignKeyField(db_column='message_id', rel_model=NsControlBouymessage, to_field='id')

    class Meta:
        db_table = 'ns_control_bouylaststate'

