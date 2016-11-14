#!/usr/bin/env python
# Michael Saunby. April 2013   
# 
# Read temperature from the TMP006 sensor in the TI SensorTag 
# It's a BLE (Bluetooth low energy) device so using gatttool to
# read and write values. 
#
# Usage.
# sensortag_test.py BLUETOOTH_ADR
#
# To find the address of your SensorTag run 'sudo hcitool lescan'
# You'll need to press the side button to enable discovery.
#
# Notes.
# pexpect uses regular expression so characters that have special meaning
# in regular expressions, e.g. [ and ] must be escaped with a backslash.
#

import pexpect
import sys
import time
import CC2650 as sensor
import hana_upload
import signal

def signal_handler(signal, frame):
	print("__MAIN__: You pressed Ctrl+C!")
	hana.set_stop()
	hana.join()
	# try to finish with a consistent state

	sys.exit(0)

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t

signal.signal(signal.SIGINT, signal_handler)
sensor_data = [ [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] , [0,0,0] ]
bluetooth_adr = sys.argv[1]
tool = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
tool.expect('\[LE\]>')
print "Preparing to connect. You might need to press the side button..."
tool.sendline('connect')
# test for success of connect
tool.expect('Connection successful.*\[LE\]>')
tool.sendline('char-write-cmd 0x24 01')
tool.expect('\[LE\]>')
tool.sendline('char-write-cmd 0x26 32')
tool.expect('\[LE\]>')

tool.sendline('char-write-cmd 0x3C 3800')
tool.expect('\[LE\]>')
tool.sendline('char-write-cmd 0x3E 32')
tool.expect('\[LE\]>')

tool.sendline('char-write-cmd 0x2C 01')
tool.expect('\[LE\]>')
tool.sendline('char-write-cmd 0x2E 32')
tool.expect('\[LE\]>')

hana = hana_upload.hana_uploader()
hana.start()

time_old = time.time()
while True:
    time_test = time.time()
    time.sleep(0.5)
    tool.sendline('char-read-hnd 0x21')
    tool.expect('descriptor: .*') 
    rval = tool.after.split()
    raw_temp_data = [ rval[1], rval[2], rval[3], rval[4] ] 
    sensor_data[6] = sensor.get_ambient_temp(raw_temp_data)
    print(sensor_data[6])


    tool.sendline('char-read-hnd 0x39')
    tool.expect('descriptor: .*')
    rval = tool.after.split()
    raw_move_data = [ rval[1], rval[2], rval[3], rval[4], rval[5], rval[6], rval[7], rval[8], rval[9], rval[10], rval[11], rval[12], rval[13], rval[14], rval[15], rval[16], rval[17], rval[18] ]
    sensor_data[3] = sensor.get_acc_data(raw_move_data)
    sensor_data[3][0] = abs(sensor_data[3][0]) * 0.5
    sensor_data[3][1] = abs(sensor_data[3][1]) * 0.5
    sensor_data[3][2] = abs(sensor_data[3][2]) * 0.5
    print(sensor_data[3])
    

    tool.sendline('char-read-hnd 0x29')
    tool.expect('descriptor: .*') 
    rval = tool.after.split()
    raw_hum_data =  [ rval[1], rval[2], rval[3], rval[4] ] 
    sensor_data[5] = sensor.get_humidity_data(raw_hum_data)
    print(sensor_data[5])

    hana.update_sensor_data(sensor_data)

    print("")
    print("Update Time: " + str( time.time()-time_test) + " seconds")
    print("Uptime: " + str( int((time.time()-time_old)/60.0)) + " minutes")
