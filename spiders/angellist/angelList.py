# coding: utf8

from selenium import webdriver 
from selenium.webdriver.common.by import By
from scrapy import Selector
import re, time
from os import listdir

STR_TYPE_PEOPLE = "people"

# unicode string to utf8 for saving to files: u.encode("utf8")

def getLstStrURLPeopleByStrURLType(driver, strURLType):
	driver.get(strURLType)

	elementTotal = driver.find_elements(By.CSS_SELECTOR, "div[data-_tn='people/list/header'] div.s-grid0-colLg11")[0]
	print re.search("\d+", elementTotal.text, re.MULTILINE).group()

	lstStrURLPeople = []
	lstElementMore = driver.find_elements_by_css_selector("div.more_field")
	intPeopleCount = 0
	intMoreCount = 0
	while (len(lstElementMore) == 1):
		elementMore = lstElementMore[0]
		intMoreCount += 1
		elementMore.click()
		while lstElementMore == driver.find_elements_by_css_selector("div.more_field"):
			# 按下 div.more_field 執行的 ajax 完成後會產生新的, 因此以判斷是不是同一個 element, 來決定是否繼續
			print "wait..."
			time.sleep(0.05)
		print "more #" + str(intMoreCount)
		driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		lstElementMore = driver.find_elements_by_css_selector("div.more_field")

	elementPeople = driver.find_elements(By.CSS_SELECTOR, "div.people-list[data-_tn='people/list/row']")
	for elementPerson in elementPeople:
		anchor = elementPerson.find_elements_by_css_selector("div.name a")[0]
		intPeopleCount += 1
		strName = anchor.text
		strURL = anchor.get_attribute("href")
		print str(intPeopleCount) + " " + strName + " -> " + anchor.get_attribute("href")
		lstStrURLPeople.append(strURL.encode("utf8"))
	return lstStrURLPeople

def getStrPageSourcePeopleByStrURLPeople(driver, strURLPeople):
	driver.get(strURLPeople)
	strPeopleId = strURLPeople[strURLPeople.rindex("/") + 1 : strURLPeople.index("?")]
	strPageSource = driver.page_source.encode("utf8")
	saveStrPageSourceByStrIdAndStrType(strPeopleId, STR_TYPE_PEOPLE, strPageSource)

def saveStrPageSourceByStrIdAndStrType(strId, strType, strPageSource):
	with open(strType + "/" + strId, "wb") as file:
		file.write(strPageSource)
		print strId + " saved"

def parsePagePeopleByStrId(StrId):
	strPageSource = None
	with open(STR_TYPE_PEOPLE + "/" + StrId, "rb") as file:
		strPageSource = file.read()
	root = Selector(text=strPageSource)

	print "Name: " + str(root.xpath("//h1[@itemprop='name']/text()").extract_first().strip())

	strSyndicate = root.xpath("//a[@href='/" + StrId + "/syndicate' and @class='u-uncoloredLink']/text()").extract_first().strip()

	matched = re.search(r"([\d|,]+) Backers\n\((.+)\)", strSyndicate, re.MULTILINE)
	print "Backers: " + str(matched.groups()[0])
	print "Backed by: " + str(matched.groups()[1])

if __name__ == "__main__":
	STR_URL_START = "https://angel.co/people/leads"

	option = webdriver.ChromeOptions()
	option.add_argument('test-type')
	driver = webdriver.Chrome("/Users/yuwei/Documents/Webdriver/chromedriver")
	driver.maximize_window()
	
	lstStrURLPeople = getLstStrURLPeopleByStrURLType(driver, STR_URL_START)

	strLstStrURLPeople = str(lstStrURLPeople)
	strLstStrURLPeople = strLstStrURLPeople.replace(", ", "\n")[1:-1].replace("'", "")
	saveStrPageSourceByStrIdAndStrType("lstStrURLPeople", STR_TYPE_PEOPLE, strLstStrURLPeople)

	lstStrURLPeople = []
	with open(STR_TYPE_PEOPLE + "/lstStrURLPeople", "rb") as file:
		for strURLPeople in file:
			strURLPeople = strURLPeople.replace("\n", "").strip()
			if len(strURLPeople) == 0:
				continue
			lstStrURLPeople.append()

	for strURLPeople in lstStrURLPeople:
		getStrPageSourcePeopleByStrURLPeople(driver, strURLPeople)

	lstStrId = [f for f in listdir(STR_TYPE_PEOPLE) if f != 'lstStrURLPeople']
	for strId in lstStrId:
		parsePagePeopleByStrId(strId)
