# Base.py - Base classes for tracker calibration
# D.Adey March 2011

# Edits
# 12-06-12 Removed writeCalibration() from Run - this is now in GainCalibrator
import string
import math
import ROOT
import LYCalib
import Configuration
import Binary
#import MessageHandler

# Some constants - could be moved into an external file but they're never going to change
chansPerBoard = 512
chansPerBank = 128
numBoards = 16
numBanks = 4
adcRange = 256 # 8bit

modulesPerBank = 2
channelsPerModule = 64
channelsPerTrip = 32

# Class to represent a single channel with adc values over a number of events, stored
# in adcValues

class ChannelHit:

	def __init__(self, chan = -1, adc = -1, tdc = -1, discrim = -1, event = -1):

		self.uniqueChan = chan
		self.adc = adc
		self.tdc = tdc
		self.discriminator = discrim
		self.event = event



class ChannelRun:

	# Constructor - set default values
	def __init__(self, storeall = 0):
            	
		self.storeAll = storeall 		# whether to only keep histograms or all raw data
		self.board = -1 			# VLSB/AFE board ID
		self.bank = -1 				# Bank ID
		self.channel = -1 			# Channel number            
		self.adcValues = []
		self.adcRange  = adcRange
		self.tdcValues = []
		self.discriminators = []
		self.histoMade = 0
		self.status = -1 			# -1 unknown, 0 dead, 1 alive, 2 breakdown
		self.maxAdc = 0
		self.size = 0

		self.hits = []
		self.totalDiscriminatorValues = 0
		self.totalDiscriminatorFired = 0
            

	# give VLSB, Bank and Channel numbers to class and create a unique channel number
	def setup(self, boardin, bankin, channelin):
		
		self.board = boardin
		self.bank = bankin
		self.channel = channelin
		self.uniqueChan = self.channel + ( (self.bank)*chansPerBank) + ( (self.board)*chansPerBoard)


		# Get Module number from channel number - channel number ranges from 0-127 for 128 channel per DFPGA
		# Two AFPGAs/MCM/VLPC Modules per DFPGA means 64 channels per module
		# Module number then runs from 0-7 on each board
		if ((self.channel < channelsPerModule) and  (self.channel >= 0)):
                	self.module = (self.bank * modulesPerBank)
			self.trip = int(self.channel/channelsPerTrip)
                elif ((self.channel >= channelsPerModule) and (self.channel < chansPerBank)):
                	self.module = (self.bank * modulesPerBank) + 1
			self.trip = int((self.channel - channelsPerModule)/channelsPerTrip)
                else:
                	#print "Channel Number out of Range"
			self.module = -1
	
		##print "Trip is " + str(self.trip)



	# add an ADC value to the array
	def addAdcValue(self, value):
            
		self.adcHist.Fill(value)
		self.size += 1
		if (value > self.maxAdc):
			self.maxAdc = value # Reset the highest ADC value recoded in this run
            

	# add a TDC value to the array
        def addTdcValue(self, value):

                if (self.storeAll):
			self.tdcValues.append(value)
		self.tdcHist.Fill(value)

	def addDiscriminator(self, discrim):
		self.totalDiscriminatorValues += 1.0
		self.totalDiscriminatorFired += discrim	
		if (self.storeAll):
			self.discriminators.append(discrim)
		self.discrimHist.Fill(discrim)


	def addHit(self, channel, adc, tdc, discrim, event):

		hit = ChannelHit(self.uniqueChan, adc, tdc, discrim, event)
		self.hits.append(hit)

	def getDiscriminatorRatio(self):
	
		if (self.totalDiscriminatorValues > 0):
			return (self.totalDiscriminatorFired/self.totalDiscriminatorValues)
		else:
			return 0.0

	# Setup 1D histograms for ADC, TDC and discrimator
	def setupHistograms(self, number):
		tdcHistogramName = "Board: " + str(self.board) + " Bank: " + str(self.bank) + " Channel: " + str(self.channel) + " (TDC)"
                tdcHistFileName = str(number) + "-" + str(self.board) + "-" + str(self.bank) + "-" + str(self.channel) + "-TDC"
		discrimHistogramName = "Board: " + str(self.board) + " Bank: " + str(self.bank) + " Channel: " + str(self.channel) + " (Discriminator)"
		discrimHistFileName = str(number) + "-" + str(self.board) + "-" + str(self.bank) + "-" + str(self.channel) + "-Disc"
                self.tdcHist = ROOT.TH1F(tdcHistFileName, tdcHistogramName, self.adcRange, 0, self.adcRange)
		self.discrimHist = ROOT.TH1F(discrimHistFileName, discrimHistogramName, 2, 0, 2)
		histogramName = "Board: " + str(self.board) + " Bank: " + str(self.bank) + " Channel: " + str(self.channel)
                histFileName = str(number) + "-" + str(self.board) + "-" + str(self.bank) + "-" + str(self.channel)
                self.adcHist = ROOT.TH1F(histFileName, histogramName, self.adcRange, 0, self.adcRange)


	# Make a histogram of stored ADC values for this channel. Take a canvas, make a histogram
	# fill with entries of adc array, draw and save to file
	# Legacy function
	def makeAdcHistogram(self):
		for adc in self.adcValues:
			self.adcHist.Fill(adc)
		self.adcHist.Draw()	
		self.histoMade = 1
		self.name = histFileName
		for adc in self.adcValues:
			del adc

	# Write the histograms
	def writeHistograms(self):
		self.adcHist.Write()
		self.tdcHist.Write()
		self.discrimHist.Write()


