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
