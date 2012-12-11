import sys
import Setup
import ROOT
import datetime
import time
import Base
import DataBase
import CalibrationManager
import Globals
from subprocess import call

# Overall management class for the autoDAQ and calibration
class TrackerManager:

	def __init__(self):
		self.afeSetModes = {"bias":self.setBias, "discriminator":self.setDiscriminator, "time":self.setTiming}
		self.settingsModes = {"bias":self.generateBiasSettings, "discriminator":self.generateDiscriminatorSettings, "timing":self.generateTimingSettings, "injection":self.generateInjectionSettings}
		self.calibrationRunDescriptions = []
		self.currentRun = 0
		self.dataSetNumber = time.mktime(datetime.datetime.now().timetuple())
		self.rootFile = ROOT.TFile("tbias.root","recreate")

	# call the generate function from the dictionary using the first entry of the settings as the type
	# then filling the remaining entries of the settings list
	def generateSettings(self, settings):
		if not(isinstance(settings[0], str)):	
			print "Something wrong with the settings type"
			raise TypeError
		for s in range(len(settings) - 1):
			setting = settings[s+1]
			if not(isinstance(setting, float)):
				print "Something wrong with the settings"
				raise TypeError
		self.settingsModes[settings[0]](settings) 

	# Generate the bias settings based on the start point, end point and interval
	def generateBiasSettings(self, settings):	
		biasStep = settings[3]
		biasJump = 1.0/biasStep
		if (settings[1] < Globals.MIN_BIAS or settings[2] > Globals.MAX_BIAS):
			print "Bias settings out of range"
			raise AttributeError
		for bias in [biasCount*biasStep for biasCount in range(int(settings[1]*biasJump),int(settings[2]*biasJump))]:	
			runSetting = CalibrationRunDescription()
			runSetting.setType("bias")
			runSetting.parameters["bias"] = bias
			self.calibrationRunDescriptions.append(runSetting)
	
	def generateDiscriminatorSettings(self, settings):	
		if (settings[1] < 0 or settings[2] > 255):
			print "VTh settings out of range"
			raise AttributeError
		for vth in range(settings[1], settings[2], settings[3]):
			runSetting = CalibrationRunDescription()
			runSetting.setType("discriminator")
			runSetting.parameters["vth"] = vth
			self.calibrationRunDescriptions.append(runSetting)	

	def generateTimingSettings(self, settings):
		if (settings[1] < 0 or settings[2] > 255):
			print "IBt settings out of range"
			raise AttributeError
		for ibt in range(settings[1], settings[2], settings[3]):
			runSetting = CalibrationRunDescription()
			runSetting.setType("ibt")
			runSetting.parameters["ibt"] = ibt
			self.calibrationRunDescriptions.append(runSetting)

	def generateInjectionSettings(self, settings):
		if (settings[1] != 0x5 or settings[1] != 0xA or settings[1] != 0xF):
			print "Level settings out of range"
			raise AttributeError
		if (settings[2] > 10):
			print "Injection delay settings out of range"
			raise AttributeError
		for injectionDelay in range(settings[1]):
			runSetting = CalibrationRunDescription()
			runSetting.setType("injection")
			runSetting.parameters["level"] = settings[1]
			runSetting.parameters["delay"] = injectionDelay
			self.calibrationRunDescriptions.append(runSetting)

	# Call the PyEPICS functions for settings the relevant parameters using the generated settings
	def setParameters(self, runDescription):	
		self.afeSetModes[runDescription.getType()](runDescription.getParameters())

	# Activate the readout managers
	def readout(self, runNumber):
		print "Reading out run" + str(runNumber)
		bias = self.calibrationRunDescriptions[self.currentRun].getParameters()["bias"]
		#call(["/home/daq/Software/ExtApps/CAENVMElib-2-11/apps/TrDAQ",str(runNumber),str(bias)])
		call(["/home/adey/MICE/TrackerCalibration/TrackerCalibration/TrackerDAQ/TrDAQ",str(runNumber),str(bias)])
		self.currentRun += 1

	# Write the run number and settings to the database, getting the current run number
	def writeLog(self, runDescription):
		dbManager = DataBase.DataBaseManager()
		runNumber = dbManager.writeRunEntry(runDescription, self.dataSetNumber)
		dbManager.disconnect()
		del dbManager 	
		return runNumber
		

	def performCalibrations(self):	
		calibrationManager = CalibrationManager.CalibrationManager()
		calibrationManager.setupDataSet(self.dataSetNumber)
		calibrationManager.calibrate(self.calibrationRunDescriptions[0].getType())

	# def engage(self):
	def automate(self):

		for runDescription in self.calibrationRunDescriptions:
			self.setParameters(runDescription)
			runNumber = self.writeLog(runDescription)
			self.readout(runNumber)	
		self.performCalibrations()

	def setBias(self, biasParameters):
		print "Setting with " + str(biasParameters["bias"])

	def setDiscriminator(self):
		pass

	def setTiming(self):
		pass

class CalibrationRunDescription:

	def __init__(self):
		self.type = "NULL"
		self.parameterSelections = {"bias":self.getBiasParameters}
		self.parameters = {"runNumber":-1, "biasCalibrationTag":-1, "discriminatorCalibrationTag":-1, "bias":00, "vth":150, "vref":150, "ibt":80, "injectionLevel":0x0, "injectionDelay":0x0}

	def setType(self, type):
		self.type = type

	def getType(self):
		return self.type

	def getAllParameters(self):
		return self.parameters

	def getParameters(self):
		return self.parameterSelections[self.type]()

	def getBiasParameters(self):
		return {"tag":self.parameters["biasCalibrationTag"], "bias":self.parameters["bias"] }
	
	def getDiscriminatorParameters(self):
		return { "tag":self.parameters["discriminatorCalibrationTag"], "vth":self.parameters["vth"], "vref":self.parameters["vref"] }
