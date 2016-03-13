#coding: utf-8
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utility'))
#sys.path.append("/Users/yuwei/Desktop/github/tier/spiders/utility")

import utility
import mailHelper
from spiderForAngellist import *

if __name__ == '__main__':
	config = loadObjFromJsonFile(os.path.dirname(os.path.abspath(__file__)) + "/spiderForAngellist_config.json")
	strCategory = config["strCategory"]
	spiderForAngellist.saveAllObjectsOfCategory("2016-03-13", strCategory)
	mailHelper.send("All Objects Of [" + strCategory + "] Are Saved!", config["strMachine"], "me", "", config["lstStrMail"])