# Class to represent the run, with list of each channel as ChannelRuns
class Run:
      
	# Constructor
	def __init__(self):
            
		self.spills = []
		self.channelRuns = []
		self.peakFinders = []
		self.attributes = {}
		self.channelsMaxed = 0
		#self.dataObjects = []
		self.runNumber = 1#int(fileName[:-4])
		#self.messageHandler = MessageHandler.MessageHandler()

	# Does what its name says, removing extensions
	def setName(self, fileName):
		self.name = fileName
		if (string.count(self.name,"gdc")):
			fileName = string.lstrip(fileName,"gdc")
		if (string.count(self.name,"dat")):
			fileName = string.rstrip(fileName,".dat")
		if (string.count(self.name,".000")):
			fileName = string.rstrip(fileName,".000")
		self.runNumber = int(fileName)

	# Setup by creating entries of channels 
	def setup(self):
		self.adcAllHist = ROOT.TH2F(self.name + "-AllChannels", self.name + "-AllChannels", 8192, 0, 8192, 256, 0, 256) 
		for boardNum in range(numBoards):
	  		for bankNum in range(numBanks):
	        		for chanNum in range(chansPerBank):
	              			chanRun = ChannelRun()
	              			chanRun.setup(boardNum, bankNum, chanNum)
					chanRun.setupHistograms( self.runNumber)
	              			self.channelRuns.append( chanRun )
					#self.messageHandler.progressBar(chanRun.uniqueChan, numBoards*512, 128, "Channel Runs Setup")
		#self.messageHandler.end()
	              
	# Get a ChannelRun based on its unique channel number           
	def getChannelRun(self, uniqueId):
           
		for i in range(len(self.channelRuns)):
			if (self.channelRuns[i].uniqueChan == uniqueId): 
				return self.channelRuns[uniqueId]
		#print "Couldn't find ID:"
		#print uniqueId
            

	def addDataObject(self, object):

		try:
			#self.dataObjects.append(object)
			uniqueChan = object.getChannel() + (object.bank*chansPerBank) + (object.board*chansPerBoard)	
			##print "un = " + str(uniqueChan)
			#self.adcAllHist.Fill(uniqueChan,object.getADC())
			self.channelRuns[uniqueChan].addAdcValue(object.getADC())
			#self.channelRuns[uniqueChan].addTdcValue(object.getTDC())
			#self.channelRuns[uniqueChan].addDiscriminator(object.getDiscriminator())
			#if (object.getDiscriminator() == 1):
			#	#print "Non-zero disc"
		except:
			#print "Problems with adding data word"
			object.display()
			#print hex(object.bank)

	# add information to channel - find by board, bank, channel and add adc & tdc
	# Legacy from ascii data files
	def addChannelInfo(self, event, board, bank, chan, tdc, adc, discrim):

		uniqueChan = chan + ( (bank)*chansPerBank) + ( (board)*chansPerBoard)
		self.adcAllHist.Fill(uniqueChan,adc)
		#self.getChannelRun(uniqueChan).addAdcValue(adc)
                #self.getChannelRun(uniqueChan).addTdcValue(tdc)
		self.channelRuns[uniqueChan].addAdcValue(adc)
		self.channelRuns[uniqueChan].addTdcValue(tdc)
		self.channelRuns[uniqueChan].addDiscriminator(discrim)
		#self.channelRuns[uniqueChan].addHit(uniqueChan, adc, tdc, discrim, event)
		del uniqueChan
	
	# Add PedestalFinder (from LYCalib) to each ChannelRun, find PE peaks, fit, get integrals
	def addPedestalFinders(self, fit=0):

		for channel in self.channelRuns:
			finder = LYCalib.PedestalFinder()
			finder.loadChannel(channel)	
			finder.findPeaks()
			if (fit):
				finder.fitAllPeaks()
				#print finder.getDarkCount()	
			self.peakFinders.append(finder)
			channel.finder = finder
			#self.messageHandler.progressBar(channel.uniqueChan, len(self.channelRuns), 128, "Pedestal Finders")
		#self.messageHandler.end()

	def save(self, canvas):

		for channel in self.channelRuns:
			#channel.finder.savePlots(canvas)
			channel.writeHistograms()

	def writePeakLocations(self):

		#print "Writing peak positions"	
                self.peakLocationFile = open("PeakLocations_" + str(self.runNumber) + ".txt", 'w')
		self.peakLocationFile.write("! channel number, peak locations\n")
		for chan in self.channelRuns:	
			self.peakLocationFile.write(str(chan.uniqueChan))
			self.peakLocationFile.write(" " + str(chan.finder.getDarkCountRatio()))
			if (chan.finder.numFoundPeaks > 0):
				for peak in range(chan.finder.numFoundPeaks):	
					self.peakLocationFile.write(" " + str(chan.finder.peakPositions[peak]))
			self.peakLocationFile.write("\n")	


	def clear(self):

		for channel in self.channelRuns:
			if channel.adcHist:
				channel.adcHist.Write()
				del channel.adcHist
			del channel.tdcHist
			del channel.discrimHist


	def display(self, canvas):

		for channel in self.channelRuns:	
			channel.makeAdcHistogram(canvas)
 			for adc in channel.adcValues:
				self.adcAllHist.Fill(channel.uniqueChan,adc)

		self.adcAllHist.Draw("colz")
		canvas.SaveAs(self.name + "_allChannels.png")


	def plotRawData(self):
                #hits_above=0
		##print "here i am"
		discrimAdc = ROOT.TH2F("discadc","discadc",8192,0,8192,256,0,256)
		eventChannel = ROOT.TH2F("eventchan","eventchan",8192,0,8192,50,0,50)
		#numhits= ROOT.TH2F("hitsover50","hitsover50",8192,0,8192,256,0,256)
		for channel in self.channelRuns:
			for hit in channel.hits:
				eventChannel.Fill(channel.uniqueChan, hit.event)
				##print "adc= " +str(hit.adc)
				if (hit.discriminator != 0):
					discrimAdc.Fill(channel.uniqueChan,hit.adc)
					##print "adc=" + str(hit.adc)
					#numhits.Fill(channel.uniqueChan,hit.adc)
		discrimAdc.Write()
		eventChannel.Write()
		#numhits.Write()
		

	# Produce histograms for this run plotting number of hits in each channel and bank
	# Compare in each looking for mismatch - all banks and channels should be equal
	# if zero suppression is turned off
	def qualityCheck(self):

		channelsMaxed = 0

		channelHitCountHist = ROOT.TH1F("ChannelCount" + self.name, "ChannelCount" + self.name, 8192, 0, 8192)
		bankHitCountHist = ROOT.TH2F("BankCount"+ self.name, "BankCount"+ self.name, 8, 0, 8, 4, 0, 4)
		channelHitCountDiffHist = ROOT.TH1F("ChanDiff"+ self.name, "ChaneDiff"+ self.name, 8192, 0, 8192)
                bankHitCountDiffHist = ROOT.TH2F("BankDiff"+ self.name, "BankDiff"+ self.name, 8, 0, 8, 4, 0, 4)

		channelPeakPositions = ROOT.TH2F("chanpeaks"+ self.name,"chanpeaks"+ self.name,8192,0,8192,256,0,256)
		channelGains = ROOT.TH2F("changains"+ self.name,"changains"+ self.name,8192,0,8192,50,0,50)

		channelRMS = ROOT.TH2F("chanrms"+ self.name,"chanrms"+ self.name,8192,0,8192,50,0,50)
		channelMaxBin = ROOT.TH2F("maxbin"+ self.name,"maxbin"+ self.name,8192,0,8192,256,0,256)

		channelPE = ROOT.TH2F("chanpe"+ self.name,"chanpe"+ self.name,8192,0,8192,50,0,10)
		discAdc = ROOT.TH2F("discadc"+ self.name,"discadc"+ self.name,8192,0,8192,50,0,1.0)
		for finder in self.peakFinders:
			channelGains.Fill(finder.channel.uniqueChan,finder.gain)
			channelRMS.Fill(finder.channel.uniqueChan,finder.channel.adcHist.GetRMS())
			if (finder.gain > 0.0):
				averagePE = (finder.channel.adcHist.GetMean() - finder.peakPositions[0]) / finder.gain
			else:
				averagePE = -1
			if (averagePE > 0.0):
				channelPE.Fill(finder.channel.uniqueChan,averagePE)
			for peak in range(finder.numFoundPeaks):
				peakBin = finder.channel.adcHist.FindBin(finder.peakPositions[peak])
				peakHeight = finder.channel.adcHist.GetBinContent(peakBin)
				peakValue = finder.peakPositions[peak]# - finder.peakPositions[0]
				channelPeakPositions.Fill(finder.channel.uniqueChan,peakValue,peakHeight)

		self.bankPopulation = [[0 for i in range(numBanks)]for j in range(numBoards)]	
		self.channelPopulation = [0 for i in range(numBoards * numBanks * chansPerBank)]

		for channel in self.channelRuns:
			channelHitCountHist.Fill(channel.uniqueChan, channel.size)
			bankHitCountHist.Fill(channel.board, channel.bank, channel.size)
			#self.bankPopulation[channel.board][channel.bank] += channel.size
			#self.channelPopulation[channel.uniqueChan] += channel.size
			channelMaxBin.Fill(channel.uniqueChan, channel.maxAdc)
			discAdc.Fill(channel.uniqueChan, channel.discrimHist.GetMean())
			if (channel.maxAdc == 255):
				channelsMaxed += 1
	
		# Assume maximum from any bank is maximum possible
		# Should really retrieve sum of sent triggers, but this isn't in the DAQ stream
		bankMaxVal = bankHitCountHist.GetMaximum()
		channelMaxVal = channelHitCountHist.GetMaximum()

		

		for sameChannel in self.channelRuns:

			bankHitCountDiffHist.Fill(sameChannel.board, sameChannel.bank, -(bankMaxVal))
			channelHitCountDiffHist.Fill(sameChannel.uniqueChan, -(channelMaxVal))

			self.bankPopulation[sameChannel.board][sameChannel.bank] += (channelMaxVal - sameChannel.size)
                        self.channelPopulation[sameChannel.uniqueChan] += (channelMaxVal - sameChannel.size)
			##print "Channel max value = " + str(channelMaxVal)
			##print "Channelsize = " + str(sameChannel.size)
			##print "Filling with: " + str(channelMaxVal - sameChannel.size) 

		channelHitCountDiffHist.Add(channelHitCountHist)
		bankHitCountDiffHist.Add(bankHitCountHist)

		self.adcAllHist.Write()
		channelMaxBin.Write()
		channelRMS.Write()
		channelGains.Write()
		channelPE.Write()
		channelPeakPositions.Write()
		channelHitCountDiffHist.Write()
		bankHitCountDiffHist.Write()
		channelHitCountHist.Write()
		bankHitCountHist.Write()
		discAdc.Write()
		#print "Channels Maxed = " + str(channelsMaxed)
		#print "RMS of gains = %f" % channelGains.GetRMS(2)

