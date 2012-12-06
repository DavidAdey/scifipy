# BiasCalib.py

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

numBoards = 16
modulesPerBoard = 8
channelsPerModule = 64

import ROOT

from array import *
import math
from datetime import date

import Configuration
import Base
import LYCalib
import CalibrationTypes
import DataBase
import Calibrator

class BiasCalibrator(Calibrator.Calibrator):


	def __init__(self):

		##print "setting up"
		super(BiasCalibrator,self).__init__()
		self.moduleRuns = []
		self.calibDate = str(date.today())	
		self.calibFile = open("BiasCalib_" + self.calibDate + ".txt", 'w')	
		self.calibQualityFile = open("BiasCalibQual_" + self.calibDate + ".txt", 'w')
		self.calibration = CalibrationTypes.BiasCalibration()
		self.algorithms = {"highest":self.algHighest, "closest":self.algClosest, "closestAbove":self.algClosestAbove}
	
		self.addProcess("makeMonitoringGraphs", self.makeMonitoringGraphs)
		self.addProcess("makeCalibration", self.makeCalibration, "highest")
		self.addProcess("writeCalibration", self.writeCalibration)
		print self.processes
	
	def setup(self):

		for boardNo in range(numBoards):
			for moduleNo in range(modulesPerBoard):
				moduleRun = ModuleRun(boardNo,moduleNo)
				self.moduleRuns.append(moduleRun)

	def getModuleRun(self, board, module):

		for moduleRun in self.moduleRuns:
			if ((moduleRun.board == board) and (moduleRun.module == module)):
				return moduleRun
		#print "ModuleRun Not Found"

	def loadDataCampaign(self, campaign, useLEDFile = 0):

		# Campaign assumes a list of files in format LED(bias1), noLED(bias1), LED(bias2), noLED(bias2)...
		# This should be enforced by retrieving the runs and files from the database
		configuration = Configuration.ConfigurationReader(campaign)	
		self.dataCampaign = campaign

		# Loop over the noLED files, get the bias entry from the configuration file
		# Create a module object with this bias
		for runnumber in range(1, len(self.dataCampaign.runs),2):
			run = self.dataCampaign.runs[runnumber]
			settings = configuration.loadDBSettings(run.runNumber)
			bias = settings.getBias()
			for mrun in self.moduleRuns:
				mrun.addRun(bias)
		i = 0

		# Loop over the noLED files, picking up the LED files with n-1
		for runnum in range(1, len(self.dataCampaign.runs), 2):
			# Get the runs and setup
			runnoled = self.dataCampaign.runs[runnum]
			runled = self.dataCampaign.runs[runnum - 1]
			runled.setup()
			runnoled.setup()
			i = runnum
			# Create the reader objects - needs to be binary - and read into run
			readernoled = Base.DATEReader(self.dataCampaign.path + self.dataCampaign.fileNames[i])
			readerled = Base.DATEReader(self.dataCampaign.path + self.dataCampaign.fileNames[i -1])
                        print "Reading files " + str(runnum)
			readerled.readBinary(runled)
			readernoled.readBinary(runnoled) 
			# Add the pedestal finders - find the peaks
			runled.addPedestalFinders()	
			runnoled.addPedestalFinders()
			settings = configuration.loadDBSettings(runnoled.runNumber)
			bias = settings.getBias()
			for findernum in range(len(runled.peakFinders)):
				ledfinder = runled.peakFinders[findernum]
				noledfinder = runnoled.peakFinders[findernum]	
				board = ledfinder.channel.board
				module = ledfinder.channel.module
				uniqueModuleNo = module + (board)*modulesPerBoard
				if (useLEDFile == 1):
					onePEPeak = settings.getPeak(uniqueModuleNo, 1)	
				modR = self.getModuleRun(board, module)
				if (modR):	
					mod = modR.getRun(bias)	
					if (useLEDFile == 1):
						mod.addDarkCountRatio( noledfinder.getDarkCount(peakLocation = onePEPeak) )
					else:
						mod.addDarkCountRatio( noledfinder.getDarkCount() )
						mod.totalCounts.append( noledfinder.getDarkCount() * noledfinder.getTotalCounts() )
					mod.addPE(ledfinder.getPE() - noledfinder.getPE() )
					#print "added PE " + str(ledfinder.getPE() - noledfinder.getPE() )

			runled.clear()
			runnoled.clear()
			del runled
			del runnoled
			i = i+1
			
	def getModuleRun(self, board, mod):

		for moduleRun in self.moduleRuns:
			if ((moduleRun.board == board) and (moduleRun.module == mod)):
				return moduleRun
			#else:
				#print "couldn't find module run for " + str(board) + "-" + str(mod)

	def getQualityFactors(self, ratio):

		#print "not getting quality factors"
		for module in self.moduleRuns:
			#bestmod =  module.findLowestRatio()
			bestmod = module.findBestQuality(ratio)
			#print "Board, Module:"
			#print bestmod.board, bestmod.module
			#print "Bias:"
			#print bestmod.bias
			calibString = str(bestmod.board) + " " + str(bestmod.module) + " " + str(bestmod.bias)	
			#calibString += " Alive: " + str(bestmod.alive) + " Dead: " + str(bestmod.dead) + " Breakdown: " + str(bestmod.breakdown) 
			calibString += "\n"
			self.calibQualityFile.write(calibString)


	def getHighestGoodBias(self, goodRatio):

		for moduleRun in self.moduleRuns:
			bestBias = 0.0
			previousRatio = 0.0
			highestRatio = 0.0
			for module in moduleRun.runs:
				bias = module.bias
				ratio = module.getAverageRatio()
				if ((ratio < goodRatio) and (bias > bestBias) and (ratio > previousRatio) and (ratio > highestRatio)):
					bestBias = bias
					highestRatio = ratio
				elif (ratio > highestRatio):
					highestRatio = ratio
				previousRatio = ratio
			calibString = str(module.board) + " " + str(module.module) + " " + str(bestBias) + "\n"
			self.calibFile.write(calibString)

	def makeCalibration(self, type, ratio=0.02):

		try:
			self.algorithms[type](ratio)
		except:
			print "Failed to perform algorithm %s" % type
			print "Options are ",
			for name, function in self.algorithms.iteritems():
				print name +  " ",


	def algHighest(self, goodRatio):
		#print "highest"
		for moduleRun in self.moduleRuns:
			bestBias = 0.0	
			previousRatio = 0.0
			highestRatio = 0.0
			for module in moduleRun.runs:
				bias = module.bias
				ratio = module.getAverageRatio()
				if ((ratio < goodRatio) and (bias > bestBias) and (ratio > previousRatio) and (ratio > highestRatio)):
					bestBias = bias
					highestRatio = ratio
				elif (ratio > highestRatio):
					highestRatio = ratio
				previousRatio = ratio
			offset = 0.0
			slope = 0.0
			self.calibration.addBiasValue(moduleRun.board, moduleRun.module, offset, slope, bestBias)

	def algClosest(self, goodRatio):
		#print "closest"
		for moduleRun in self.moduleRuns:
			bestBias = 0.0
			previousRatio = 0.0
			highestRatio = 0.0
			difference = 0.0
			previous = 500.0
			for module in moduleRun.runs:
				bias = module.bias
				ratio = module.getAverageRatio()
				difference = math.abs(ratio - goodRatio)
				if ((difference < previous) and (bias > bestBias) and (ratio > previousRatio) and (ratio > highestRatio)):
					bestBias = bias
					highestRatio = ratio
				elif (ratio > highestRatio):
					highestRatio = ratio
				previousRatio = ratio
				previous = difference
			offset = 0.0
			slope = 0.0
			self.calibration.addBiasValue(moduleRun.board, moduleRun.module, offset, slope, bestBias)

	def algClosestAbove(self, goodRatio):
		#print "closest"
		for moduleRun in self.moduleRuns:
			bestBias = 0.0
			previousRatio = 0.0
			highestRatio = 0.0
			difference = 0.0
			previous = 500.0
			for module in moduleRun.runs:
				bias = module.bias
				ratio = module.getAverageRatio()
				difference = math.abs(ratio - goodRatio)
				if ((difference < previous) and (bias > bestBias) and (ratio > previousRatio) and (ratio > highestRatio) and (ratio > goodRatio)):
					bestBias = bias
					highestRatio = ratio
				elif (ratio > highestRatio):
					highestRatio = ratio
				previousRatio = ratio
				previous = difference
			offset = 0.0
			slope = 0.0
			self.calibration.addBiasValue(moduleRun.board, moduleRun.module, offset, slope, bestBias)

	def writeCalibration(self):
	
		dbManager = DataBase.DataBaseManager()
		dbManager.writeBiasCalibration(self.calibration)	

	def makeMonitoringGraphs(self):

		for moduleRun in self.moduleRuns:
			moduleRun.makeMonitoringGraphs()

	def endSetup(self):	
		self.addProcess(self.makeMonitoringGraphs)
		print self.processes

