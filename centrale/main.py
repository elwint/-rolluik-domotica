#!/bin/python3
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from enum import IntEnum
import sys, os, time, serial, pyqtgraph
import serial.tools.list_ports
import pyqtgraph
pyqtgraph.setConfigOption('background', 'w')
pyqtgraph.setConfigOption('foreground', '#333')

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
	INVALID_LIMITS = 3

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

	def send(self, command, data=[], values=0, user_input=False):
		c = self.write_data(command, data, user_input)
		if c:
			return self.get_data(values, user_input)
		return None

	def get_data(self, values=0, user_input=False):
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
		elif status == Status.INVALID_LIMITS:
			if user_input:
				error_dialog('Waardes ongeldig.')
				return None
			else:
				raise Exception('Invalid limits')
		elif status != Status.OK:
			raise Exception('Received unknown status')

		data = []
		if (values < (len(response)-1) / 2):
			raise Exception('Received less values than expected')
		for i in range(values):
			data.append(256*response[i*2+1] + response[i*2+2])
		return data
	
	def write_data(self, command, data=[], user_input=False):
		for number in data:
			if number > (1<<16)-1 or number < 0:
				if user_input:
					error_dialog('Waardes ongeldig.')
					return False
				else:
					raise Exception('Extra values cannot be bigger than 16 bit or be negative')
		
		self.ser.write(bytes([command]))
		for number in data:
			self.ser.write(bytes([number // 256, number % 256]))
		return True
	
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

		if self.sensor[1] == Sensor.LIGHT:
			self.gui.lblSensor.setText('Sensordata Lichtintensiteit')
			self.gui.lblSensorIcon.setPixmap(QtGui.QPixmap("icons/light.png"))
		elif self.sensor[1] == Sensor.TEMP:
			self.gui.lblSensor.setText('Sensordata Temperatuur')
			self.gui.lblSensorIcon.setPixmap(QtGui.QPixmap("icons/temp.png"))

		self.graph = pyqtgraph.PlotWidget()
		self.graph.setLabel('bottom', 'Tijd (min)')
		if self.sensor[1] == Sensor.LIGHT:
			self.graph.setLabel('left', 'Licht (klx)')
		elif self.sensor[1] == Sensor.TEMP:
			self.graph.setLabel('left', 'Temperatuur (\00B0C)')
		self.gui.graphLayout.addWidget(self.graph)
		self.graph.setMouseEnabled(False, False)
		self.plot_data = [self.sensor[1]]
		self.update_graph()

		self.timer = QtCore.QTimer()
		self.timer.timeout.connect(self.update_data)
		self.timer.start(10000)
		self.graphTimer = QtCore.QTimer()
		self.graphTimer.timeout.connect(self.update_graph)
		self.graphTimer.start(60000)

	def update_data(self):
		self.status = self.dev.send(Command.STATUS, [], 3)
		self.sensor = self.dev.send(Command.SENSOR, [], 3)
		self.limits = self.dev.send(Command.GET_LIMITS, [], 4)

		if self.status[2] == 1:
			statusText = 'OPGEROLD ' if self.status[1] == State.UP else 'UITGEROLD '
		else:
			statusText = 'OPROLLEN ' if self.status[1] == State.UP else 'UITROLLEN '
		statusText += str(self.sensor[0]/100) + ' m '
		statusText += '[automatisch]' if self.status[0] == 0 else '[handmatig]'

		self.gui.lblStatus.setText(statusText)
		self.gui.lblOprollen.setText('{0:.2f}'.format(self.limits[0]/100) + ' m')
		self.gui.lblUitrollen.setText('{0:.2f}'.format(self.limits[1]/100) + ' m')

		if self.sensor[1] == Sensor.LIGHT:
			unit = ' klx'
		elif self.sensor[1] == Sensor.TEMP:
			unit = ' \u00B0C'
			self.sensor[2] -= 50
			self.limits[2] -= 50
			self.limits[3] -= 50

		self.gui.lblSensorData.setText(str(self.sensor[2]) + unit)
		self.gui.lblSensorOprollen.setText(str(self.limits[2]) + unit)
		self.gui.lblSensorUitrollen.setText(str(self.limits[3]) + unit)
	
	def update_graph(self):
		if len(self.plot_data) == 24:
			self.plot_data.pop(0)
		self.plot_data.append(self.sensor[2])
		data = (24-len(self.plot_data)) * [0] + self.plot_data
		self.graph.plot(range(-23,1), data, pen={'color': '#333'}, clear=True)

	def force_state(self, state):
		self.dev.send(Command.FORCE, [state])
		self.update_data()

	def enable_auto(self):
		self.dev.send(Command.AUTO)
		self.update_data()

	def set_limits(self):
		distance_limits = [self.limits[0], self.limits[1]]
		sensors_limits = [[self.sensor[1], self.limits[2], self.limits[3]]]
		new_data = set_limits_dialog(self.dev.port, distance_limits, sensors_limits)
		if new_data == None:
			return

		distance_limits = new_data['dl']
		sensor_limits = new_data['sl'][0]
		if sensor_limits[0] == Sensor.TEMP:
			sensor_limits[1] += 50
			sensor_limits[2] += 50
		self.dev.send(Command.SET_LIMITS, [distance_limits[0], distance_limits[1], sensor_limits[1], sensor_limits[2]], 0, True)
		time.sleep(0.5)
		self.update_data()

	def remove(self):
		self.parent.widgetsLayout.removeWidget(self.gui)
		self.gui.deleteLater()
		self.gui = None
		self.graphTimer.stop()
		self.timer.stop()

app = QtWidgets.QApplication(sys.argv)
app.setStyle("fusion")
f = open('stylesheet.qss', 'r')
app.setStyleSheet(f.read())
mainWindow = uic.loadUi('main.ui')

cPorts = []
device_widgets = []
def check_devices():
	portList = list(serial.tools.list_ports.comports())
	for cPort in cPorts:
		if cPort not in portList: # Device disconnected
			for widget in device_widgets:
				if widget.dev.port == cPort[0]:
					widget.remove()
					widget.dev.close()
					device_widgets.remove(widget)
					update_widgets_positions()
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
			update_widgets_positions()
		cPorts.append(port)

def update_widgets_positions(resizeEvent=None):
	r,p = 0,0
	for w in device_widgets:
		mainWindow.widgetsLayout.removeWidget(w.gui)
		if (w.gui.width()+mainWindow.widgetsLayout.horizontalSpacing())*p+w.gui.width()+16 > mainWindow.scrollArea.width():
			r += 1
			p = 0
		mainWindow.widgetsLayout.addWidget(w.gui, r, p, QtCore.Qt.AlignTop)
		p += 1
		
def update_widgets():
	for w in device_widgets:
		w.update_data()

def all_set_limits():
	if not device_widgets:
		return
	distance_limits = [device_widgets[0].limits[0], device_widgets[0].limits[1]]
	sensors_limits = []
	for w in device_widgets:
		sensors_limits.append([w.sensor[1], w.limits[2], w.limits[3]])

	new_data = set_limits_dialog('Alles', distance_limits, sensors_limits)
	if new_data == None:
		return

	distance_limits = new_data['dl']
	sensors_limits = new_data['sl']
	for sensor in sensors_limits:
		if sensor[0] == Sensor.TEMP:
			sensor[1] += 50
			sensor[2] += 50

	for w in device_widgets:
		for sensor in sensors_limits:
			if sensor[0] == w.sensor[1]:
				w.dev.send(Command.SET_LIMITS, [distance_limits[0], distance_limits[1], sensor[1], sensor[2]], 0, True)
				break
	time.sleep(0.5)
	update_widgets()

def all_force_state(state):
	for w in device_widgets:
		w.dev.send(Command.FORCE, [state])
	update_widgets()

def all_enable_auto():
	for w in device_widgets:
		w.dev.send(Command.AUTO)
	update_widgets()

def error_dialog(msg):
	dialog = uic.loadUi('error.ui')
	dialog.lblError.setText(msg)
	dialog.exec_()

def set_limits_dialog(t, distance_limits, sensors_limits):
	dialog = uic.loadUi('instellen.ui')
	dialog.setParent(mainWindow, QtCore.Qt.Dialog)
	dialog.setWindowTitle('Instellen - ' + t)
	dialog.txtOprollen.setText('{0:.2f}'.format(distance_limits[0]/100))
	dialog.txtUitrollen.setText('{0:.2f}'.format(distance_limits[1]/100))

	t,l = False,False
	for sensor in sensors_limits:
		if sensor[0] == Sensor.TEMP and t == False:
			t = True
			dialog.txtTOprollen.setText(str(sensor[1]))
			dialog.txtTUitrollen.setText(str(sensor[2]))
		elif sensor[0] == Sensor.LIGHT and l == False:
			l = True
			dialog.txtLOprollen.setText(str(sensor[1]))
			dialog.txtLUitrollen.setText(str(sensor[2]))

	if t == False:
		dialog.frmTemp.hide()
	if l == False:
		dialog.frmLight.hide()

	result = dialog.exec_()
	if result == QtWidgets.QDialog.Accepted:
		try:
			dl = [int(float(dialog.txtOprollen.text())*100),  int(float(dialog.txtUitrollen.text())*100)]
			sl = []
			if t:
				sl.append([Sensor.TEMP, int(dialog.txtTOprollen.text()), int(dialog.txtTUitrollen.text())])
			if l:
				sl.append([Sensor.LIGHT, int(dialog.txtLOprollen.text()), int(dialog.txtLUitrollen.text())])
			return {'dl':dl, 'sl':sl}
		except ValueError:
			error_dialog('Waardes ongeldig.')
			return None
	else:
		return None

timer = QtCore.QTimer()
timer.timeout.connect(check_devices)
timer.start(1000)

mainWindow.btnInstellen.clicked.connect(all_set_limits)
mainWindow.btnOprollen.clicked.connect(lambda: all_force_state(State.UP))
mainWindow.btnUitrollen.clicked.connect(lambda: all_force_state(State.DOWN))
mainWindow.btnAutomatisch.clicked.connect(all_enable_auto)
mainWindow.resizeEvent = update_widgets_positions
mainWindow.show()
os._exit(app.exec_())
