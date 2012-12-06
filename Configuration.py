# Configuration.py

# This file is part of SciFiPyBiTri.

# SciFiPyBiTri is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# SciFiPyBiTri is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with SciFiPyBiTri.  If not, see <http://www.gnu.org/licenses/>

# D. Adey March 2011

import Base
import DataBase
import ROOT
import math

class ConfigurationReader:

        def __init__(self, campaign):

                #print "Reading" 
		self.campaign = campaign

        def loadData(self):
		pass
                #print "loading data"
		
	def loadSettings(self, runNumber):

		config = ConfigurationSettings()
		configFile = open(self.campaign.configFile,"r")
                fileLines = configFile.readlines()
                for line in fileLines:
			lineArray = line.rsplit(" ")
			#try:
			if (lineArray[0] != "!") and (int(lineArray[0]) == runNumber):
				#print "found run"
				runStr, biasStr, timeInjStr, discrimStr, timeCurStr, intWindowStr, tempStr, ledPeakLocsStr = lineArray
                        	bias = float(biasStr)
				vth = int(discrimStr)
				time = float(timeInjStr)
				intWidth = float(intWindowStr)
				config.addSettings(bias, vth, time, intWidth)
			#	if ((ledPeakLocsStr != "n\n") or (ledPeakLocsStr != "n")):
			#		peakFileName = "PeakLocations_" + ledPeakLocsStr + ".txt"
			#		peakReader = PeakLocationReader(peakFileName)
			#		peaks = peakReader.loadPeakLocations()
			#		config.addPeaks(peaks)				

			#else:
				#print "Failed if"
				#print lineArray
				##print lineArray[0]
				#print runNumber
			#	#returnConfig = config
		return config


	def loadDBSettings(self, runNumber):
		dbManager = DataBase.DataBaseManager()
		bias = dbManager.getRunSetting(runNumber, "bias")
		vth = dbManager.getRunSetting(runNumber, "vth")
		time = 0 #dbManager.getRunSetting(runNumber, "")
		intWidth = 0
		configuration = ConfigurationSettings()
		configuration.addSettings(bias, vth, time, intWidth) 
		dbManager.disconnect()
		return configuration

class ConfigurationSettings:


	def __init__(self):

		#print "Making settings"
		self.channelPeakLocations = []

	def addSettings(self, bias, vth, time, intWindow):

		self.bias = bias
		self.vTh = vth
		self.time = time
		self.integrationWindow = intWindow

	def addPeaks(self, peaks):

		#print "Adding peaks"
		#print len(peaks)
		self.channelPeakLocations = peaks
		#print len(self.channelPeakLocations)

	def getPeak(self, channel, peak):

		#print len(self.channelPeakLocations)
		for peakLocation in self.channelPeakLocations:
			if (peakLocation.channel == channel):
				try:
					return peakLocation.peaks[peak]
				except:
					#print "Failed to find peak, probably out of range"
					return -1
		#print "Couldn't find channel"
		return -1

	def getIntegrationWindow(self):

		return self.integrationWindow

	def getBias(self):

		return self.bias

	def getVTh(self):

		return self.vTh

	def getInjectTime(self):

		return self.time


class PeakLocation:

	def __init__(self, chan=-1, peaks=[]):

		self.channel = chan
		self.peaks = peaks


class PeakLocationReader:

	def __init__(self, file):

		file = file.replace("\n","")
		#print file
		self.file = open(file,"r")


	def loadPeakLocations(self):

		peakLocations = []
		fileLines = self.file.readlines()
                for line in fileLines:
			peaks = [] 	
			lineArray = line.rsplit(" ")
			chanStr = ""
                        if (lineArray[0] != "!"):
				chanStr = lineArray[0]
				if (len(lineArray) > 1):
					#print line
					#print "Length:"
					#print len(lineArray)
					#chanStr = lineArray[0]
					for peak in range(len(lineArray) - 1):
						#print "Peak:"
						#print peak
						peaks.append(float(lineArray[peak + 1]))
						#print lineArray[peak + 1]
				location = PeakLocation(int(chanStr),peaks)
				peakLocations.append(location)
		#print "Returnng from loadPeakLocs:"
		#print len(peakLocations)
		return peakLocations
