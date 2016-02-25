#coding: utf-8
import os.path
import sys
sys.path.append("/Users/yuwei/Desktop/github/tier/spiders/utility")

import utility
import mailHelper
from spiderForKickstarter import *

if __name__ == '__main__':
	spider = spiderForKickstarter()
	spider.saveProjectToLocalFile(u"https://www.kickstarter.com/projects/tsandcompany/help-ts-and-company-grow", str(datetime.date.today()).encode('utf8'), "Film & Video", "Animation")
