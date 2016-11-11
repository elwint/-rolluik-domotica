#!/bin/python3
from PyQt5 import QtWidgets, uic
from enum import IntEnum
import threading, sys, os
import serial
import serial.tools.list_ports
import time

class Command(IntEnum):
	PING = 1
	ECHO = 2
	SENSOR = 3

class Status(IntEnum):
	OK = 0
	UNKNOWN_COMMAND = 1
	MISSING_DATA = 2

class Sensor(IntEnum):
	LIGHT = 1
	TEMP = 2

class Arduino:
	def __init__(self, port):
		self.port = port
		self.ser = serial.Serial(self.port, 19200, timeout=0.25)
		time.sleep(2.5)

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

		if status == Status.UNKNOWN_COMMAND:
			raise Exception('Sent unknown command')
		elif status == Status.MISSING_DATA:
			raise Exception('Sent less values than expected')

		data = []
		if (values < (len(response)-1) / 2):
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

class Widget:
	def __init__(self, parent, device): #TODO: Add widget to window
		self.widget_ui = uic.loadUi('widget.ui')
		self.parent = parent
		self.dev = device
		self.stop = False
		self.run()

	def update_data(self): #TODO: update data & graph
		print('Updating widget ' + self.dev.port)
		data = self.dev.send(Command.SENSOR, [], 3)
		if data[1] == Sensor.LIGHT:
			pass
		elif data[1] == Sensor.TEMP:
			pass

	def run(self):
		if self.stop:
			return
		self.update_data()
		threading.Timer(60, self.run).start()
	
	def remove(self): #TODO: Remove from window
		self.stop = True

app = QtWidgets.QApplication(sys.argv)
mainWindow = uic.loadUi('main.ui')

cPorts = []
device_widgets = []
def update_devices():
	portList = list(serial.tools.list_ports.comports())
	for cPort in cPorts:
		if cPort not in portList: # Device disconnected
			for widget in device_widgets:
				if widget.dev.port == cPort[0]:
					widget.remove()
					widget.dev.close()
					device_widgets.remove(widget)
					break
			cPorts.remove(cPort)

	for port in portList:
		if port in cPorts:
			continue
		try: # Test new device
			dev = Arduino(port[0])
			data = dev.send(Command.PING)
			if data != None:
				w = Widget(mainWindow, dev)
				device_widgets.append(w)
			else:
				dev.close()
		except serial.SerialException:
			pass
		cPorts.append(port)
	threading.Timer(1, update_devices).start()

threading.Timer(1, update_devices).start()
mainWindow.show()
os._exit(app.exec_())
