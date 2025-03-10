just some notes:

MeanWell NPB (NPB-1700-48) for my DIY home battery to be steered by CAN-BUS. 
**COMMANDS HAVE TO BE SENT WITH SWAPPED LOW AND HIGH BYTES**, thus reading from the manual e.g. set system_config 
(0x00c2), you have to sent 0xc2, 0x00. I know, it is in the manual, but I guess many of us are first time CAN-BUS users.

FROM THE MANUAL (mine: 6 4.3 Practical Operation of Communication) **Add 120 terminal resistor to both the controller and the NPB** 

I could write 0x03, 0x04 to 0xc2, 0x00 and the value of 4 (the famous 
bit 10) was sustained after power up, indicating it has the disabled 
EEPROM write function! 

When in use as charger change B0, B1, B2, ... 
V and I out_set are for **PSU usage**!  Fields 60 and 61 (READ_VOUT and READ_IOUT) do work, also in charger mode.
(using raspberry pi 3B+ (lan),  Waveshare 2-CH-CAN-Hat, NPB-1700-48 as 
charger and OpenDTU together with Hoymiles HMS-500 as inverters)

Claiming 1700 Watt is somewhat optimistic: Max amp = 25, thus
1700/25=68V. E.g. LiFePO4, ABSOLUTE MAXIMUM voltage: 3.65, 
times 16 cells = 58.4V. Times 25A = 1460 Watt max. In practice voltage
will be even lower, e.g. 56V -> 1400 Watt. Where is the rest of the promised
1700 Watt?
Minimal value (for me) is 5A, max 25A (CURVE_CC)
Choose the CURVE_CV to your liking, I use 55.5V, 3.47 per cell.

Note from the manual: 2. **The setting of charging related parameters requires AC
power on, remote on/off, or communication operation on/off before it can take effect, not immediately.**

And, oh yeah, the search term for the connector on the MeanWell NPB: JST PHDR-14VS (I bought these: 
https://nl.aliexpress.com/item/1005005295218531.html?spm=a2g0o.order_list.order_list_main.29.21ef79d2HRHRib&gatewayAdapt=glo2nld
You get 5 pieces with connectors on both sites, enough to connect 10 chargers!

/boot/firmware/config.txt  
dtparam=spi=on
dtoverlay=mcp2515-can1,oscillator=16000000,interrupt=25
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=23
dtoverlay=spi-bcm2835-overlay

/etc/network/interfaces.d/can  
auto can0
auto can1
iface can0 inet manual
iface can1 inet manual
pre-up ip link set can0 type can bitrate 250000 listen-only off
pre-up ip link set can1 type can bitrate 250000 listen-only off
up /sbin/ifconfig can0 up
up /sbin/ifconfig can1 up
down /sbin/ifconfig can0 down
down /sbin/ifconfig can1 down

sudo apt install python3-can  

import can  
can.rc['interface'] = 'socketcan'
can.rc['channel'] = 'can0'
canbus_charger = can.Bus()
MEANWELL_off(canbus_charger)
LAST_MEANWELL_SET = MEANWELL_set_value(canbus_charger, 1000)


def MEANWELL_off(bus):  
▸   msg = can.Message(arbitration_id=0xc0103, data=[0x00, 0x00, 0x00], is_extended_id=True)
▸   bus.send(msg)
def MEANWELL_on(bus):
▸   msg = can.Message(arbitration_id=0xc0103, data=[0x00, 0x00, 0x01], is_extended_id=True)
▸   bus.send(msg)

def MEANWELL_dump(bus, fields = [0xb0, 0xb1, 0xb2, 0xb3, 0xb9, 0x60, 0x61]):  

▸   for field in fields:  
▸   ▸   print("==============", "FIELD %02x" % field)
▸   ▸   msg = can.Message(arbitration_id=0xc0103, data=[field, 0x00], is_extended_id=True)
▸   ▸   print(msg)
▸   ▸   try:
▸   ▸   ▸   bus.send(msg)
▸   ▸   ▸   ans = bus.recv(1)
▸   ▸   ▸   print(ans)
▸   ▸   ▸   out = float(ans.data[2]) * 0.01 + float(ans.data[3]) * 0.01 * 256.0
▸   ▸   ▸   print("FIELD %02x" % field, out)
▸   ▸   ▸   print("==============")
▸   ▸   except can.CanError:
▸   ▸   ▸   print("Message NOT sent")

MEANWELL_LAST_SET_VALUE = -1  
MEANWELL_AVG_SET_N = 5
MEANWELL_AVG_SET_VALUE = []

def MEANWELL_set_value(bus, value):  # value = Watt's to burn
▸   global MEANWELL_LAST_SET_VALUE, MEANWELL_AVG_SET_N, MEANWELL_AVG_SET_VALUE
▸   print("MEANWELL set value", value)
▸   if value < 0:
▸   ▸   print("MEANWELL_set_value negative", value)
▸   ▸   MEANWELL_off(bus)
▸   ▸   value = 0
▸   ▸   return 0
▸   if value > (56 * 25): value = 56 * 25  # i do the calculations at 56 volt
▸   MEANWELL_AVG_SET_VALUE.append(value)
▸   if len(MEANWELL_AVG_SET_VALUE) > MEANWELL_AVG_SET_N:
▸   ▸   MEANWELL_AVG_SET_VALUE.pop(0)
▸   value = min(MEANWELL_AVG_SET_VALUE)
▸   print("MEANWELL calculated set value", value)

▸   if value == MEANWELL_LAST_SET_VALUE:
▸   ▸   print("MEANWELL already at that setting, leaving as is")
▸   ▸   time.sleep(15)
▸   ▸   return (value)
▸   MEANWELL_LAST_SET_VALUE = value
▸   A = value / 56.0
▸   print("Amps:", A)
▸   A100 = int(A * 100)
▸   high = A100 // 256
▸   low = A100 % 256

▸   msg = can.Message(arbitration_id=0xc0103, data=[0xb0, 0x00,  low, high], is_extended_id=True)
▸   MEANWELL_off(bus)
▸   time.sleep(0.1)  #  I do not like these, but if ommited it does work well
▸   bus.send(msg)
▸   time.sleep(0.1) #  I do not like these, but if ommited it does work well
▸   MEANWELL_on(bus)
▸   time.sleep(15)
▸   return (value)



