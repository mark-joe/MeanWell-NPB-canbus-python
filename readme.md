just some notes:
DIY Battery with MeanWell NPB (NPB-1700-48) charger, two Hoymiles HMS-500 as inverters, and JK B2A20S20PR-HC BMS, and 16 EVE 280Ah cells.
 
MeanWell NPB (NPB-1700-48) for my DIY home battery to be steered by CAN-BUS. 
**COMMANDS HAVE TO BE SENT WITH SWAPPED LOW AND HIGH BYTES**, thus reading from the manual e.g. set system_config 
(0x00c2), you have to sent 0xc2, 0x00. I know, it is in the manual, but I guess many of us are first time CAN-BUS users.

FROM THE MANUAL (mine: 6 4.3 Practical Operation of Communication) **Add 120 Ohm terminating resistor to both the controller and the NPB** 

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
This holds if using the charger in **charger** mode. You are able to charge the batteries also in **PSU mode**.
In the **PSU mode** case, changes to the settings (voltage/current) are **immediate**. Realize however that **you** are
responsible for monitoring voltages and currents and making sure that charching is done correct and also safe.
In **charger** mode things are much more automated by the charger.

And, oh yeah, the search term for the connector on the MeanWell NPB: JST PHDR-14VS (I bought these: 
https://nl.aliexpress.com/item/1005005295218531.html?spm=a2g0o.order_list.order_list_main.29.21ef79d2HRHRib&gatewayAdapt=glo2nld
You get 5 pieces with connectors on both sites, enough to connect 10 chargers!

**Raspberry settings**

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



