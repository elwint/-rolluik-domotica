#!/bin/python3
from PyQt5 import QtWidgets, uic
import threading, sys, os
import serial
import serial.tools.list_ports
import time

class Arduino:
	def __init__(self, port):
		self.port = port
		self.ser = serial.Serial(self.port, 19200, timeout=0.25)
		time.sleep(2.5) #TODO: Fix freeze issue

	def send(self, command, data=[], values=0):
		self.write_data(command, data)
		return self.get_data(values)

	def get_data(self, values=0):
		response = self.ser.read(1 + (2*values))
		if not len(response):
			return None
		if values == 0:
			status = bytes(response)[0]
		else:
			status = response[0]

		if status == 1:
			raise Exception('Sent unknown command')
		elif status == 2:
			raise Exception('Sent more values than expected')

		data = []
		if (values < (len(response)-1) // 2):
			raise Exception('Received less values than expected')
		for i in range(values):
			data.append(256*response[i*2+1] + response[i*2+2])
		return data
	
	def write_data(self, command, data=[]):
		self.ser.write(bytes([command]))
		for number in data:
			if number > (1<<16)-1:
				raise exception('Extra values cannot be bigger than 16 bit')
			self.ser.write(bytes([number // 256, number % 256]))
	
	def close(self):
		self.ser.close()

	def get_port(self):
		return self.port

cPorts = []
cDevices = []
def update_devices(loop=False):
	global cPorts, cDevices
	print('Checking...')
	portList = list(serial.tools.list_ports.comports())
	for cPort in cPorts:
		if cPort not in portList: # Device disconnected
			for dev in cDevices:
				if dev.get_port() == cPort[0]:
					cDevices.remove(dev)
					break
			else:
				raise Exception('Attempted to remove an unknown device')
			cPorts.remove(cPort)
			mainWindow.lblPort.setText('--')
			print('Disconnected ' + cPort[0])

	for port in portList:
		if port in cPorts:
			continue
		print('Testing new device...')
		try: # Test new devices
			dev = Arduino(port[0])
			data = dev.send(1)
			if data != None:
				cDevices.append(dev)
				cPorts.append(port)
				mainWindow.lblPort.setText(port[0])
				print('Added ' + port[0])
			else: #TODO: Remember tested devices
				dev.close()
		except serial.SerialException:
			continue
	if loop:
		threading.Timer(2, update_devices, [True]).start()

app = QtWidgets.QApplication(sys.argv)
mainWindow = uic.loadUi('main.ui')
#mainWindow.btnInstellen.clicked.connect(test)
mainWindow.show()
update_devices(True)
os._exit(app.exec_())
