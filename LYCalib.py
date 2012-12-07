# D. Adey March 2011



from math import *
import ROOT
from ROOT import TMath
import array

PI = 3.142
numbers = ['one','two','three','four','five','six','seven','eight','nine','ten']

# Class to use TSpectrum and other ROOT fitting functions to find the 
# pedestal and multi-PE peaks for a distribution of ADC counts for
# a particular channel. The ratio of accidentals to pedestal can then be used
# to determine a quality factor for this distribution

class PedestalFinder:

	def __init__(self):

		##print "something"
		#self.canvas = canvas
		#self.numPeaks = 5
		self.gain = 0
		self.numFoundPeaks = 0
		self.integrals = {}
		self.fitResults = []

	# Load a ChannelRun, which should already have been filled with ADC counts
	# Add a TSpectrum
	def loadChannel(self, channelRun):

		self.channel = channelRun
		self.spectrum = ROOT.TSpectrum();

	# Call make histograms function for the channel in this pedestal finder
	def makeHistograms(self):

		if (self.channel.histoMade == 0):
			self.channel.makeAdcHistogram()
			

	# Using a ROOT TSpectrum, find the PE peaks in this channel's ADC distribution
	# Store the positions of the peaks in self.peakPositions
	# Loop over the peak positions and make a guess at the gain as the average
	# distance between peaks, store as self.gain
	def findPeaks(self):

		gainGuess = 0.0
		self.numFoundPeaks = self.spectrum.Search(self.channel.adcHist,2,"", 0.0025 ); # 2 = minimum peak sigma, 0.0025  = minimum min:max peak height ratio - see TSpectrum
		self.peakPositions = []
		if (self.numFoundPeaks > 0):
                        positionsTemp = self.spectrum.GetPositionX() 
                        for peak in range(self.numFoundPeaks): 
				if (positionsTemp[peak] > 1.0):
                                	self.peakPositions.append(positionsTemp[peak])
				else:
					self.numFoundPeaks -= 1 
                        self.peakPositions.sort() # put the peaks in ADC order, not the pulse height order ROOT returns	
			for i in range(self.numFoundPeaks):
				if (i > 0):
					gainGuess += self.peakPositions[i] - self.peakPositions[i-1]
			if (self.numFoundPeaks > 1):
				gainGuess = gainGuess/(self.numFoundPeaks - 1)	
				self.gain = gainGuess

	# Loop over peak positions found by findPeaks() and guess the gain by
	# taking the average distance between peaks - to replace the same code
	# implemented in findPeaks()
	def guessGains(self):

		for i in range(self.numFoundPeaks):
                        if (i > 0):
                        	gainGuess += self.peakPositions[i] - self.peakPositions[i-1]
                if (i > 0):
                	gainGuess = gainGuess/(self.numFoundPeaks - 1) 
                        self.gain = gainGuess
	
	# Make a rough fit of the pedestal, assuming it to be the first peaks in self.peakPositions
	# (largest by TSpectrum) and fit a Gaussian one half gain either side
	def fitPedestal(self):

		if (self.gain > 0):
			self.channel.adcHist.Fit("gaus","","",self.peakPositions[0] - (self.gain/2.0),self.peakPositions[0] + (self.gain/2.0) )
			self.channel.adcHist.Draw()
		else: 
			self.channel.adcHist.Fit("gaus")	
	
	# Perform the same as the pedestal peak fit, but for the second found peak
	def fitSinglesPeak(self):

		if (self.numFoundPeaks > 1):
			self.channel.adcHist.Fit("gaus","+","",self.peakPositions[1] - (self.gain/2.0),self.peakPositions[1] + (self.gain/2.0) )
                self.channel.adcHist.Draw()

	# Perform a Gaussian fit of width one gain to all peaks found by the peak finder
	def fitAllPeaks(self):

		params = ROOT.TArrayD(3*self.numFoundPeaks)
		if (self.numFoundPeaks > 1 and self.numFoundPeaks < 10):
			for i in range(self.numFoundPeaks):
				try:
					fitFunction = ROOT.TF1(numbers[i],"gaus",self.peakPositions[i] - (self.gain/2.0),self.peakPositions[i] + (self.gain/2.0))
					self.fitResults.append(fitFunction)
					self.channel.adcHist.Fit(fitFunction,"NR+")
					for p in range(3):
						param = fitFunction.GetParameter(p)
						params.AddAt(param,(i*3 + p))
				except:
					print "Failed to fit"
			#functionString = "gaus(0)"
			#for i in range(self.numFoundPeaks - 1):
			#	functionString += "+gaus(%i)" % (i*3 + 3)
			#allFits = ROOT.TF1("allPeaks",functionString,0,255)
			#allFits.SetParameters(params.GetArray())
			#self.channel.adcHist.Fit(allFits,"R+")
				#self.channel.adcHist.Fit("gaus","+","",self.peakPositions[i] - (self.gain/2.0),self.peakPositions[i] + (self.gain/2.0) )
		else:
			try:
                        	self.channel.adcHist.Fit("gaus")
			except:
				print "Failed again"
		self.channel.adcHist.Draw()

	def getCalculatedGain(self):

		gain = -1.0
		if (len(self.fitResults) > 0):
			gain += 1.0
			sum = 0.0
			num = 0.0
			for peak in range(len(self.fitResults)):
				if (peak > 0):
					sum += (self.fitResults[peak].GetParameter(1) - self.fitResults[peak - 1].GetParameter(1))
					num += 1.0
			gain += (sum / num)
		return gain

	# Calculate the integral of the bins one gain around each peak, and then for the whole
	# histogram above the final peak (with a width of one gain)
	def getIntegrals(self):

		self.totalIntegral = self.channel.adcHist.Integral(0,self.channel.adcHist.GetNbinsX())
		for i in range(self.numFoundPeaks):
			upperBin = self.channel.adcHist.FindBin(self.peakPositions[i] + (self.gain/2.0))
			lowerBin = self.channel.adcHist.FindBin(self.peakPositions[i] - (self.gain/2.0)) + 1
			self.integrals[i] = (self.channel.adcHist.Integral(lowerBin, upperBin))	
		if (self.numFoundPeaks > 0):
			lastUpperBin = self.channel.adcHist.FindBin(self.peakPositions[self.numFoundPeaks - 1] + (self.gain/2.0))
			self.integrals[i] = (self.channel.adcHist.Integral(lastUpperBin, self.channel.adcHist.GetNbinsX()))

	def getTotalCounts(self):
		return ( self.channel.adcHist.Integral(0,self.channel.adcHist.GetNbinsX() ) )	

	def getDarkCount(self, peakLocation = 0):

		peakLocation = 0
		darkCountRatio = 0.0
		if (peakLocation == 0):
			if (len(self.fitResults) > 0):
				peakLocation = self.fitResults[1].GetParameter(0)
		if (peakLocation == 0):	
			#if ((self.numFoundPeaks == 2) and (self.gain < 30)):
			if ((self.gain < 50) and (self.numFoundPeaks > 1) and (self.peakPositions[0] > 1)):
				lowerBin = self.channel.adcHist.FindBin(self.peakPositions[1]) - (self.gain/2.0)
				upperBin = self.channel.adcHist.FindBin(self.peakPositions[1]) + (self.gain/2.0)
				#upperBin = self.channel.adcHist.GetNbinsX()
				darkCount = self.channel.adcHist.Integral(lowerBin,upperBin)
				darkCountRatio = darkCount/( self.channel.adcHist.Integral(0,self.channel.adcHist.GetNbinsX() ) )
				self.channel.status = 1
			#elif ((self.numFoundPeaks > 3) or ( (self.numFoundPeaks == 2) and (self.gain < 30))):
			#	#print "Probably in breakdown"
			#	self.channel.status = 2
			elif (self.numFoundPeaks == 0):
				self.channel.status = 0
		else:
			lowerBin = self.channel.adcHist.FindBin(peakLocation)
                        upperBin = self.channel.adcHist.GetNbinsX()
                        darkCount = self.channel.adcHist.Integral(lowerBin,upperBin)
			darkCountRatio = darkCount/( self.channel.adcHist.Integral(0,self.channel.adcHist.GetNbinsX() ) )
		return darkCountRatio


	def savePlots(self, canvas):
		self.channel.adcHist.Draw()	
		self.channel.adcHist.Write()


	def getPE(self):	
		pe = 0.0
		if (self.numFoundPeaks > 1):
			pe = (self.channel.adcHist.GetMean() - self.peakPositions[0]) / self.gain
		if (self.gain > 0.0):
			return pe
		else:
			return 0.0



