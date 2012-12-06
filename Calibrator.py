from Helpers import *

# Base class for calibrator types
class Calibrator(object):

	def __init__(self):
		self.processes = ProcessDictionary()
		self.globalParameters = {}
	# Setup - defined in child classes
	def setup(self):
		pass
	# Setup - defined in child classes
	def loadDataCampaign(self):
		pass
	
	# Add a process (function) to the lis that will be executed by
	# this calibrator
	def addProcess(self, name, process, parameters = None):
		if (parameters is not None):
			self.processes[name] = process
			self.globalParameters[name] = parameters
		else:
			self.processes[name] = process
	
	# Add a seperate parameter to the global list used
	# by the processes
	def addParameter(self, name, parameter):
		self.globalParameters[name] = parameter

	# Loop over all processes in the dicionary
	# execute the process with its arguments,
	# if they are defined
	def runProcesses(self):	
		for name in self.processes:
			process = self.processes[name] # this is a function
			print "Running " + str(name)
			if name in self.globalParameters:
				process(self.globalParameters[name]) # execute with arguments
			else:
				process() # execute

if __name__ == "__main__":

	print "here"
	d = ProcessDictionary()
	c = Calibrator()
	d["test"] = 1
	d["test2"] = 3
	d["test3"] = 6
	for k in d:
		print d[k]
