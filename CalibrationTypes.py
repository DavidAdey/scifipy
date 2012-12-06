import Setup
import sys
import math
import datetime
import Base

class TrackerState:

	def __init__(self, time = datetime.datetime.now()):
		self.timeStamp = time
		print self.timeStamp
		self.status = {'biasCalibration':BiasCalibration(self.timeStamp), 
				'discriminatorCalibration':DiscriminatorCalibration(self.timeStamp), 
				'ibtCalibration':IBTCalibration(self.timeStamp), 
				'setBias':0.0, 'vref':170, 'vth':170, 'ibt':80}

# Base class for defintions of a calibrated state
class CalibrationType(object):
	def __init__(self, time = datetime.datetime.now()):
		self.time = time	
		self.calibrationValues = []

# State for a bias calibration with bias, slope and offset for each module
class BiasCalibration(CalibrationType):

	def __init__(self, time = datetime.datetime.now()):	
		super(BiasCalibration,self).__init__(time)

	def addBiasValue(self, board, module, offset, slope, bias):
		biasEntry = {'board':board, 'module':module, 'offset':offset, 'slope':slope, 'bias':bias}
		self.calibrationValues.append(biasEntry)

# State for the timing circuit - IBT level for each TriPt
class IBTCalibration(CalibrationType):

	def __init__(self, time = datetime.datetime.now()):
		super(IBTCalibration,self).__init__(time)

	def addIBTValue(self, board, module, tript, ibt):
		ibtEntry = {'board':board,'module':module,'tript':tript,'ibt':ibt}
		self.calibrationValues.append(ibtEntry)

# State for the discrimiantor level in each TriPt
class DiscriminatorCalibration(CalibrationType):

	def __init__(self, time = datetime.datetime.now()):
		super(DiscriminatorCalibration,self).__init__(time)

	def addTriPtValues(self, board, module, tript, vref, vth):
		triptEntry = {'board':board, 'module':module, 'tript':tript, 'vref':vref, 'vth':vth}
		self.calibrationValues.append(triptEntry)

# State for the gain and pedestal of each channel in each module
# Used to convert ADC counts into PE
class GainCalibration(CalibrationType):

	def __init__(self, time = datetime.datetime.now()):
		super(GainCalibration,self).__init__(time)
	
	def addGainEntry(self, board, bank, channel, pedestal, gain):
		gainEntry = {'board':board, 'bank':bank, 'channel':channel, 'pedestal':pedestal, 'gain':gain}
		self.calibrationValues.append(gainEntry)

# State for the conversion from TDC counts to nanoseconds for each channe
# Uses slope and offset equivalent to gain and pedestal
class TDCCalibration(CalibrationType):

	def __init__(self, time = datetime.datetime.now()):
		super(TDCCalibration,self).__init__(time)

	def addTDCEntry(self, board, bank, channel, offset, slope):
		tdcEntry = {'board':board, 'bank':bank, 'channel':channel, 'offset':offset, 'slope':slope}
		self.calibrationValues.append(tdcEntry)