class ModuleRun:


	def __init__(self, board, moduleNo):

		#print "Making Module Calibrator"
		self.runs = [] # map bias to Module class
		self.board = board
		self.module = moduleNo

	def addRun(self, bias):

		biasedModule = Module()
		biasedModule.board = self.board
		biasedModule.module = self.module
		biasedModule.bias = bias
		self.runs.append(biasedModule)

	def getRun(self, bias):

		for mod in self.runs:
			if (mod.bias == bias):
				return mod
		#print "Failed to find module"

	def findLowestRatio(self):

		lowest = self.runs[0]
		for run in self.runs:
			#print "Run Bias:"
			#print run.bias
			#print "Run ratio:"
			#print run.getAverageRatio()
			if (run.getAverageRatio() < lowest.getAverageRatio() ):
				lowest = run
		return lowest

	def findLowestDifference(self, optimum):

		lowest = self.runs[0]
                for run in self.runs:
                        #print "Run Bias:"
                        #print run.bias
                        #print "Run ratio:"
			#print run.getAverageRatio()
			difference = optimum - run.getAverageRatio()
			deviation = math.fabs(difference)
			quality = deviation/run.getSignalRatio()
			lowestDeviation = math.fabs(optimum - lowest.getAverageRatio() )
			lowestQuality = lowestDeviation/lowest.getSignalRatio()
                        #print "Absolute Deviation:"
			#print deviation
			#print "Quality:"
			#print quality
                        if ( quality < lowestQuality ):
                                lowest = run
                return lowest

	def findBestQuality(self, optimum):

		lowest = self.runs[0]
		lowest.calculateOffsets(optimum)
		for run in self.runs:
			#print "Run Bias:"
                        #print run.bias
                        #print "Run ratio:"
			run.calculateOffsets(optimum)
			lowestQual = lowest.getAverageOffset() / lowest.getSignalRatio()
			runQual = run.getAverageOffset() / run.getSignalRatio()
			#print "RunQuality:"
			#print runQual
			if (runQual < lowestQual):
				lowest = run
		return lowest


	def makeMonitoringGraphs(self):

		biases = array('d')
		ratios = array('d')
		lightYields = array('d')
		biasErrors = array('d')
		ratioErrorsH = array('d')
		ratioErrorsL = array('d')

		channelAllRatios = array('f')
		channelAllLightYields = array('f')
		channelAllBiases = array('f')
		channels = array('f')
		allChannelNoiseName = str(self.board) + "-" + str(self.module) + "-AllChannelsGraph"
		allChannelPEName = str(self.board) + "-" + str(self.module) + "-AllChannelsPE"
		fileName = str(self.board) + "-" + str(self.module) + "-Graph"
		peName = str(self.board) + "-" + str(self.module) + "-PE"
		allName = str(self.board) + "-" + str(self.module) + "-All"
		#discrimRate = ROOT.TH1F(fileName,fileName,10,0,10)
		self.allChannelsRatioHist = ROOT.TH2F(allChannelNoiseName,allChannelNoiseName,64,-0.5,63.5,20,5.95,7.95)
		self.allChannelsPEHist = ROOT.TH2F(allChannelPEName,allChannelPEName,64,-0.5,63.5,20,5.95,7.95)
		for mod in self.runs:	
			
			bias = mod.bias
			ratio = mod.getAverageRatio()
			lightYield = mod.getAveragePE()
			#discrimRate.Fill(bias,ratio)
			biases.append(bias)
			ratios.append(ratio)	
			lightYields.append(lightYield)

			biasErrors.append(0.02)
			ratioErrorsH.append(mod.getError())

		for channel in range(mod.numChannels):
			channelRatios = array('d')
			channelLightYields = array('d')
			channelBiases = array('d')
			channelGraphName = str(self.board) + "-" + str(self.module) + "-" + str(channel) + "-Graph"	
			channelPEName = str(self.board) + "-" + str(self.module) + "-" + str(channel) + "-PE"
			allName = str(self.board) + "-" + str(self.module) + "-" + str(channel) + "-All"
			for mod in self.runs:
				noise = mod.channelNoiseRatios[channel]
				ly = mod.lightYields[channel]
				bias = mod.bias
				channelRatios.append(noise)
				channelLightYields.append(ly)
				channelBiases.append(bias)
				chan = float(channel)
				self.allChannelsRatioHist.Fill(chan,bias,noise)
				self.allChannelsPEHist.Fill(chan,bias,ly)
				print "Channel, bias, noise:"
				print chan, bias, noise
				#if ((bias > 0.0) and (bias < 8.0) and (chan >= 0.0) and (chan < 64.0) and (noise >= 0.0) and (noise <= 1.0) and (ly >= 0.0)):
				#	print "PASSED IF"
				#	channelAllRatios.append(noise)
				#	channelAllLightYields.append(ly)
				#	channelAllBiases.append(bias)
				#	channels.append(chan)
		
			chanGraph = ROOT.TGraph(len(channelRatios),channelBiases,channelRatios) 
			chanPE = ROOT.TGraph(len(channelRatios),channelBiases,channelLightYields) 
			chanGraph.SetName(channelGraphName)
			chanPE.SetName(channelPEName)
			chanGraph.Write()
			chanPE.Write()

		#self.allChannelGraph = ROOT.TGraph2D(len(channelAllRatios),channelAllBiases,channels,channelAllRatios)
		#elf.allChannelPE = ROOT.TGraph2D(len(channelAllRatios),channelAllBiases,channels,channelAllLightYields)
		#self.allChannelGraph.SetName(allChannelNoiseName)
		#self.allChannelPE.SetName(allChannelPEName)
		#self.allChannelGraph.SetTitle(allChannelNoiseName)
		#self.allChannelPE.SetTitle(allChannelPEName)
		self.allChannelsRatioHist.Write()
		self.allChannelsPEHist.Write()
		#except:
		#	print channelAllBiases
		#	print channels
		#	print channelAllRatios
		#	print channelAllLightYields"""
		self.graph = ROOT.TGraphErrors(len(self.runs),biases,ratios,biasErrors,ratioErrorsH)
		self.graph.SetName(fileName)
		self.graph.SetTitle(fileName)
		self.graph.SetMinimum(0.0)
		self.graph.Write()

		self.peGraph = ROOT.TGraph(len(self.runs),biases,lightYields)
                self.peGraph.SetName(peName)
                self.peGraph.SetTitle(peName)
                self.peGraph.SetMinimum(0.0)
                self.peGraph.Write()

		self.allGraph = ROOT.TGraph(len(self.runs),ratios, lightYields)
                self.allGraph.SetName(allName)
                self.allGraph.SetTitle(allName)
                self.allGraph.SetMinimum(0.0)
                self.allGraph.Write()

		#discrimRate.Write()

