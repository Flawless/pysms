import re
import logging
def pdu_to_sms(pdu):
    pdu = pdu[int(pdu[:2],16)*2+2:]
    if not pdu[1:2]=='4':
        return None, None
        #raise Exception('not SMS-DELIVER message')
    pdu    = pdu[2:]
    number = pdu[4:int(pdu[:2],16)+5]
    pdu    = pdu[int(pdu[:2],16)+5:]
    if not pdu[:2]=='00':
        logging.warning('TP-PID %s'%pdu[:2])
    pdu = pdu[2:]
    if not pdu[:2]=='08':
        pass
        #raise Exception('cant handle non 8bit messages')
    pdu    = pdu[2:]
    ts     = pdu[:7*2]
    pdu    = pdu[7*2:]
    result = pdu[2:int(pdu[:2],16)*2+2]
    number = swap_octets(number)
    number = re.sub("\D", "", number)        
    number = '+' + number

    return result.encode(), number.encode()

def swap_octets(string):
    string=''.join([ string[x:x+2][::-1] for x in range(0, len(string), 2) ])
    return string

def sms_to_pdu(number, text):
    number = re.sub("\D", "", number)
    result = "000100"
    result += byte_to_pdu_str(len(number))
    result += "91"
    if len(number)%2 != 0:
        number += "F"
 
    number=swap_octets(number)

    result += number
    result += "00"
    result += "04" #8bit encoding
    result += byte_to_pdu_str(int(len(text)/2))
    result += text
    return result.encode(), str(int(len(result)/2) - 1).encode()

def pdu_char_to_byte(s):
    return chr(int("0x" + s,0))
 
def pdu_str_to_byte(s):
    result = ""
    for i in range(int(len(s)/2)):
        result += pdu_char_to_byte(s[i*2:i*2+2])
    return result

def byte_to_pdu_str(b):
    converted = hex(b).upper()
    if b > 0x0f:
        return converted[2:4]
    else:
        return "0" + converted[2]
