#!/bin/python3
from PyQt5 import QtCore, QtWidgets, uic
from enum import IntEnum
import sys, os, time, serial
import serial.tools.list_ports

class Command(IntEnum):
	PING = 1
	ECHO = 2
	SENSOR = 3
	STATUS = 4
	GET_LIMITS = 5
	SET_LIMITS = 6
	FORCE = 7
	AUTO = 8

class Status(IntEnum):
	OK = 0
	UNKNOWN_COMMAND = 1
	MISSING_DATA = 2

class Sensor(IntEnum):
	LIGHT = 1
	TEMP = 2

class State(IntEnum):
	UP = 1
	DOWN = 2

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
		elif status != Status.OK:
			raise Exception('Received unknown status')

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
	def __init__(self, parent, device):
		self.gui = uic.loadUi('widget.ui')
		self.parent = parent
		self.dev = device

		self.parent.widgetsLayout.addWidget(self.gui)
		self.gui.lblPort.setText(self.dev.port)
		self.gui.btnInstellen.clicked.connect(self.set_limits)
		self.gui.btnOprollen.clicked.connect(lambda: self.force_state(State.UP))
		self.gui.btnUitrollen.clicked.connect(lambda: self.force_state(State.DOWN))
		self.gui.btnAutomatisch.clicked.connect(self.enable_auto)

		self.update_data()
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update_data)
		self.timer.start(60000)

	def update_data(self): #TODO: Graph
		print('Updating widget ' + self.dev.port)
		status = self.dev.send(Command.STATUS, [], 3)
		sensor = self.dev.send(Command.SENSOR, [], 3)
		limits = self.dev.send(Command.GET_LIMITS, [], 4)

		if status[2] == 0:
			statusText = 'OPGEROLD ' if status[1] == State.UP else 'UITGEROLD '
		else:
			statusText = 'OPROLLEN ' if status[1] == State.UP else 'UITROLLEN '
		statusText += str(sensor[0]/100) + ' m '
		statusText += '[automatisch]' if status[0] == 0 else '[handmatig]'

		self.gui.lblStatus.setText(statusText)
		self.gui.lblOprollen.setText(str(limits[0]/100) + ' m')
		self.gui.lblUitrollen.setText(str(limits[1]/100) + ' m')

		if sensor[1] == Sensor.LIGHT:
			self.gui.lblSensor.setText('Sensordata Lichtintensiteit')
			unit = ' klx'
			sensorData = sensor[2]
		elif sensor[1] == Sensor.TEMP:
			self.gui.lblSensor.setText('Sensordata Temperatuur')
			unit = ' ºC'
			sensorData = sensor[2]-50

		self.gui.lblSensorData.setText(str(sensorData) + unit)
		self.gui.lblSensorOprollen.setText(str(limits[2]) + unit)
		self.gui.lblSensorUitrollen.setText(str(limits[3]) + unit)

	def force_state(self, state):
		self.dev.send(Command.FORCE, [state])
		self.update_data()

	def enable_auto(self):
		self.dev.send(Command.AUTO)
		self.update_data()

	def set_limits(self): #TODO: Limits popup
		pass

	def remove(self):
		print('Removing widget' + self.dev.port)
		self.parent.widgetsLayout.removeWidget(self.gui)
		self.gui.deleteLater()
		self.gui = None
		self.timer.stop()

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

		t = False
		try: # Test new device
			dev = Arduino(port[0])
			data = dev.send(Command.PING)
			if data != None:
				t = True
			else:
				dev.close()
		except:
			pass

		if t == True:
			w = Widget(mainWindow, dev)
			device_widgets.append(w)
		cPorts.append(port)

def update_widgets():
	for w in device_widgets:
		w.update_data()

def all_set_limits(): #TODO: Limits popup
	pass

def all_force_state(state):
	for w in device_widgets:
		w.dev.send(Command.FORCE, [state])
	update_widgets()

def all_enable_auto():
	for w in device_widgets:
		w.dev.send(Command.AUTO)
	update_widgets()

timer = QtCore.QTimer()
timer.timeout.connect(update_devices)
timer.start(1000)

mainWindow.btnInstellen.clicked.connect(all_set_limits)
mainWindow.btnOprollen.clicked.connect(lambda: all_force_state(State.UP))
mainWindow.btnUitrollen.clicked.connect(lambda: all_force_state(State.DOWN))
mainWindow.btnAutomatisch.clicked.connect(all_enable_auto)
mainWindow.show()
os._exit(app.exec_())
