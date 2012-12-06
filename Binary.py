import sys
import binascii
import struct
import os
import Base
#import MessageHandler
masterIndicator = 0x00000082
boardIndicator = 0x00000083
bankIndicator = 0x00000084

oldMasterIndicator = 0x0000005a
oldBoardIndicator = 0x00000050

wordSize = 4 # bytes
bankLengths = [0,0,0,0]

# representation of the 32bit word used to package the single channel/trigger data
# in the VLSBs. Functions use bitshifts to retrieve the packed information for
# ADC, TDC, Discrimiantor, Channel and Event number
class DataObject:

	def __init__(self, board, bank, word, spill):

		self.board = board
		self.bank = bank
		self.data = word
		self.spill = spill

	def getADC(self):
		return (self.data & 0xFF)

	def getTDC(self):
		return (self.data & 0xFF00) >> 8

	def getEvent(self):
		return (self.data & 0xFF000000) >> 24

	def getDiscriminator(self):
		return (self.data & 0x800000) >> 23

	def getChannel(self):
		return (self.data & 0x7F0000) >> 16

	def getSpill(self):
		return self.spill

	def display(self):
		print hex(self.data)

class BinaryReader:

	def __init__(self):
		#self.messageHandler = MessageHandler.MessageHandler()
		pass

	def open(self, file):
		self.file = open(file,"rb")
		self.size = os.path.getsize(file)	

	# Read the autoDAQ format, which is the bin value for all channels
	def readCompressed(self, run):
		spill = 0
		channel = 0
		bin = 0
		hist = run.getChannelRun(channel).adcHist
		bytes = self.file.read(wordSize)
		while bytes != "":	
			if (bin > 255):		# if the last bin has been reached, 
				bin = 0		# reset and increment channel
				channel += 1
				hist = run.getChannelRun(channel).adcHist	
			word = struct.unpack('i',bytes)[0]
			if (word):		# if the bin value is not zero, add to the histogram
				hist.SetBinContent(bin, word)
			bytes = self.file.read(wordSize) # read the next word
			bin += 1
	
	# Read the DATE format
	# Legacy for the autoDAQ, but left for competeness and old files
	def read(self, run):
		spill = 0	
		physicsEvent = 0
		board = 0 
		bank = 0
		data = 0	
		byte = self.file.read(wordSize)	
		while byte != "":	
			word = struct.unpack('i',byte)[0]	
			if (word == oldMasterIndicator): # master
				self.file.read(16)	
				byte = self.file.read(wordSize)
				numTriggers = struct.unpack('i',byte)[0]
				byte = self.file.read(wordSize)
				trigTDC = struct.unpack('i',byte)[0]
				spill += 1	
			if (word == oldBoardIndicator):	
				# Get the board ID	
				byte = self.file.read(wordSize)
				boardId = struct.unpack('i',byte)[0]
				self.file.read(5*wordSize) # Skip to the data
				# Read the data which is the 4 bank length
				for i in range(4):
					byte = self.file.read(wordSize)
					length = struct.unpack('i',byte)[0]	
					bankLengths[i] = length
				if (bankLengths[0] != bankLengths[1]):# != bankLengths[2] != bankLengths[3]):
					physicsEvent = 0
				else:
					physicsEvent = 1
				board = boardId	
				# option for retrieving the fifo status
				#fifoWord = f.read(wordSize)
				#fifoStatus = struct.unpack('i',fifoWord)[0]
			if (word == bankIndicator):
				byte = self.file.read(wordSize)
				bankId = struct.unpack('i',byte)[0]
				self.file.read(4*wordSize)
				bank = bankId	
				l = bank%4	
				if (physicsEvent):
					for i in range(bankLengths[l]):
						byte = self.file.read(wordSize)
						data = struct.unpack('i',byte)[0]	
						object = DataObject(board, bank, data, spill)
						run.addDataObject(object)	
			byte = self.file.read(4)		

	# Legacy read functions
	def readOld(self, run):

		spill = 0	
		physicsEvent = 0
		board = 0 
		bank = 0
		data = 0
		bytesRead = 0
		#print "about to read"
		byte = self.file.read(wordSize)
		#print "read byte"
		while byte != "":
			bytesRead += wordSize
			#print bytesRead
			#if (not bytesRead % 1024*1024):
			#	self.messageHandler.progressBar((bytesRead - 1), self.size, 1, "Bytes Read")		
			word = struct.unpack('i',byte)[0]
			##print word
			if (word == oldMasterIndicator):
				##print "master"
				"""self.file.read(16)	
				byte = self.file.read(wordSize)
				numTriggers = struct.unpack('i',byte)[0]
				byte = self.file.read(wordSize)
				trigTDC = struct.unpack('i',byte)[0]
				spill += 1"""	
			if (word == oldBoardIndicator):	
				
				# Get the board ID	
				##print "board"
				byte = self.file.read(wordSize)
				boardId = struct.unpack('i',byte)[0]
				##print boardId
				self.file.read(4*wordSize) # Skip to the data
				# Read the data which is the 4 bank length
				for i in range(4):
					byte = self.file.read(wordSize)
					length = struct.unpack('i',byte)[0]	
					bankLengths[i] = length
				if (bankLengths[0] != bankLengths[1]):# != bankLengths[2] != bankLengths[3]):
					physicsEvent = 0
				else:
					physicsEvent = 1
				board = (boardId - 1)	
				#fifoWord = f.read(wordSize)
				#fifoStatus = struct.unpack('i',fifoWord)[0]
				if (physicsEvent):
					for l in range(4):
                                        ##print "getting data of length: " + str(bankLengths[l])
                                        	for i in range(bankLengths[l]):
                                        	        byte = self.file.read(wordSize)
                                        	        data = struct.unpack('i',byte)[0]
                                        	        ##print hex(data)
                                        	        object = DataObject(board, l, data, spill)
                                        	        run.addDataObject(object)
                                        	        ##print object.getADC()
			if (word == bankIndicator):
				##print "bank"
				"""##print hex(word)	
				byte = self.file.read(wordSize)
				bankId = struct.unpack('i',byte)[0]
				self.file.read(4*wordSize)
				bank = bankId
				##print hex(bankId)
				l = bank%4
				##print bank
				if (physicsEvent):
				#for l in range(4):
					##print "getting data of length: " + str(bankLengths[l])
					for i in range(bankLengths[l]):
						byte = self.file.read(wordSize)
						data = struct.unpack('i',byte)[0]
						##print hex(data)
						object = DataObject(board, bank, data, spill)
						run.addDataObject(object)
						##print object.getADC()
				"""
			byte = self.file.read(4)		


