#coding: utf-8
import os.path
import sys
sys.path.append("/Users/yuwei/Desktop/github/tier/spiders/utility")

import utility
import mailHelper
from spiderForKickstarter import *

if __name__ == '__main__':
	config = loadObjFromJsonFile(os.path.dirname(os.path.abspath(__file__)) + "/spiderForKickstarter_config.json")
	strCategory = config["strCategory"]
	spiderForKickstarter.saveAllProjectsOfCategory("2016-02-16", strCategory)
	mailHelper.send("Projects Of [" + strCategory + "] Are Saved!", config["strMachine"], "me", "", config["lstStrMail"])