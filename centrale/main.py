#!/bin/python3
import serial
import time
import random

def get_data(ser, values=0):
	response = ser.read(1 + (2*values))
	if values == 0:
		status = bytes(response)[0]
	else:
		status = response[0]

	data = []
	for i in range((len(response)-1) // 2):
		data.append(256*response[i*2+1] + response[i*2+2])
	return {'status': status, 'data': data}

def write_data(ser, command, data=[]):
	ser.write(bytes([command]))
	for number in data:
		if number > (1<<16)-1:
			raise Exception('Extra values cannot be bigger than 16 bit')
		ser.write(bytes([number // 256, number % 256]))
	print('Sent command', command, 'with values', data)


ser = serial.Serial('/dev/ttyACM0', 19200, timeout=0.25)
while ser.is_open:
	print('Sending ping command')
	write_data(ser, 1)
	print(get_data(ser))

	print()

	print('Sending echo command')
	write_data(ser, 2, [random.randint(0,65000)])
	print(get_data(ser, 1))

	print()
	time.sleep(2)
