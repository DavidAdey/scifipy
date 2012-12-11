
# Run.py
# Script to run calibration of trackers given an input file and plot ADC histograms
#
# D. Adey March 2011

import string
import sys
sys.path.append("../")
import Base
import ROOT
import GainCalibrator

# Get input file
file = sys.argv[1]
path = sys.argv[2]
# Setup ROOT
ROOT.gROOT.Reset()
ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetPalette(1)
c1 = ROOT.TCanvas( 'c1', 'ADC', 200, 10, 700, 500 )
ROOT.gStyle.SetOptStat("RMe")
ROOT.gStyle.SetOptFit()

fileName = str(file)
if (string.count(fileName,"gdc")):
	fileName = string.lstrip(fileName,"gdc")
if (string.count(fileName,"dat")):
	fileName = string.rstrip(fileName,".dat")
if (string.count(fileName,".000")):
	fileName = string.rstrip(fileName,".000")

tfile = ROOT.TFile(fileName + ".root","recreate")

# Create Run
run = Base.Run()
run.setName(file)
run.setup()

# Create file reader
reader = Base.DATEReader(path + file)
print file

# Read file into Run
reader.readBinary(run, "cosmic")

# Add peak finders and measure pedestals
run.addPedestalFinders(fit=1)
run.writePeakLocations()
run.qualityCheck()
run.save(c1)
run.clear()
tfile.Write()
tfile.Close()
