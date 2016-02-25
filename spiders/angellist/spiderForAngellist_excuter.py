#coding: utf-8
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utility'))
#sys.path.append("/Users/yuwei/Desktop/github/tier/spiders/utility")

import utility
import mailHelper
from spiderForAngelist import *

if __name__ == '__main__':
	config = loadObjFromJsonFile(os.path.dirname(os.path.abspath(__file__)) + "/spiderForAngellist_config.json")
	strCategory = config["strCategory"]
	spiderForAngelist.saveAllProjectsOfCategory("2016-02-16", strCategory)
	mailHelper.send("Projects Of [" + strCategory + "] Are Saved!", config["strMachine"], "me", "", config["lstStrMail"])