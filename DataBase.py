import sys
import math
import MySQLdb
import Local
#import sqlite3
from datetime import *
from array import *

# Management of all database reads and writes though SQL wrapper
class DataBaseManager:
	def __init__(self, type="mysql"):	
		self.db = MySQLdb.connect(Local.HOSTNAME,Local.USERNAME,Local.PASSWORD,Local.DATABASE)
		#elif (type == "sqlite"):
		#	pass
			#self.db = sqlite3.connect("file.db")
		self.cursor = self.db.cursor()	

	def disconnect(self):		
		self.db.close()

	def writeBiasCalibration(self, calibration):
		for entry in calibration.calibrationValues:
			sql = "INSERT INTO Bias(board, module, offset, slope, bias) VALUES ('%i', '%i', '%f', '%f', '%f' )" % (entry['board'], entry['module'], entry['offset'], entry['slope'], entry['bias'])
			try:
				self.cursor.execute(sql)
				self.db.commit()
			except:
				self.db.rollback()

	def writeGainCalibration(self, calibration):
		format = '%Y-%m-%d %H:%i:%s.%f' 
		for entry in calibration.calibrationValues:
			sql = "INSERT INTO PE(validTime, board, bank, channel, pedestal, gain) VALUES (STR_TO_DATE('%s','%s'),'%i','%i','%i','%f','%f')" % (str(calibration.time), format, entry['board'],entry['bank'],entry['channel'],entry['pedestal'],entry['gain'])
			try:
				self.cursor.execute(sql)
				self.db.commit()
			except:
				self.db.rollback()

	def writeTDCCalibration(self, calibration):
		format = '%Y-%m-%d %H:%i:%s.%f' 
		for entry in calibration.calibrationValues:
			sql = "INSERT INTO TDC(validTime, board, bank, channel, offset, slope) VALUES (STR_TO_DATE('%s','%s'),'%i','%i','%i','%f','%f')" % (str(calibration.time), format, entry['board'],entry['bank'],entry['channel'],entry['offset'],entry['slope'])
			try:
				self.cursor.execute(sql)
				self.db.commit()
			except:
				self.db.rollback()

	def writeDiscriminatorCalibration(self, discCalib):
		pass

	def writeIBTCalibration(self, ibtCalibration):
		format = '%Y-%m-%d %H:%i:%s.%f' 
		for entry in ibtCalibration.calibrationValues:
			sql = "INSERT INTO IBT(validTime, board, module, tript, channel, ibt) VALUES( STR_TO_DATE('%s','%s'),%i,%i,%i,%i,%i)" % (str(ibtCalibration.time),format,entry['board'],entry['module'],entry['tript'],entry['ibt'])
			try:
				self.cursor.execute(sql)
				self.db.commit()
			except:
				self.db.rollback()
		pass

	def getRunSetting(self, run, setting):
		sql = "SELECT %s FROM Runs WHERE run = '%i'" % (setting, run) 
                self.cursor.execute(sql)
                results = self.cursor.fetchall()
		result = results[0][0]
		return result

	def getDataSet(self, dataSet, timeBegin=0, timeEnd=0):
		fileSet = []
		if (dataSet != -1):
			format = '%Y-%m-%d %H:%i:%s.%f'
                	sql = "SELECT run FROM Runs WHERE dataSet = '%i'" % dataSet 
                	self.cursor.execute(sql)
                	results = self.cursor.fetchall()
                	for line in results:
                        	fileSet.append(line[0])
		return fileSet

	# Write the run state and return the current run ID
	def writeRunEntry(self, runDescription, dataSetNumber):
		parameters = runDescription.getAllParameters()	
		sql = "INSERT INTO Runs(biasTag, discriminatorTag, bias, vth, vref, dataSet) VALUES(%i, %i, %f, %i, %i, %i)" % (parameters["biasCalibrationTag"], parameters["discriminatorCalibrationTag"], parameters["bias"], parameters["vth"], parameters["vref"], dataSetNumber)
		try:
			self.cursor.execute(sql)
			self.db.commit
		except:
			self.db.rollback()
		return self.db.insert_id()
	
	def getGainCalibration(self, calibration):
		pass

	def getTDCCalibration(self, tdcCalib):
		pass

	def getDiscriminatorCalibration(self, discCalib):
		pass

	#def getLastRunSet(self):
	#	lastID = self.cursor.lastrowid

	def convertBoardIndex(self, board, time):
		# Tell MySQL how to read standard output from python str(datetime)
		format = '%Y-%m-%d %H:%i:%s.%f' 
		sql = "SELECT * FROM BoardLocations WHERE validBegin < STR_TO_DATE('%s','%s') AND validEnd > STR_TO_DATE('%s','%s') AND boardIndex = %i" % (time, format, time, format, board)
		self.cursor.execute(sql)
		results = self.cursor.fetchall()
		for line in results:
			print line

		
