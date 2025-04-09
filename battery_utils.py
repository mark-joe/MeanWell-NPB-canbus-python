#!/usr/bin/env python 
import paho.mqtt.client as mqtt
from battery_config import *
import time
import can
import random
import RPi.GPIO as GPIO

TODAY_DTU = -1
DTU_LAST_SET_VALUE = -1
DTU_AVG_SET_N = 5
DTU_AVG_SET_VALUE = []

MEANWELL_LAST_SET_VALUE = -1
MEANWELL_AVG_SET_N = 7
MEANWELL_AVG_SET_VALUE = []

def DTU_switch_off(client, verbose=False):
	if verbose: print("SWITCH OFF DTU")
	for dtu in range(len(DTUs)):
		topic = 'opendtu/%s/cmd/limit_nonpersistent_absolute' % DTUs[dtu]
		ret = client.publish(topic,0)
		topic2 = 'opendtu/%s/cmd/power' % DTUs[dtu]
		ret = client.publish(topic2,0)
	time.sleep(5)


def DTU_switch_on(client, verbose=False):
	if verbose: print("SWITCH ON DTU")
	for dtu in range(len(DTUs)):
		topic2 = 'opendtu/%s/cmd/power' % DTUs[dtu]
		ret = client.publish(topic2,1)
		topic = 'opendtu/%s/cmd/limit_nonpersistent_absolute' % DTUs[dtu]
		ret = client.publish(topic,0)
	time.sleep(5)

def DTU_set_value(client, in_value, react=False):
	global DTU_LAST_SET_VALUE, DTU_AVG_SET_N, DTU_AVG_SET_VALUE, TODAY_DTU

	if TODAY_DTU < 0:
		TODAY_DTU = random.randint(0,len(DTUs)-1)
		print("Today's DTU", TODAY_DTU)
	print("DTU new setting (in)", in_value)
	value = int(in_value)
	if value > 1000: value = 1000
	save_value = value
	DTU_AVG_SET_VALUE.append(value)
	if len(DTU_AVG_SET_VALUE) > DTU_AVG_SET_N:
		DTU_AVG_SET_VALUE.pop(0)
	value = min(DTU_AVG_SET_VALUE)
	if react: value = save_value
	if DTU_LAST_SET_VALUE == value: 
		if VERBOSE: print("DTU already at that setting, leaving as is")
		time.sleep(WAIT_P1)
		return
	print("DTU new setting", value, value/2)
	DTU_LAST_SET_VALUE = value
	if value < 100:
		topic = 'opendtu/%s/cmd/limit_nonpersistent_absolute' % DTUs[TODAY_DTU]
		ret = client.publish(topic, value)
		for i in range(len(DTUs)):
			if i != TODAY_DTU:
				topic = 'opendtu/%s/cmd/limit_nonpersistent_absolute' % DTUs[i]
				ret = client.publish(topic, 0)
		time.sleep(WAIT_DTU)
	else:
		v = value / 2.0
		topic1 = 'opendtu/%s/cmd/limit_nonpersistent_absolute' % DTUs[0]
		topic2 = 'opendtu/%s/cmd/limit_nonpersistent_absolute' % DTUs[1]
		ret = client.publish(topic1,v)
		ret = client.publish(topic2,v)
		time.sleep(WAIT_DTU)

def MEANWELL_disable(verbose=False):
	if verbose: print("Disable MeanWell charger (hardware)")
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
# 14 = remote on/off (out)
# 15 = charger OK (in)
# 28 = battery OK (in)
	GPIO.setup(14, GPIO.OUT)
	GPIO.output(14, GPIO.LOW)

def MEANWELL_enable(verbose=False):
	if verbose: print("Enable MeanWell charger (hardware)")
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
# 14 = remote on/off (out)
# 15 = charger OK (in)
# 28 = battery OK (in)
	GPIO.setup(14, GPIO.OUT)
	GPIO.output(14, GPIO.HIGH)

def MEANWELL_check_comms(bus):
	msg = can.Message(arbitration_id=0xc0103, data=[0x00, 0x00], is_extended_id=True)
	try:
		bus.send(msg)
		ans = bus.recv(1)
		if int(ans.data[0]) == 0  or  int(ans.data[0]) == 1: return(False)
	except can.CanError:
		return(True)
	return(True)

def MEANWELL_off(bus, verbose=False):
	if verbose: print("MeanWell charger off (software)")
	msg = can.Message(arbitration_id=0xc0103, data=[0x00, 0x00, 0x00], is_extended_id=True)
	try:
		bus.send(msg)
	except can.CanError:
		print("Message NOT sent, is the charger on?")

def MEANWELL_on(bus):
	msg = can.Message(arbitration_id=0xc0103, data=[0x00, 0x00, 0x01], is_extended_id=True)
	bus.send(msg)

def MEANWELL_get_power(bus):
	P = MEANWELL_get_field(bus, 0x60) * MEANWELL_get_field(bus, 0x61)
	return(P)

