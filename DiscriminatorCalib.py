# DiscriminatorCalib.py

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
# for the pedestal and higher photo-electron peaks

from array import array

import math
import ROOT
import Configuration

import Base

discriminatorModulesPerModule = 2
channelsPerDiscriminatorModule = 32
numModules = 8
numBoards = 16

class DiscriminatorCalibrator:

	def __init__(self):

		print "Calibrating Discrimiantors"
		self.discModuleRuns = []

	def setup(self):

		for board in range(numBoards):
			for module in range(numModules):
				for trip in range(discriminatorModulesPerModule):
					discModRun = DiscriminatorModuleRun(board, module, trip)
					self.discModuleRuns.append(discModRun)
		

	def loadDataCampaign(self, campaign):

		self.dataCampaign = campaign
		configuration = Configuration.ConfigurationReader(campaign)
		for run in self.dataCampaign.runs:
			print "Looking at run " + str(run.runNumber)
                        settings = configuration.loadSettings(run.runNumber)
                        vth = settings.getVTh()
			for discModRun in self.discModuleRuns:
				discModule = DiscriminatorModule()
				discModule.setVThreshold(vth)
				discModRun.modules.append(discModule)
				print "Added a disc module with vth = " + str(vth)
		i = 0
		for run in self.dataCampaign.runs:
			run.setup()
			settings = configuration.loadSettings(run.runNumber)
                        vth = settings.getVTh()
			readeri = Base.DATEReader(self.dataCampaign.fileNames[i])
                        print "Starting to analyse file:"
                        print self.dataCampaign.fileNames[i]
                        readeri.readBinary(run)
			for channel in run.channelRuns:
				discModRun = self.findDiscriminatorModuleRun(channel.board, channel.module, channel.trip)
				discMod = discModRun.getDiscriminatorModule(vth)
				discMod.addChannelFiredRatio(channel.getDiscriminatorRatio())
				if (channel.getDiscriminatorRatio() != 0.0):
					print "ratio = " + str(channel.getDiscriminatorRatio())
			i = i + 1
			run.clear()		



	def getBestModules(self, optimumRatio):

		for moduleRun in self.discModuleRuns:
			bestVth = 255
			for module in moduleRun.modules:
				vth = module.vTh
				ratio = module.getAverageRatio()
				if ((ratio < optimumRatio) and(vth < bestVth)):
					bestVth = vth
			print "Disc board, module, trip:"
			print moduleRun.board, moduleRun.module, moduleRun.trip
			print "Vth:"
			print bestVth


	def findDiscriminatorModuleRun(self, board, module, trip):

		for dMod in self.discModuleRuns:
			if ((dMod.board == board) and (dMod.module == module) and (dMod.trip == trip)):
				return dMod

		print "Couldn't find module with board, module, trip:"
		print board, module, trip


	def makeHistograms(self):

		for dModRun in self.discModuleRuns:
			moduleString = "Board " + str(dModRun.board) + " Module " + str(dModRun.module) + " Trip " + str(dModRun.trip) + " DiscMod"
			moduleFileName = str(dModRun.board) + "-" + str(dModRun.module) + "-" + str(dModRun.trip) + "DiscMod"
			discModuleRunHist = ROOT.TH1F(moduleString, moduleFileName, 256,0,255)
			for mod in dModRun.modules:
				ratio = mod.getAverageRatio()
				vth = mod.vTh
				discModuleRunHist.Fill(vth,ratio)
			discModuleRunHist.Write()

	def makeGraphs(self):

		for dModRun in self.discModuleRuns:
                        moduleString = "Board " + str(dModRun.board) + " Module " + str(dModRun.module) + " Trip " + str(dModRun.trip) + " DiscMod"
                        moduleFileName = str(dModRun.board) + "-" + str(dModRun.module) + "-" + str(dModRun.trip) + "DiscMod"
			vths = array("d")
			ratios = array("d")
			for mod in dModRun.modules:
                                ratio = mod.getAverageRatio()	
				print ratio
                                vth = mod.vTh
				print vth
				ratios.append(ratio)
				vths.append(vth)
			print len(dModRun.modules)
			print vths
			print ratios	
			dModRun.graph = ROOT.TGraph(len(dModRun.modules),vths,ratios)
			dModRun.graph.SetName(moduleFileName)
			dModRun.graph.SetTitle(moduleString)
			dModRun.graph.SetMinimum(0.0)
			dModRun.graph.Write()



class DiscriminatorModule:

	def __init__(self):

		print "Making a trip-t"
		#self.board = board
		#self.module = module
		#self.trip = trip
		self.channelFiredRatios = []


	def setVThreshold(self, vth):

                self.vTh = vth
		print "Vth = " + str(self.vTh)

	def addChannelFiredRatio(self, ratio):

		self.channelFiredRatios.append(ratio)


	def getAverageRatio(self):

		sumRatio = 0
		for channel in self.channelFiredRatios:
			sumRatio += channel
		ratio =  (sumRatio/channelsPerDiscriminatorModule)
		return ratio


class DiscriminatorModuleRun:

	def __init__(self, board, module, trip):


		print "Making disc mod run"
		self.board = board
                self.module = module
                self.trip = trip
		self.modules = []

	def getDiscriminatorModule(self, vth):

		for mod in self.modules:
			if (mod.vTh == vth):
				return mod
		print "Couldn't find module with vth " + str(vth)
