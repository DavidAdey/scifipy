import sys
import math
import Setup
import Base
import CalibrationTypes
import DataBase

class GainCalibrator(object):

	def __init__(self, run):

		self.run = run
		self.calibration = CalibrationTypes.GainCalibration()

	def getCalibrationValues(self):

		pass

	def makeGainCalibration(self):

		for channel in self.run.channelRuns:
			ped = 0.0
			gain = 0.0
			if (channel.finder.numFoundPeaks > 1):
				gain = channel.finder.getCalculatedGain()
				ped = channel.finder.peakPositions[0]
			self.calibration.addGainEntry(channel.board, channel.bank, channel.channel, ped, gain)

	def writeCalibration(self):

		dbManager = DataBase.DataBaseManager()
		dbManager.writeGainCalibration(self.calibration)

	# Legacy functions
	def writePeakLocationsTextFile(self):
 
                self.peakLocationFile = open("PeakLocations_" + str(self.runNumber) + ".txt", 'w')
                self.peakLocationFile.write("! channel number, peak locations\n")
                for chan in self.run.channelRuns:
                        self.peakLocationFile.write(str(chan.uniqueChan))
                        if (chan.finder.numFoundPeaks > 0):
                                for peak in range(chan.finder.numFoundPeaks):
                                        self.peakLocationFile.write(" " + str(chan.finder.peakPositions[peak]))
                        self.peakLocationFile.write("\n")


	def writeCalibrationTextFile(self):

                calibrationFile = open("Calibration_" + str(self.runNumber) + ".txt", 'w')
                for channel in self.run.channelRuns:
                        writeString = str(channel.uniqueChan) + " " + str(channel.board) + " " + str(channel.bank) + " " + str(channel.channel) + " "
                        ped = 0.0
                        gain = 0.0
                        if (channel.finder.numFoundPeaks > 1):
                                gain = channel.finder.gain
                                ped = channel.finder.peakPositions[0]
                        writeString += str(ped) + " " + str(gain) + "\n"
                        calibrationFile.write(writeString)	
