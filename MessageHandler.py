import sys
import fcntl
import termios
import threading
import time
import struct

COLS = struct.unpack('hh',  fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, '1234'))[1]

class MessageHandler:

	def __init__(self):
		pass

	def bold(self, msg):
		return u'\033[1m%s\033[0m' % msg

	def progress(self, current, total, type):
	
		prefix = '%d / %d %s' % (current, total, type)
		bar_start = ' ['
		bar_end = '] '
		bar_size = COLS - len(prefix + bar_start + bar_end)
		amount = int(current / (total / float(bar_size)))
		remain = bar_size - amount
		bar = '.' * amount + ' ' * remain
		return self.bold(prefix) + bar_start + bar + bar_end

	def progressBar(self, number, total, interval, type):
		#NUM = 100
		number += 1
		#for i in range(NUM + 1):
		if (not (number % interval)):
			sys.stdout.write(self.progress(number, total, type) + '\r')
			sys.stdout.flush()
		#time.sleep(0.05)
		
	def end(self):
		print ""

#mh = MessageHandler()
#for i in range(100):
#	mh.progressBar(i, 100, "Histogram")
#print ""
