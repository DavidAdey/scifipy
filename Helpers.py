import inspect
# Modification of dictionary class for processes
class ProcessDictionary(object):

	def __init__(self):
		self.items = {}
		self.order = []

	def __setitem__(self, key, item):
		#order = 1
		self.items[key] = item
		#if (order > len(self.order)):
		#	addition = [0 for x in range(order - len(self.order) + 1)]	
		#	self.order.extend(addition)	
		self.order.append(key)

	def __getitem__(self, key):
		try:
			return self.items[key]
		except:
			raise AttributeError

	def __iter__(self):
		return iter(self.order)
		
def line():
	return inspect.currentframe().f_back.f_lineno

def file():
	return inspect.getfile(inspect.currentframe()) # script filename (usually with path)


print line()
print file()
print line()	
