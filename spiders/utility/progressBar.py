#coding: utf-8
import io
import sys
import math
from time import sleep
from progressBar import *

class ProgressBar:
	__barWidth = 40;
	__progressLabel = "░"

	def __init__(self):
		self.__fProgress = 0
		self.__iCurProgressLabelCount = 0
		
	def show(self, strLabel):
		sys.stdout.write((strLabel + "[%s]") % (" " * self.__barWidth))
		sys.stdout.flush()
		sys.stdout.write("\b" * (self.__barWidth+1))

	def setProgress(self, progress):
		newProgressLabelCount = int(math.floor(progress * self.__barWidth))
		if newProgressLabelCount >= self.__iCurProgressLabelCount:
			for i in range(self.__iCurProgressLabelCount, newProgressLabelCount, 1):
				sys.stdout.write(self.__progressLabel)
			self.__iCurProgressLabelCount = newProgressLabelCount
			sys.stdout.flush()

	def finish(self):
		sys.stdout.write("\n")

#Example
def main():	
	pb = ProgressBar()
	pb.show("Progress\n")
	for i in xrange(40):
		sleep(0.1)
		pb.setProgress(float(i+1)/40)
	pb.finish()

if __name__ == '__main__':
	main()
