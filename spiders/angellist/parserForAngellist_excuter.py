#coding: utf-8
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utility'))
#sys.path.append("/Users/yuwei/Desktop/github/tier/spiders/utility")

import utility
import mailHelper
from parserForAngellist import *

if __name__ == '__main__':
	config = loadObjFromJsonFile(os.path.dirname(os.path.abspath(__file__)) + "/parserForAngellist_config.json")
	# strCategory = config["strCategory"]
	# parserForAngellist.parseAllObjectsOfCategory("2016-03-13", strCategory)
	parserForAngellist.parseAllObjectsOfCategory("2016-03-13", "People")
	parserForAngellist.parseAllObjectsOfCategory("2016-03-13", "Location")
	#mailHelper.send("All Objects Of [" + strCategory + "] Are Parsed!", config["strMachine"], "me", "", config["lstStrMail"])