class LYCalibrator:
	def __init__(self, run):
		#print "Calibrating those photons"
		self.run = run

	def findPeaks(self):
		self.run.addPedestalFinders()

	def fitLEDPeaks(self):
		for channel in self.run.channelRuns:
			if ((channel.board == 1) and (channel.bank == 0) and (channel.channel < 5)):
				fitFunction = PEFunction(0,255,channel.finder.numFoundPeaks, channel.finder.peakPositions, channel.finder.gain)
				fitFunction.fitHistogram(channel.adcHist)




class PEFunction:

	def __init__(self, lowerLimit, UpperLimit, numPeaks, peakPositions, gain):
		self.numPeaks = numPeaks
		numParams = 4 + numPeaks*2
		#numParams = 0
		self.gain = gain
		self.peakPositions = peakPositions
		x = range(255)
		par = [10.0,20,10,30,40,50,5,5,5]
		self.function = ROOT.TF1("PeFunction",self.peFunction, lowerLimit, UpperLimit, numParams)


	def factorial(self, x):
		start = 1.0;
		for i in range(x - 1):
			start *= (i + 1)
		return start


	def fitHistogram(self, hist):
		#self.function.SetParameters(10.0, hist.GetMean(), hist.GetRMS())
		#hist.Fit(self.function)
		self.function.SetParameter(0,hist.Integral())
		self.function.SetParameter(1,2.0)
		self.function.SetParName(0,"Constant")
		self.function.SetParLimits(1,0.0,20.0)
		self.function.SetParName(1,"Mean PE")
		self.function.SetParameter(2,self.peakPositions[0])
		self.function.SetParName(2,"Pedestal")
		self.function.SetParLimits(2,self.peakPositions[0] - 20.0,self.peakPositions[0] + 20.0)
		self.function.SetParameter(3,hist.GetRMS())
		self.function.SetParLimits(3,5.0,25.0)
		self.function.SetParName(3,"Gain")
		for peak in range(self.numPeaks):
			self.function.SetParameter(peak+4, self.peakPositions[peak])
			self.function.SetParLimits(peak+4, self.peakPositions[peak] - 5, self.peakPositions[peak] + 5)
			self.function.SetParName(peak+4,"PE Peak " + str(peak))
			self.function.SetParameter(self.numPeaks + peak + 4, self.gain/2.0)
			self.function.SetParLimits(self.numPeaks + peak + 4, 0.0, 5.0)
			self.function.SetParName(self.numPeaks + peak + 4,"PE Peak RMS " + str(peak))
		self.function.SetNumberFitPoints(256)
		hist.Fit(self.function,"LM")

	# Poisson of Gaussians as fit function for photo electron peaks in ADC distribution
	# Value = ADC
	# Parameters: 0 = const 1 = meanPE, 2 = pedestal, 3 = gain
	# 3+ = list of means, then list of sigmas for peak Gaussians
	def peFunction(self, values, parameters):
		pe = (values[0] - parameters[2]) / parameters[3]
		if (pe < 0):
			pe = 0
		#pePoisson = ( pow(abs(parameters[1]),pe) * exp(-(abs(parameters[1]))) ) / self.factorial(int(pe))
		pePoisson = ROOT.TMath.Poisson(pe, parameters[1])
		gausSum = 0
		for peak in range(self.numPeaks):
			constant = 1 / ( sqrt(2*PI*( pow(parameters[4],2) )) )
			if (parameters[4] > 0.0):
				expArg = -(pow( (values[0] - ( parameters[2] + parameters[3]*peak)),2) / (2*pow(parameters[4],2)) )
			else:
				#print "sigma below 0"
				expArg = 1.0
			gausSum += constant*exp(expArg)
		return parameters[0]*pePoisson*gausSum

