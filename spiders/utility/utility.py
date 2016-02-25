
#coding: utf-8
import os
import os.path
import io
import json
import sys
import math
from selenium import webdriver

def checkElementExist(driver, strCssSelector):
	return len(driver.find_elements_by_css_selector(strCssSelector)) > 0

def loadObjFromJsonFile(filePath):
	if os.path.isfile(filePath) == True:
		with open(filePath, 'r') as jsonfile:
			jsonData = json.loads(jsonfile.read(), encoding='utf-8')
		return jsonData
	else:
		return None

#讀取字串列表檔案
def loadStrListInfo(strFilePath): 									
	strList = []
	if(os.path.isfile(strFilePath) == True):
		with open(strFilePath) as f:
			for line in f:
				strList.append(purifyString(line))
	return strList

#save object object to json file
def saveObjToJson(dicData, strOutputPath):
	overwriteTextFile(json.dumps(dicData, ensure_ascii = False).encode('utf8'), strOutputPath)
	return

#save string to file
def overwriteTextFile(strData, strOutputPath):
	directory = strOutputPath[0:strOutputPath.rfind('/')]
	if not os.path.exists(directory):
		os.makedirs(directory)
	with io.open(strOutputPath, "wb") as file:
		file.write(strData)

def appendTextFile(strData, strOutputPath):
	directory = strOutputPath[0:strOutputPath.rfind('/')]
	if not os.path.exists(directory):
		os.makedirs(directory)
	with open(strOutputPath, "a") as file:
		file.write(strData + "\n")

def printStringList(strList):
	print(', '.join(strList))

def purifyString(strOri):
	str = strOri.replace("\n", "")
	str = str.strip()
	return str

#return "filename" from "XXXX/XXXX/XXXX/filename.XXXX"
def getFileNameInUrl(str):
	idIndex = str.rfind('/')+1
	dotIndex = str.rfind('.')
	if dotIndex == -1 or dotIndex < idIndex:
		dotIndex = len(str)
	return str[idIndex:dotIndex]

if __name__ == '__main__':
	print("[Test for getFileNameInUrl]:")
	inStr = "XXXX/XXXX/XXXX/filename"
	out = getFileNameInUrl(inStr)
	print(inStr + " to " + out)

