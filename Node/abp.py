#!/usr/bin/env python
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

from network import LoRa
import socket
import binascii
import struct
import time

# initialize LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
LORA_NODE_DR = 5
LORA_FREQUENCY = 917200000
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AU915)

# create an ABP authentication params
dev_addr = struct.unpack(">l", binascii.unhexlify('260D42B1'))[0]
nwk_swkey = binascii.unhexlify('D544A372FA5E49A11439B389F1664968')
app_swkey = binascii.unhexlify('08C55F42EC93120B569E13844711DBE7')

# remove all the channels
for i in range(0, 72):
    lora.remove_channel(i)

# set all channels to the same frequency (must be before sending the OTAA join request)
lora.add_channel(0, frequency=LORA_FREQUENCY, dr_min=0, dr_max=5)
lora.add_channel(1, frequency=LORA_FREQUENCY, dr_min=0, dr_max=5)
lora.add_channel(2, frequency=LORA_FREQUENCY, dr_min=0, dr_max=5)
# join a network using ABP (Activation By Personalization)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, LORA_NODE_DR)
# make the socket non-blocking
s.setblocking(False)

for i in range (200):
    pkt = b'PKT #' + bytes([i])
    print('Sending:', pkt)
    s.send(pkt)
    time.sleep(4)
    rx, port = s.recvfrom(256)
    if rx:
        print('Received: {}, on port: {}'.format(rx, port))
    time.sleep(6)