class Module:

	def __init__(self):

		self.board = -1
		self.module = -1
		self.channelNoiseRatios = []
		self.deviations = []
		self.bias = 0
		self.numChannels = 64
		self.numSignalChannels = 0
		self.totalCounts = []
		self.dead = 0
		self.alive = 0
		self.breakdown = 0
		self.unknown = 0

		self.lightYields = []
		self.avergePE = 0

	def getError(self):
		sum = 0.0
		for count in self.totalCounts:
			if (count > 0.0):
				sum += (1.0 / math.sqrt(count))
		return sum / len(self.totalCounts)

	def addChannelRatio(self, noiseIntegral, totalIntegral):

		self.channelNoiseRatios.append(noiseIntegral/totalIntegral)

	def addDarkCountRatio(self, ratio):

		self.channelNoiseRatios.append(ratio)
		if (ratio > 0.0):
			self.numSignalChannels += 1
		

	def addPE(self, pe):
		
		self.lightYields.append(pe)


	def getAveragePE(self):

		sumLY = 0
		for ly in self.lightYields:
			sumLY += ly
			#print sumLY
			#print "is sum LY"
		return (sumLY/self.numChannels)		

	def calculateOffsets(self, optimum):

		for chan in range(self.numChannels):
			difference = optimum - self.channelNoiseRatios[chan]
                        deviation = math.fabs(difference)
			self.deviations.append(deviation)

	def getAverageOffset(self):

		sum = 0
		for chan in range(self.numChannels):
			sum += self.deviations[chan]
			#print "Deviation:"
			#print self.deviations[chan]
		averageDeviation = sum/self.numChannels
		#print "Average deviation:"
		#print averageDeviation
		return averageDeviation


	def getAverageRatio(self):

		#print "Getting ratios for module:"
		#print self.board, self.module
		totalRatio = 0.0
		for ratio in self.channelNoiseRatios:
			#print ratio
			totalRatio += ratio
		self.averageNoiseRatio = totalRatio/self.numChannels
		#print "Average:"
		#print self.averageNoiseRatio
		return self.averageNoiseRatio

	def getSignalRatio(self):

		ratio = self.numSignalChannels/self.numChannels
		if (ratio > 0):
			return ratio
		else:
			#print "This module saw no signal"
			return 0.0001 # to avoid division by zero. This is less than 1/64 so worst possible case for weighting]

	def addStatuses(self, status):

		if (status == 0):
			self.dead += 1
		elif (status == 1):
			self.alive += 1
		elif (status == 2):
			self.breakdown += 1
		else:
			self.known += 1

	def getStatuses(self):

		return self.dead, self.alive, self.breakdown