# Unfinished spill class - may not be needed
class Spill:
      
	def __init__(self):
            
		self.events = []
      
# Unfinished event class - may not be needed
class Event:
          
	def __init__(self):
		pass
		#print "This is an event"

# Unfinished Data Campaign class - need for multi-run calibrations
class DataCampaign:

	def __init__(self):

		#print "Campaigning the data"
		self.fileNames = []
		self.runs = []

	def setup(self, args, path):

		self.path = path
		#self.configFile = args[1]
		#print self.configFile
		#for i in range(len(args) - 2):
		for i in range(len(args)):
			#self.fileNames.append("gdc" + str(args[i+2]) + ".000")
			self.fileNames.append(str(args[i]))
			#print args[i+2]
			runi = Run()
			#runi.setup()
			##print args[i+2]
			runi.setName(str(args[i]))
			#readeri = DATEReader(args[i+2])
			#readeri.readFile(runi)
			self.runs.append(runi)
			



class Monitor:

	def __init__(self):

		pass

	def loadCampaign(self, campaign):

		self.campaign = campaign	
		#self.configuration = Configuration.ConfigurationReader(self.campaign)
		self.numRuns = len(self.campaign.runs)

	def setup(self):

		self.runBankPopulation = ROOT.TH2F("BankPopulations","BnkPopulations",numBanks*self.numRuns,0,numBanks*self.numRuns, numBoards,0,numBoards)

	def monitorRuns(self):

		pass

		i = 0
		for run in self.campaign.runs:
			run.setup()
			#settings = self.configuration.loadSettings(run.runNumber)
			readeri = DATEReader(self.campaign.fileNames[i])
			readeri.readFile(run)
			run.addPedestalFinders()
			run.qualityCheck()
			for board in range(numBoards):
				for bank in range(numBanks):
					#print "Board, bank, i:"
					#print board, bank, i
					#print run.bankPopulation[board][bank]
					self.runBankPopulation.Fill(numBanks*i + bank, board, run.bankPopulation[board][bank])
			run.qualityCheck()
			run.clear()
			i += 1				
		self.runBankPopulation.Write()

