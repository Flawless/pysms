#!/usr/bin/env python3
from struct import pack
import sys
import argparse

def createParser():
    parser=argparse.ArgumentParser()
    subparsers=parser.add_subparsers(dest='message_id')
    id4_parser=subparsers.add_parser('id4')
    id4_parser.add_argument('--alarm_timeout', type=int, required=True)
    id4_parser.add_argument('--regular_timeout', type=int, required=True)
    id4_parser.add_argument('--blink_mode', type=int, required=True)
    id4_parser.add_argument('--allowed_radius', type=int, required=True)
    id4_parser.add_argument('--allowed_inclination', type=int, required=True)
    id4_parser.add_argument('--allowed_bump', type=int, required=True)
    id4_parser.add_argument('--allowed_charge', type=int, required=True)
    id4_parser.add_argument('--twilight', type=int, required=True)
    id4_parser.add_argument('--brightness', type=int, required=True)
    id4_parser.add_argument('--alarm_mask', type=str, required=True)

    return parser

def id4(namespace):
    alarm_timeout=namespace.alarm_timeout
    regular_timeout=namespace.regular_timeout
    blink_mode=namespace.blink_mode
    allowed_radius=namespace.allowed_radius
    allowed_inclination=namespace.allowed_inclination
    allowed_bump=namespace.allowed_bump
    allowed_charge=namespace.allowed_charge
    twilight=namespace.twilight
    brightness=namespace.brightness
    alarm_mask=namespace.alarm_mask.encode()
    
    data=bytes([4])+pack('H',alarm_timeout)+pack('H', regular_timeout)+pack('B',blink_mode)+pack('B',allowed_radius)+pack('B',allowed_inclination)+pack('B',allowed_bump)+pack('H',allowed_charge)+pack('B', twilight)+pack('H',brightness)+alarm_mask

    return data

options={
    'id4':id4
}

if __name__=='__main__':
    parser = createParser()
    namespace = parser.parse_args()
    data=options[namespace.message_id](namespace)
    sys.stdout.buffer.write(data)
