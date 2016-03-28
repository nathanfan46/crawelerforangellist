#coding: utf-8

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from random import randint
#from time import sleep
import time
import datetime
import os.path
import io
import json
import platform
import sys
import zipfile
import string

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utility'))

from utility import *
from mailHelper import *

class spiderForAngellist:

	START_PAGE_URL = "https://angel.co/"

	LOGIN_URL = "https://angel.co/login?utm_source=top_nav_home"
	LOGIN_USERNAME = ""
	LOGIN_PASSWORD = ""

	PEOPLE_SYNDICATELEADS_URL = "https://angel.co/people/leads"
	PEOPLE_INVESTORS_URL = "https://angel.co/people/investors"	
	PEOPLE_INVESTMENTS_MORE_CSS = "div.more_button"
	PEOPLE_REFERENCES_MORE_CSS = "div.more"
	SYNDICATE_READ_MORE_CSS = "div.more"
	SYNDICATE_INVESTMENTS_MORE_CSS = "li.more"

	LOCATION_TAIWAN_URL = "https://angel.co/taiwan"

	MARKET_MORE_CSS = "a.items.section.more_button"
	MARKET_SUBNODE_CSS = "div#tags_list.section > div.items > div.clickable_area"

	STARTUP_PRODUCT_MORE_CSS = "a.hidden_more"
	STARTUP_PRODUCT_FUNDINGSTAGE_CSS = "a.more_participants_link"
	STARTUP_PRODUCT_PREINVEST_CSS = "a.view_all"
	STARTUP_ACTIVITY_NOMORE_CSS = "a.g-feed_more.more.disabled"
	STARTUP_ACTIVITY_PRESSITEM_CSS = "div.active.startups-show-helpers"
	STARTUP_FOLLOWERS_MORE_CSS = "a.g-feed_more.more"


	LOCAL_PAGR_CATEGORY_MAPPING_FILENAME = "categroyMapping.json"
	LOCAL_PAGR_LOCATION_MAPPING_FILENAME = "locationMapping.json"
	LOCAL_PAGR_MARKET_MAPPING_FILENAME = "marketMapping.json"
	LOCAL_PAGE_CHROME_EXTEND_FILENAME = "chromeextend.zip"
	LOCAL_PAGE_PROJECT_LIST_FILENAME = "ProjectListPage"
	LOCAL_PAGE_PEOPLE_SAVED_URLS_FILENAME = "PeopleSavedUrls.json" 
	LOCAL_PAGE_STARTUP_SAVED_URLS_FILENAME = "StartupsavedUrls.json"
	LOCAL_PAGE_SAVED_URLS_FILENAME = "savedUrls" 		#每次存完的網站會把url存下
	LOCAL_PAGE_ERROR_URLS_FILENAME = "errorList" 		#抓取發生錯誤的網頁
	LOCAL_PAGE_IGNORED_URL_FILENAME = "ignoredUrls" 	#若是已經結束募資的url，之後爬此網站會忽略，在saveProjectToLocalFile會建立其內容
	LOCAL_PAGE_SPONSOR_FILENAME = "proposer" 			#file name: "proposer_id.html" 
	LOCAL_PAGE_EXTENSION = ".html"
	LOCAL_PAGE_INFO_EXTENSION = ".txt"

	INT_SCROLL_TIMEOUT = 5

	def __init__(self):
		self.__driver = None
		self.__lstSavedUrls = []
		self.__lstSavedPeopleUrls = []
		self.__lstSavedStartupUrls = []
		self.__dicMarketUrls = {}
		self.__dicLocationUrls = {}
		self.__startTime = None
		self.__workPeriod = None
		self.__sleepPeriod = None
		#self.__lstIgnoredUrl = []

	def loadCategoryFromPage(self, driver):
		self.__driver = driver
		dicMapping = {}

		# Get Market mapping
		strMarketFilePath = spiderForAngellist.getMarketMappingFilePath()
		strLocationFilePath = spiderForAngellist.getLocationMappingFilePath()
		listMarket = []
		listLocation = []

		if(os.path.isfile(strMarketFilePath)):
			self.__dicMarketUrls = loadObjFromJsonFile(strMarketFilePath)
			for key in self.__dicMarketUrls: 
				if(key.strip() != ''):
					listMarket.append(key)
		else:
			self.__driver.get("https://angel.co/markets")

			self.autoClickMoreToExtendLst(spiderForAngellist.MARKET_MORE_CSS, "div#tags_list.section > div.items > div.item-tag")
			lstElementRight = self.__driver.find_elements_by_css_selector('div.item-tag > div.arrow_modifier.arrow_list_right')
			skippedIndex = 0
			lstclickedId = []

			while(len(lstElementRight) > skippedIndex):
				# Skip ALl market
				print('Total count of elementRight: ' + str(len(lstElementRight)))

				elementRight = lstElementRight[skippedIndex]


				if(elementRight.get_attribute("data-tag_id") in lstclickedId or not elementRight.is_displayed()):
					skippedIndex += 1
				else:
					elementClickable = elementRight.find_element_by_xpath('..').find_element_by_xpath('..').find_element_by_css_selector('div.clickable_area')
					self.__driver.execute_script("arguments[0].scrollIntoView();", elementClickable)
					self.__driver.execute_script("window.scrollBy(0,-250)")
					try:
						elementClickable.click()
					except Exception, e:
						import pdb; pdb.set_trace()
					lstclickedId.append(elementRight.get_attribute("data-tag_id"))

				wait = WebDriverWait(self.__driver, 10)
				wait.until(self.ajax_complete, "Timeout waiting for page to load")
				
				lstElementRight = self.__driver.find_elements_by_css_selector('div.item-tag > div.arrow_modifier.arrow_list_right')

			lstElement = self.__driver.find_elements_by_css_selector('div#tags_list.section > div.items > div.item-tag > a')

			for element in lstElement:
				if(element.text not in listMarket):
					self.__dicMarketUrls[element.text] = element.get_attribute('href')
					if(element.text.strip() != ''):
						listMarket.append(element.text)

			saveObjToJson(self.__dicMarketUrls, strMarketFilePath)

		# Get Location mapping
		if(os.path.isfile(strLocationFilePath)):
			self.__dicLocationUrls = loadObjFromJsonFile(strLocationFilePath)
			for key in self.__dicLocationUrls:
				if(key.strip() != ''): 
					listLocation.append(key)
		else:
			self.__driver.get("https://angel.co/locations")

			self.autoClickMoreToExtendLst(spiderForAngellist.MARKET_MORE_CSS, "div#tags_list.section > div.items > div.item-tag")
			lstElementRight = self.__driver.find_elements_by_css_selector('div.item-tag > div.arrow_modifier.arrow_list_right')
			skippedIndex = 0
			lstclickedId = []

			while(len(lstElementRight) > skippedIndex):
				# Skip ALl market
				print('Total count of elementRight: ' + str(len(lstElementRight)))

				elementRight = lstElementRight[skippedIndex]


				if(elementRight.get_attribute("data-tag_id") in lstclickedId or not elementRight.is_displayed()):
					skippedIndex += 1
				else:
					elementClickable = elementRight.find_element_by_xpath('..').find_element_by_xpath('..').find_element_by_css_selector('div.clickable_area')
					self.__driver.execute_script("arguments[0].scrollIntoView();", elementClickable)
					self.__driver.execute_script("window.scrollBy(0,-250)")
					try:
						elementClickable.click()
					except Exception, e:
						import pdb; pdb.set_trace()

					lstclickedId.append(elementRight.get_attribute("data-tag_id"))

				wait = WebDriverWait(self.__driver, 10)
				wait.until(self.ajax_complete, "Timeout waiting for page to load")
				
				lstElementRight = self.__driver.find_elements_by_css_selector('div.item-tag > div.arrow_modifier.arrow_list_right')

			lstElement = self.__driver.find_elements_by_css_selector('div#tags_list.section > div.items > div.item-tag > a')

			
			for element in lstElement:
				if(element.text not in listLocation):
					self.__dicLocationUrls[element.text] = element.get_attribute('href')
					if(element.text.strip() != ''):
						listLocation.append(element.text)


			strLocationFilePath = spiderForAngellist.getLocationMappingFilePath()
			saveObjToJson(self.__dicLocationUrls, strLocationFilePath)


		dicMapping['Location'] = listLocation	
		dicMapping['Market'] = listMarket
		dicMapping['People'] = ["SyndicateLeads", "Investors"]

		strFilePath = spiderForAngellist.getCategoryMappingFilePath()
		saveObjToJson(dicMapping, strFilePath)

		return dicMapping;


	def saveObjectsToLocalFile(self, driver, strDate, strCategory, strSubCategory, intCount = 0, isClearSavedUrls = False):
		self.__driver = driver

		if(strCategory == "Market"):
			strMarketFilePath = spiderForAngellist.getMarketMappingFilePath()
			if(os.path.isfile(strMarketFilePath)):
				self.__dicMarketUrls = loadObjFromJsonFile(strMarketFilePath)
		elif(strCategory == "Location"):
			strLocationFilePath = spiderForAngellist.getLocationMappingFilePath()
			if(os.path.isfile(strLocationFilePath)):
				self.__dicLocationUrls = loadObjFromJsonFile(strLocationFilePath)

		strUrl = self.getBaseStrUrl(strCategory, strSubCategory)
		self.__driver.get(strUrl)

		self.checkLoginStatus("a.auth.login")
		
		strSavedFileUrl = spiderForAngellist.strSavedUrlFilePath(strDate, strCategory, strSubCategory)
		#strIgnoredFileUrl = spiderForAngellist.strIgnoredUrlFilePath(strCategory, strSubCategory)
		if(isClearSavedUrls == True and os.path.isfile(strSavedFileUrl)):
			os.remove(strSavedFileUrl)			

		self.__lstSavedUrls = loadStrListInfo(strSavedFileUrl)

		strSavedPeopleFileUrl = spiderForAngellist.strSavedPeopleUrlFilePath()

		if(os.path.isfile(strSavedPeopleFileUrl)):
			self.__lstSavedPeopleUrls = loadObjFromJsonFile(strSavedPeopleFileUrl)

			self.__lstSavedPeopleUrls = list(set(self.__lstSavedPeopleUrls))

		strSavedStartupFileUrl = spiderForAngellist.strSavedStartupUrlFilePath()

		if(os.path.isfile(strSavedStartupFileUrl)):
			self.__lstSavedStartupUrls = loadObjFromJsonFile(strSavedStartupFileUrl)

			self.__lstSavedStartupUrls = list(set(self.__lstSavedStartupUrls))


		#self.__lstIgnoredUrl = loadStrListInfo(strIgnoredFileUrl

		# if self.setFilter(strCategory, strSubCategory) == False:
		# 	return

		lstStrUrl = []

		intTotalObjectCount = 0
		lstObjElement = self.getLstOfAllObjects(strCategory)
		print("[spiderForAngellist] Length of Objects: " + str(len(lstObjElement)))
		for objElement in lstObjElement:
			strUrl = objElement.find_element_by_css_selector("a").get_attribute("href")
			lstStrUrl.append(strUrl.encode("utf8"))

		for i in range(0, len(lstStrUrl), 1):
			#if(lstStrUrl[i] not in self.__lstSavedUrls and lstStrUrl[i] not in self.__lstIgnoredUrl):
			if(self.__startTime == None):
				self.__startTime = time.time()
				self.__workPeriod = 4 * 60 * 60 # randint(30, 60) * 60 #seconds
				self.__sleepPeriod = randint(30, 60)#12 * 60 * 60 #randint(30, 60) * 60 
			elif (time.time() - self.__startTime) > self.__workPeriod:
				print("[spiderForAngellist] Take a nap from: " + str(time.time()))
				time.sleep(self.__sleepPeriod)
				print("[spiderForAngellist] Continue to work from: " + str(time.time()))
				# import pdb; pdb.set_trace()
				self.__startTime = time.time()
				self.__workPeriod = randint(30, 60) * 60 #seconds
				self.__sleepPeriod = randint(30, 60) * 60 

			if(strCategory == "People" and lstStrUrl[i] in self.__lstSavedPeopleUrls):
				print("[spiderForAngellist] " + lstStrUrl[i] + " this person has been saved before")
			elif(strCategory == "Location" or strCategory == "Market") and lstStrUrl[i] in self.__lstSavedStartupUrls:
				print("[spiderForAngellist] " + lstStrUrl[i] + " this startup has been saved before")
			elif(lstStrUrl[i] not in self.__lstSavedUrls):
				self.saveObjectToLocalFile(lstStrUrl[i], strDate, strCategory, strSubCategory)
				print("[spiderForAngellist] " + str(i + 1).encode("utf8") + "/" + str(len(lstStrUrl)).encode("utf8"))
			else:
				print("[spiderForAngellist] " + lstStrUrl[i] + " has been saved")

		saveObjToJson(self.__lstSavedPeopleUrls, strSavedPeopleFileUrl)	

		saveObjToJson(self.__lstSavedStartupUrls, strSavedStartupFileUrl)


	def saveObjectToLocalFile(self, strUrl, strDate, strCategory, strSubCategory, driver = None):
		if(self.__driver == None):
			self.__driver = webdriver.Firefox()
			self.__driver.maximize_window()
		print("[spiderForAngellist] Saving " + strUrl + "...")			
		try:
			self.__driver.get(strUrl)

			if(strCategory == "People"):
				#save People page
				self.autoClickMoreToExtendLst(spiderForAngellist.PEOPLE_INVESTMENTS_MORE_CSS)
				self.autoClickMoreToExtendLst(spiderForAngellist.PEOPLE_REFERENCES_MORE_CSS)
				self.saveCurrentPage(spiderForAngellist.getPeopleLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
				#save Syndicate page
				lstElementSyndicate = self.__driver.find_elements_by_css_selector("div.back_syndicate_button")
				if(len(lstElementSyndicate) == 1):
					strSyndicateUrl = self.__driver.find_element_by_css_selector("div.back_syndicate_button > a").get_attribute("href")
					self.__driver.get(strSyndicateUrl)		
					#self.autoClickMoreToExtendLst(spiderForAngellist.SYNDICATE_READ_MORE_CSS) s
					self.autoClickMoreToExtendLst(spiderForAngellist.SYNDICATE_INVESTMENTS_MORE_CSS)
					self.saveCurrentPage(spiderForAngellist.getSyndicateLocalFilePath(strUrl, strDate, strCategory, strSubCategory))

				self.__lstSavedPeopleUrls.append(strUrl)

			if(strCategory == "Location" or strCategory == "Market"):
				#save Overview page
				self.autoClickMoreToExtendLst(spiderForAngellist.STARTUP_PRODUCT_MORE_CSS)
				self.autoClickMoreToExtendLst(spiderForAngellist.STARTUP_PRODUCT_FUNDINGSTAGE_CSS, '', True)
				self.autoClickMoreToExtendLst(spiderForAngellist.STARTUP_PRODUCT_PREINVEST_CSS, '', True)
				self.saveCurrentPage(spiderForAngellist.getOverviewLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
				elementActivityTab = self.__driver.find_element_by_css_selector("a.tab.activity")
				strActivityUrl = elementActivityTab.get_attribute("href")
				# divFinance = self.__driver.find_element_by_css_selector("div.past_financing.section")
				lstInverstorUrls = []

				if(self.check_exists_by_css_selector("div.past_financing.section > div.startups-show-sections > div.group > div.startup_roles.startup_profile_group")):
					divInverstors = self.__driver.find_element_by_css_selector("div.past_financing.section > div.startups-show-sections > div.group > div.startup_roles.startup_profile_group")
					lstInverstors = divInverstors.find_elements_by_css_selector("div.startup_roles.startup_profile > div.g-lockup.top.medium > div.photo > a.profile-link")
					for investor in lstInverstors:
						lstInverstorUrls.append(investor.get_attribute("href"))

				for investorUrl in lstInverstorUrls:
					if(investorUrl not in self.__lstSavedPeopleUrls):
						self.saveObjectToLocalFile(investorUrl, strDate, "People", "Investors")

				#save Activiey#Press page
				self.__driver.get(strActivityUrl)

				wait = WebDriverWait(self.__driver, 10)
				wait.until(self.ajax_complete, "Timeout waiting for page to load")

				elementActivityPressTab = self.__driver.find_element_by_css_selector("ul.g-sub_nav > li[data-tab='press'] > a")
				#strActivityPressUrl = elementActivityPressTab.get_attribute("href")
				#self.__driver.get(strActivityPressUrl)
				strCurrentUrl = self.__driver.current_url
				elementActivityPressTab.click()
				while (strCurrentUrl == self.__driver.current_url):
					time.sleep(5)

				wait = WebDriverWait(self.__driver, 10)
				wait.until(self.ajax_complete, "Timeout waiting for page to load")
				#self.scrollToExtendLst(spiderForAngellist.STARTUP_ACTIVITY_NOMORE_CSS) 
				self.scrollForCreatingAllItem(spiderForAngellist.STARTUP_ACTIVITY_PRESSITEM_CSS)
				self.saveCurrentPage(spiderForAngellist.getActivityPressLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
				#save Followers page
				elementFollowersTab = self.__driver.find_element_by_css_selector("a.tab.followers")
				strFollowersUrl = elementFollowersTab.get_attribute("href")
				self.__driver.get(strFollowersUrl)
				self.autoClickMoreToExtendLst(spiderForAngellist.STARTUP_FOLLOWERS_MORE_CSS)
				self.saveCurrentPage(spiderForAngellist.getFollowersLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
				#save investors
				self.__lstSavedStartupUrls.append(strUrl)
			
				    
			appendTextFile(strUrl, spiderForAngellist.strSavedUrlFilePath(strDate, strCategory, strSubCategory))
			return True

		except Exception, e:
			print("[spiderForAngellist] Failed! ErrorMessage:" + str(e))
			appendTextFile("[" + strUrl + "] " + repr(e), spiderForAngellist.strErrorListFilePath(strDate, strCategory, strSubCategory))
			# import pdb; pdb.set_trace()
			return False				

	def check_exists_by_css_selector(self, strCss):
		try:
			self.__driver.find_element_by_css_selector(strCss)
		except NoSuchElementException:
			return False
		return True

	def checkLoginStatus(self, strLoginCss):
		lstElementLogin = self.__driver.find_elements_by_css_selector(strLoginCss)
		if(len(lstElementLogin) == 1):
			strCurrentUrl = self.__driver.current_url
			self.__driver.get(spiderForAngellist.LOGIN_URL)
			username = self.__driver.find_element_by_id("user_email")
			password = self.__driver.find_element_by_id("user_password")
			username.send_keys(spiderForAngellist.LOGIN_USERNAME)
			password.send_keys(spiderForAngellist.LOGIN_PASSWORD)
			self.__driver.find_element_by_name("commit").click()
			self.__driver.get(strCurrentUrl)
		else:
			#import pdb; pdb.set_trace()		
			print("[spiderForAngellist] Already Login!")

	def ajax_complete(self, driver):
		print("[spiderForAngellist] waiting for AJAX complete")
		try:
			time.sleep(0.1)
			return 0 == driver.execute_script("return jQuery.active")
		except WebDriverException:
			pass

	def wait_for(self, condition_function, link):
		start_time = time.time()
		while time.time() < start_time + 3:
			if condition_function(link):
				return True
			else:
				time.sleep(0.1)
		raise Exception(
			'Timeout waiting for {}'.format(condition_function.__name__)
		)

	def link_has_gone_stale(self, link):
		print("[spiderForAngellist] waiting for link stale")
		try:
			# poll the link with an arbitrary call
			link.get_attribute("href")
			return False
		except StaleElementReferenceException:
			return True

	def autoClickMoreToExtendLst(self, strMoreCss, strItemCss = '', waitForStale = False):
		wait = WebDriverWait(self.__driver, 10)
		# element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, strMoreCss)))
		wait.until(self.ajax_complete, "Timeout waiting for page to load")
		lstElementMore = self.__driver.find_elements_by_css_selector(strMoreCss)
		lstElementNoMore = self.__driver.find_elements_by_css_selector(strMoreCss + ".disabled")
		#print "wait CSS: " + strMoreCss + " has count: " + str(len(lstElementMore))
		intMoreCount = 0
		#while(len(lstElementMore) == 1):
		while(len(lstElementMore) >= 1):
			elementMore = lstElementMore[0]
			intMoreCount += 1

			intItemCount = 0

			if(strItemCss != ''):
				intItemCount = len(self.__driver.find_elements_by_css_selector(strItemCss))


			if(len(lstElementMore) == 1 and len(lstElementNoMore) == 1 and lstElementMore[0] == lstElementNoMore[0]):
				print "The more element is disabled"
				break

			if(elementMore.is_displayed() and elementMore.is_enabled()): #Avoid click on hidden element
				self.__driver.execute_script("arguments[0].scrollIntoView();", elementMore)
				self.__driver.execute_script("window.scrollBy(0,-250)")
				elementMore.click()
				# actions = ActionChains(self.__driver)
				# actions.move_to_element(elementMore)
				# actions.click(elementMore)
				# actions.perform()
			elif(not elementMore.is_enabled()):
				print "The more element is disabled"
				break
			else:
				print "The more element is hidden"
				break

			wait.until(self.ajax_complete, "Timeout waiting for page to load")

			if(waitForStale):
				self.wait_for(self.link_has_gone_stale, elementMore)

			if(strItemCss != ''):
				intLastItemCount = intItemCount
				intItemCount = len(self.__driver.find_elements_by_css_selector(strItemCss))
				if(intItemCount == intLastItemCount):
					print "No more item generated, the itemCount is : " + str(intItemCount)
					break

			#while lstElementMore == self.__driver.find_elements_by_css_selector(strMoreCss):
				# 按下 div.more_field 執行的 ajax 完成後會產生新的, 因此以判斷是不是同一個 element, 來決定是否繼續
				#print "wait..."
				#sleep(0.05)

			
			print "more #" + str(intMoreCount)
			# self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

			lstElementMore = self.__driver.find_elements_by_css_selector(strMoreCss)
			lstElementNoMore = self.__driver.find_elements_by_css_selector(strMoreCss + ".disabled")
			#print "wait CSS: " + strMoreCss + " has count: " + str(len(lstElementMore))

	def scrollToExtendLst(self, strNoMoreCss):
		wait = WebDriverWait(self.__driver, 10)
		wait.until(self.ajax_complete, "Timeout waiting for page to load")
		lstElementNoMore = self.__driver.find_elements_by_css_selector(strNoMoreCss)
		print "wait Nomore CSS: " + strNoMoreCss + " has count: " + str(len(lstElementNoMore))
		while(len(lstElementNoMore) == 0):	
			self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			wait.until(self.ajax_complete, "Timeout waiting for page to load")
			lstElementNoMore = self.__driver.find_elements_by_css_selector(strNoMoreCss)
			print "wait Nomore CSS: " + strNoMoreCss + " has count: " + str(len(lstElementNoMore))

	def scrollForCreatingAllItem(self, strItemCss): #適用於網頁往下滑即可產生列表物件的頁面，輸入生成物件的css selector字串
		fCurTime = 0
		intLastItemCount = 0
		# sometimes angellist will have bug for scroll down ajax
		intScrollCount = 0
		intScrollLimit = 10 
		while True:
			intCurItemCount = len(self.__driver.find_elements_by_css_selector(strItemCss))
			if fCurTime > self.INT_SCROLL_TIMEOUT or intScrollCount > intScrollLimit:
				break
			elif intCurItemCount > intLastItemCount:
				intLastItemCount = intCurItemCount
				self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
				intScrollCount += 1
				fCurTime = 0
			else:
				fCurTime = fCurTime + 0.5
				time.sleep(0.5)

	def getLstOfAllObjects(self, strCategory):
		wait = WebDriverWait(self.__driver, 10)
		wait.until(self.ajax_complete, "Timeout waiting for page to load")
		lstObjElement = []
		if(strCategory == "People"):
			self.autoClickMoreToExtendLst("div.more_field", "div.people-list[data-_tn='people/list/row']")
			return self.__driver.find_elements(By.CSS_SELECTOR, "div.people-list[data-_tn='people/list/row']")
		elif(strCategory == "Location"):
			self.autoClickMoreToExtendLst("div.more.hidden", "div.item.column > div.g-lockup > div.photo")
			return self.__driver.find_elements(By.CSS_SELECTOR, "div.item.column > div.g-lockup > div.photo")
		elif(strCategory == "Market"):
			self.autoClickMoreToExtendLst("div.more.hidden", "div.item.column > div.g-lockup > div.photo")
			return self.__driver.find_elements(By.CSS_SELECTOR, "div.item.column > div.g-lockup > div.photo")
		else:
			return lstObjElement;

	def getBaseStrUrl(self, strCategory, strSubCategory):
		strUrl = spiderForAngellist.START_PAGE_URL
		if(strCategory == "People"):
			if(strSubCategory == "SyndicateLeads"):
				strUrl = spiderForAngellist.PEOPLE_SYNDICATELEADS_URL
			elif(strSubCategory == "Investors"):
				strUrl = spiderForAngellist.PEOPLE_INVESTORS_URL

		if(strCategory == "Location"):
			strUrl = self.__dicLocationUrls[strSubCategory]
			# if(strSubCategory == "Taiwan"):
			# 	strUrl = spiderForAngellist.LOCATION_TAIWAN_URL

		if(strCategory == "Market"):
			strUrl = self.__dicMarketUrls[strSubCategory]

		return strUrl

	def saveCurrentPage(self, strFilePath):
		strData = self.__driver.page_source.encode('utf8')
		overwriteTextFile(strData, strFilePath)

	@staticmethod
	def strLocalPagePath():
		if(os.name == "nt"):
			# return "C:/Users/Nathan/Documents/SavedPage/"
			return "C:/Users/Administrator/Documents/SavedPage/"
		elif(os.name == "posix"):
			return "/Users/yuwei/Desktop/LocalPage/angellist/"

	@staticmethod				
	def strSavedDirectory(strDate, strCategory, strSubCategory):							#本次已抓取url列表
		return spiderForAngellist.strLocalPagePath() + "/" + strDate + "/" + strCategory + "/" + strSubCategory

	@staticmethod				
	def strSavedUrlFilePath(strDate, strCategory, strSubCategory):							#本次已抓取url列表
		return spiderForAngellist.strLocalPagePath() + "/" + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForAngellist.LOCAL_PAGE_SAVED_URLS_FILENAME + spiderForAngellist.LOCAL_PAGE_INFO_EXTENSION


	@staticmethod				
	def strSavedPeopleUrlFilePath():							#本次已抓取url列表
		return spiderForAngellist.strLocalPagePath() + "/" + spiderForAngellist.LOCAL_PAGE_PEOPLE_SAVED_URLS_FILENAME

	@staticmethod				
	def strSavedStartupUrlFilePath():							#本次已抓取url列表
		return spiderForAngellist.strLocalPagePath() + "/" + spiderForAngellist.LOCAL_PAGE_STARTUP_SAVED_URLS_FILENAME
		

	@staticmethod				
	def strErrorListFilePath(strDate, strCategory, strSubCategory):							#error列表
		return spiderForAngellist.strLocalPagePath() + "/" + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForAngellist.LOCAL_PAGE_ERROR_URLS_FILENAME + spiderForAngellist.LOCAL_PAGE_INFO_EXTENSION


	@staticmethod
	def getPeopleLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 	#People
		strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		return spiderForAngellist.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + strObjectID + "_people" + spiderForAngellist.LOCAL_PAGE_EXTENSION

	@staticmethod
	def getSyndicateLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 	#People
		strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		return spiderForAngellist.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + strObjectID + "_syndicates" + spiderForAngellist.LOCAL_PAGE_EXTENSION

	@staticmethod
	def getOverviewLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 	#Startup
		strObjectID = getFileNameInUrl(strUrl)
		return spiderForAngellist.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + strObjectID + "_overview" + spiderForAngellist.LOCAL_PAGE_EXTENSION

	@staticmethod
	def getActivityPressLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 	#Startup
		strObjectID = getFileNameInUrl(strUrl)
		return spiderForAngellist.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + strObjectID + "_activitypress" + spiderForAngellist.LOCAL_PAGE_EXTENSION

	@staticmethod
	def getFollowersLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 	#Startup
		strObjectID = getFileNameInUrl(strUrl)
		return spiderForAngellist.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + strObjectID + "_followers" + spiderForAngellist.LOCAL_PAGE_EXTENSION		
	
	@staticmethod
	def getCategoryMappingFilePath():
		return spiderForAngellist.strLocalPagePath() + spiderForAngellist.LOCAL_PAGR_CATEGORY_MAPPING_FILENAME

	@staticmethod
	def getLocationMappingFilePath():
		return spiderForAngellist.strLocalPagePath() + spiderForAngellist.LOCAL_PAGR_LOCATION_MAPPING_FILENAME

	@staticmethod
	def getMarketMappingFilePath():
		return spiderForAngellist.strLocalPagePath() + spiderForAngellist.LOCAL_PAGR_MARKET_MAPPING_FILENAME

	@staticmethod
	def getChromeExtendFilePath():
		return spiderForAngellist.strLocalPagePath() + spiderForAngellist.LOCAL_PAGE_CHROME_EXTEND_FILENAME

	@staticmethod
	def getPureUrl(strUrl): 										#從專案的url去掉"?ref_XXX"等字樣
		strUrl = strUrl[0:strUrl.rfind('?')]
		return strUrl

	@staticmethod
	def getCategoryMapping(spider = None, driver = None):
		strFilePath = spiderForAngellist.getCategoryMappingFilePath()
		if(os.path.isfile(strFilePath)):
			dicMapping = loadObjFromJsonFile(strFilePath)
			return dicMapping
		else:
			if(driver == None):
				chromedriver = "C:/Python27/Scripts/chromedriver.exe"
				os.environ["webdriver.chrome.driver"] = chromedriver
				driver = webdriver.Chrome(chromedriver)
				driver.maximize_window()

			if(spider == None):
				spider = spiderForAngellist()

			dicMapping = spider.loadCategoryFromPage(driver);

			return dicMapping


	@staticmethod
	def create_proxyauth_extension(proxy_host, proxy_port, proxy_username, proxy_password, scheme='http', plugin_path=None):

		if plugin_path is None:
			plugin_path = spiderForAngellist.getChromeExtendFilePath()

		background_js = string.Template(
		"""
			var config = {
				mode: "fixed_servers",
				rules: {
					singleProxy: {
						scheme: "${scheme}",
						host: "${host}",
						port: parseInt(${port})
					},
					bypassList: ["foobar.com"]
				}
			};

			chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

			function callbackFn(details) {
				return {
					authCredentials: {
						username: "${username}",
						password: "${password}"
					}
				};
			}

			chrome.webRequest.onAuthRequired.addListener(
				callbackFn,
				{urls: ["<all_urls>"]},
				['blocking']
			);
		"""
		).substitute(
		    host=proxy_host,
		    port=proxy_port,
		    username=proxy_username,
		    password=proxy_password,
		    scheme=scheme,
		)

		manifest_json = """
		{
		    "version": "1.0.0",
		    "manifest_version": 2,
		    "name": "Chrome Proxy",
		    "permissions": [
		        "proxy",
		        "tabs",
		        "unlimitedStorage",
		        "storage",
		        "<all_urls>",
		        "webRequest",
		        "webRequestBlocking"
		    ],
		    "background": {
		        "scripts": ["background.js"]
		    },
		    "minimum_chrome_version":"22.0.0"
		}
		"""

		with zipfile.ZipFile(plugin_path, 'w') as zp:
			zp.writestr("manifest.json", manifest_json)
			zp.writestr("background.js", background_js)

		return plugin_path


	@staticmethod
	def saveAllObjectsOfCategory(strDate, strCategory, lstStrSubCategory = [], isClearSavedUrls = False):
		spider = spiderForAngellist()
		# driver = webdriver.Firefox()

		# For using tor
		# chrome_options = webdriver.ChromeOptions()
		# chrome_options.add_argument('--proxy-server=http://127.0.0.1:8118')

		# For using authenticated proxy
		# proxyauth_plugin_path = spiderForAngellist.create_proxyauth_extension(
		# 	proxy_host="us-dc.proxymesh.com",
		# 	proxy_port=31280,
		# 	proxy_username="",
		# 	proxy_password=""
		# )

		# co = Options()
		# co.add_argument("--start-maximized")
		# co.add_extension(proxyauth_plugin_path)
			
		
		chromedriver = "C:/Python27/Scripts/chromedriver.exe"
		os.environ["webdriver.chrome.driver"] = chromedriver
		driver = webdriver.Chrome(chromedriver)
		# driver = webdriver.Chrome(executable_path=chromedriver,chrome_options=chrome_options)
		# driver = webdriver.Chrome(chrome_options=co)

		# firefox_capabilities = DesiredCapabilities.FIREFOX
		# firefox_capabilities['marionette'] = True
		# firefox_capabilities['binary'] = 'C:/Python27/Scripts/wires.exe'
		# driver = webdriver.Firefox(capabilities=firefox_capabilities)

		driver.maximize_window()
		if len(lstStrSubCategory) == 0:
			dicMapping = spiderForAngellist.getCategoryMapping(spider, driver)
			# import pdb; pdb.set_trace()
			for strSubCategoryInMapping in dicMapping[strCategory]:
				spider.saveObjectsToLocalFile(driver, strDate, strCategory, strSubCategoryInMapping, isClearSavedUrls)
		else:
			for strSubCategory in lstStrSubCategory:
				spider.saveObjectsToLocalFile(driver, strDate, strCategory, strSubCategory, isClearSavedUrls)


def main():
	#spiderForAngellist.saveAllObjectsOfCategory("2016-02-25", "Location", ["Taiwan"])
	#spiderForAngellist.saveAllObjectsOfCategory("2016-02-25", "People", ["SyndicateLeads", "Investors"])
	spiderForAngellist.saveAllObjectsOfCategory("2016-03-15", "People", ["Investors"])
	

if __name__ == '__main__':
	main()