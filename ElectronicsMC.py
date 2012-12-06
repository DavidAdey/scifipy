import ROOT

# Class to represnet a single hit in a single channel
class ChannelEvent:

	def __init__(self):

		print "Creating an event"
		self.tdc = -1
		self.adc = -1
		self.discriminator = -1

	def setData(self, spill, event, board, bank, channel, adc, tdc, discriminator):

		self.spill = spill
		self.event = event
		self.board = board
		self.bank = bank
		self.channel = channel
		self.adc = adc
		self.tdc = tdc
		self.discriminator = discriminator

	def setLocation(self, board, bank, channel):

		self.board = board
                self.bank = bank
                self.channel = channel

	def setSpillEvent(self, spill, event):

		self.spill = spill
		self.event = event

	def getData(self, dataType):

		if (dataType == "spill"):
			return self.spill
		elif (dataType == "event"):
			return self.event


    	def package(self):
    
        	packageString = str(self.spill) + " " + str(self.event) + " "
        	packageString += str(self.board) + " " + str(self.bank) + " " + str(self.channel) + " "
        	packageString += str(self.tdc) + " " + str(self.adc) + " " + str(self.discriminator)
        	return packageString
    
            
                


class ElectronicsSimulator:

	def __init__(self):

		pass
		print "Simulating the 'tronics"

		self.adcResolution = 2
		self.timeOffset = 10
		self.integrationWindow = 120
		self.vTh = 150
		self.timeCurrent = 1
		self.gain = 15	
		self.adcPedestal = 50

	def setParameters(self, vth):

		self.vTh = vth
		pass        
        
	def inject(self, channel, time, charge):

		adcMean = charge*self.gain + self.adcPedestal
		if (adcMean > self.vTh):
			print "charge above threshold"
			channel.discriminator = 1
			self.timeCircuit(channel, time)
		else:
			channel.discriminator = 0
			channel.tdc = int(ROOT.gRandom.Gaus(self.timeOffset, self.adcResolution))
			if (channel.tdc < 0):
				channel.tdc = 1
		channel.adc = int(ROOT.gRandom.Gaus(adcMean, self.adcResolution))
		if (channel.adc > 255):
			channel.adc = 255
		elif (channel.adc < 0):
			channel.adc = 1


	def timeCircuit(self, channel, time):

		timeToEnd = self.integrationWindow - time
		print "Time to end"
		timeCharge = timeToEnd*self.timeCurrent + self.timeOffset
		print "Time charge: " + str(timeCharge)
		channel.tdc = int(ROOT.gRandom.Gaus(timeCharge, self.adcResolution))
		if (channel.tdc > 255):
			channel.tdc = 255
