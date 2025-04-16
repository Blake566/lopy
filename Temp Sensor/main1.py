# Measuring temperature by TMP36
from network import LoRa
import socket
import utime
import binascii
import pycom
import ustruct
import machine
import struct
from machine import Pin

adc = machine.ADC()               # create an ADC object
apin = adc.channel(pin=Pin.exp_board.G3)   # Lopy4 specific: (pin = 'P16')   create an analog pin on P16 & connect TMP36

# Temp measurment
def temp_measure():
    print("")
    print("Reading TMP36 Sensor...")
    value = apin()
    print("ADC count = %d" %(value))

    # LoPy  has 1.1 V input range for ADC
    temp = ((value * 1100 ) / 4096 -562) / 10
    print("Temperature = %5.1f C" % (temp))

    return temp

# disable LED heartbeat (so we can control the LED)
pycom.heartbeat(False)
# set LED to red
pycom.rgbled(0x7f0000)

# lora config
LORA_NODE_DR = 5
LORA_FREQUENCY = 917200000
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AU915)

# create an ABP authentication params
dev_addr = struct.unpack(">l", binascii.unhexlify('260DDE73'))[0]
nwk_swkey = binascii.unhexlify('****')
app_swkey = binascii.unhexlify('****')

# remove all the channels
for i in range(0, 72):
    lora.remove_channel(i)

# set all channels to the same frequency (must be before sending the OTAA join request)
lora.add_channel(0, frequency=LORA_FREQUENCY, dr_min=0, dr_max=5)
lora.add_channel(1, frequency=LORA_FREQUENCY, dr_min=0, dr_max=5)
lora.add_channel(2, frequency=LORA_FREQUENCY, dr_min=0, dr_max=5)
# join a network using ABP (Activation By Personalization)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))


# wait for a connection
print('Waiting for LoRaWAN network connection...')
while not lora.has_joined():
	utime.sleep(1)
	# if no connection in a few seconds, then reboot
	if utime.time() > 15:
		print("possible timeout")
		machine.reset()
	pass

# we're online, set LED to green and notify via print
pycom.rgbled(0x004600)
print('Network joined!')

# setup the socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
s.setblocking(False)
s.bind(1)

count = 0
# limit to 200 packets; just in case power is left on
while count < 200:

	# take temp measurment, turn the temp blue when measuring
	pycom.rgbled(0x00007d)
	utime.sleep(1)
	temp = temp_measure()
	pycom.rgbled(0x004600)

	# encode the packet, so that it's in BYTES (TTN friendly)
	# could be extended like this struct.pack('f', temp)   struct.pack('c',"example text")
    # 'h' packs it into a short, 'f' packs it into a float, must be decoded in TTN
	packet = ustruct.pack('f', temp)

	# send the prepared packet via LoRa
	s.send(packet)

	# example of unpacking a payload - unpack returns a sequence of
	#immutable objects (a list) and in this case the first object is the only object
	print ("Unpacked value is:", ustruct.unpack('f',packet)[0])

	# check for a downlink payload, up to 64 bytes
	rx_pkt = s.recv(64)

	# check if a downlink was received
	if len(rx_pkt) > 0:
		print("Downlink data on port 200:", rx_pkt)
		pycom.rgbled(0xffa500)
		input("Downlink recieved, press Enter to continue")
		pycom.rgbled(0x004600)

	count  = 1
	utime.sleep(10)