def MEANWELL_get_field(bus, field):
	msg = can.Message(arbitration_id=0xc0103, data=[field, 0x00], is_extended_id=True)
	try:
		bus.send(msg)
		ans = bus.recv(1)
		if field == 0xb8  or  field == 0xc1:
			out = ans.data[2] + ans.data[3] * 256
		else:
			out = float(ans.data[2]) * 0.01 + float(ans.data[3]) * 0.01 * 256.0
	except can.CanError:
		print("Message NOT sent, is the charger on?")
		godown(0,0)
	return(out)
	
def MEANWELL_dump(bus, fields = [0xb0, 0xb1, 0xb2, 0xb4, 0xb8, 0xb9, 0x60, 0x61, 0x40, 0xc1, 0xc2]):

	varNames = {}
	varNames[0xb0] = 'curve_cc'
	varNames[0xb1] = 'curve_cv'
	varNames[0xb2] = 'curve_fv'
	varNames[0xb3] = 'curve_tc'
	varNames[0xb4] = 'curve_config'
	varNames[0xb5] = 'curve cc timeout'
	varNames[0xb8] = 'charge_status'
	varNames[0xb9] = 'restart_Vbat'

	varNames[0x60] = 'Vout'
	varNames[0x61] = 'Iout'
	varNames[0x40] = 'fault status'
	varNames[0xc1] = 'system status'
	varNames[0xc2] = 'system config'

	showBits = [0xb4, 0xb8, 0x40, 0xc1, 0xc2]

	for field in fields:
#		print("==============", "FIELD %02x" % field)
		msg = can.Message(arbitration_id=0xc0103, data=[field, 0x00], is_extended_id=True)
#		print(msg)
		try:
			bus.send(msg)
			ans = bus.recv(1)
			if field in showBits:
				out = ans.data[2] + ans.data[3] * 256
				print("FIELD %02x %s %02x %02x" % (field,varNames[field],ans.data[3],ans.data[2]))
			else:
				out = float(ans.data[2]) * 0.01 + float(ans.data[3]) * 0.01 * 256.0
				print("FIELD %02x %s" % (field,varNames[field]), out)
		except can.CanError:
			print("Message NOT sent")

def MEANWELL_set_voltage(bus, in_value):

	if in_value > 56:
		print("Won't set charging voltage to higher than 56 V")
		value = 5600
	else:
		value = int(in_value * 100)

	high = value // 256
	low = value % 256
	msg = can.Message(arbitration_id=0xc0103, data=[0xb1, 0x00,  low, high], is_extended_id=True)
	MEANWELL_off(bus)
	bus.send(msg)
	time.sleep(0.05)
	MEANWELL_on(bus)

def MEANWELL_set_restart_voltage(bus, in_value):

	if in_value > 56:
		print("Won't set charging voltage to higher than 56 V")
		value = 5600
	else:
		value = int(in_value * 100)


# THIS IS CURVE_CONFIG FIRST TO ENABLE RESTART
	high = 8
	low = 196
	msg = can.Message(arbitration_id=0xc0103, data=[0xb4, 0x00,  low, high], is_extended_id=True)
	bus.send(msg)
	time.sleep(0.05)

# HERE RESTART VALUE
	MEANWELL_off(bus)

	high = value // 256
	low = value % 256
	msg = can.Message(arbitration_id=0xc0103, data=[0xb9, 0x00,  low, high], is_extended_id=True)
	bus.send(msg)
	time.sleep(0.05)
	MEANWELL_on(bus)

def MEANWELL_set_value(bus, value, do_not_store=False):
	global MEANWELL_LAST_SET_VALUE, MEANWELL_AVG_SET_N, MEANWELL_AVG_SET_VALUE

	print("MEANWELL set value", value)
	if value < 300:
		print("MEANWELL_set_value under 300 Watt", value)
		MEANWELL_off(bus)
		MEANWELL_LAST_SET_VALUE = 0
		return 0
	if value > (56 * 25): value = 56 * 25  # = 1400
	if not do_not_store:
		MEANWELL_AVG_SET_VALUE.append(value)
		if len(MEANWELL_AVG_SET_VALUE) > MEANWELL_AVG_SET_N:
			MEANWELL_AVG_SET_VALUE.pop(0)
		value = min(MEANWELL_AVG_SET_VALUE)
	print("MEANWELL calculated derived set value", value)
	if value == MEANWELL_LAST_SET_VALUE:
		print("MEANWELL already at that setting, leaving as is")
		time.sleep(WAIT_MEANWELL)
		return (value)
	MEANWELL_LAST_SET_VALUE = value
	A = value / 56.0
#	print("Amps:", A)
	A100 = int(A * 100)
	high = A100 // 256
	low = A100 % 256

	msg = can.Message(arbitration_id=0xc0103, data=[0xb0, 0x00,  low, high], is_extended_id=True)
	MEANWELL_off(bus)
	time.sleep(0.1)
	bus.send(msg)
	time.sleep(0.1)
	MEANWELL_on(bus)
	time.sleep(WAIT_MEANWELL)
	return (value)
