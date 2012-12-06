import sys
import Setup
import Base
import BiasCalib
import Globals
import DataBase

# Manager class for the calibration algorthims
class CalibrationManager:

	def __init__(self):
		self.calibrators = {"bias":BiasCalib.BiasCalibrator()}
		self.dbManager = DataBase.DataBaseManager()

	def setupDataSet(self, dataSetNumber):
		self.fileNumberList = self.dbManager.getDataSet(dataSetNumber)
		self.dataCampaign = Base.DataCampaign()
		self.dataCampaign.setup(self.fileNumberList,Globals.PATH)	

	def setConditions(self, calibrationConditions = 0):
		self.conditions = {"darkCount":0.02, "discriminatorRate":0.02, "gainSpread":0.04}

	def calibrate(self, type):	
		calibrator = self.calibrators[type]
		calibrator.setup()
		calibrator.loadDataCampaign(self.dataCampaign)
		calibrator.runProcesses()


if __name__ == "__main__":

	cm = CalibrationManager()
	cm.setupDataSet(1347405264)
	print cm.fileNumberList