class DATEReader:
      
	# Constructor
	def __init__(self, filename):

		#print filename
		self.filename = filename            
            

	def readRootFile(self, run):

		pass

	def readBinary(self, run, dataFormat="compressed"):

		binaryReader = Binary.BinaryReader()
		binaryReader.open(self.filename)
		#binaryReader.readOld(run)	
		#binaryReader.readCompressed(run)
		binaryReader.formats[dataFormat](run)
	# Read in lines of file to array, break up each individual line into an array
	# and pass array entries into variables based on known format of file.
	# Convert variables to ints and add information to run's channels
	def readFile(self, run):
            
		#print "reading "
		run.setName(self.filename)
		dataFile = open(self.filename,"r")
		#fileLines = dataFile.readlines()
		#eventCount = 0
		#channelCount = 0
		#for line in fileLines:
		line = " "#dataFile.readline()	
		while (line != ""):
			line = dataFile.readline()
			#++channelCount
			#if (channelCount == 8192):
			#	++eventCount
			##print "Read " + str(eventCount) + " events"
			lineArray = line.rsplit(" ")
			if ( len(lineArray) > 1):	
				spillStr, eventStr, boardStr, bankStr, chanStr, tdcStr, adcStr, discStr = lineArray
			discrim = int(discStr)
			#lse:
			#	spillStr, eventStr, boardStr, bankStr, chanStr, tdcStr, adcStr = lineArray
			spill = int(spillStr)
			event = int(eventStr)
			board = int(boardStr)
			bank = int(bankStr)
			chan = int(chanStr)
			tdc = int(tdcStr)
			adc = int(adcStr)
			#run.addChannelInfo(event, (board-2), bank, chan, tdc, adc)
			#if ( len(lineArray) == 8):
				##print ".",
			#if (discrim > 0):
			#		#print "ITS MORE THAN 0! IT'S " + str(discrim) + " at " + str(board) + " " + str(bank) + " " + str(chan) 
			run.addChannelInfo(event, board, bank, chan, tdc, adc, discrim)
			#line = dataFile.readline()
			#else:
			#	run.addChannelInfo(event, board, bank, chan, tdc, adc, 0)

