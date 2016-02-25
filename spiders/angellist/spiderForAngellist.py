#coding: utf-8

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from time import sleep
import datetime
import os.path
import io
import json
import platform
import sys

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

	STARTUP_PRODUCT_MORE_CSS = "a.hidden_more"
	STARTUP_PRODUCT_FUNDINGSTAGE_CSS = "a.more_participants_link"
	STARTUP_PRODUCT_PREINVEST_CSS = "a.view_all"
	STARTUP_ACTIVITY_NOMORE_CSS = "a.g-feed_more.more.disabled"
	STARTUP_FOLLOWERS_MORE_CSS = "a.g-feed_more.more"


	LOCAL_PAGR_CATEGORY_MAPPING_FILENAME = "categroyMapping.json"
	LOCAL_PAGE_PROJECT_LIST_FILENAME = "ProjectListPage"
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
		#self.__lstIgnoredUrl = []

	def saveObjectsToLocalFile(self, driver, strDate, strCategory, strSubCategory, intCount = 0, isClearSavedUrls = False):
		self.__driver = driver
		strUrl = self.getBaseStrUrl(strCategory, strSubCategory)
		self.__driver.get(strUrl)

		self.checkLoginStatus("a.auth.login")
		
		strSavedFileUrl = spiderForAngellist.strSavedUrlFilePath(strDate, strCategory, strSubCategory)
		#strIgnoredFileUrl = spiderForAngellist.strIgnoredUrlFilePath(strCategory, strSubCategory)
		if(isClearSavedUrls == True and os.path.isfile(strSavedFileUrl)):
			os.remove(strSavedFileUrl)			

		self.__lstSavedUrls = loadStrListInfo(strSavedFileUrl)
		#self.__lstIgnoredUrl = loadStrListInfo(strIgnoredFileUrl)

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
			if(lstStrUrl[i] not in self.__lstSavedUrls):
				self.saveObjectToLocalFile(lstStrUrl[i], strDate, strCategory, strSubCategory)
				print("[spiderForAngellist] " + str(i + 1).encode("utf8") + "/" + str(len(lstStrUrl)).encode("utf8"))
			else:
				print("[spiderForAngellist] " + lstStrUrl[i] + " has been saved")		

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

			if(strCategory == "Location"):
				#save Overview page
				self.autoClickMoreToExtendLst(spiderForAngellist.STARTUP_PRODUCT_MORE_CSS)
				print "1"
				self.autoClickMoreToExtendLst(spiderForAngellist.STARTUP_PRODUCT_FUNDINGSTAGE_CSS)
				print "2"
				self.autoClickMoreToExtendLst(spiderForAngellist.STARTUP_PRODUCT_PREINVEST_CSS)
				print "3"
				self.saveCurrentPage(spiderForAngellist.getOverviewLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
				#save Activiey#Press page
				elementActivityTab = self.__driver.find_element_by_css_selector("a.tab.activity")
				strActivityUrl = elementActivityTab.get_attribute("href")
				self.__driver.get(strActivityUrl)
				elementActivityPressTab = self.__driver.find_element_by_css_selector("ul.g-sub_nav > li[data-tab='press'] > a")
				strActivityPressUrl = elementActivityPressTab.get_attribute("href")
				self.__driver.get(strActivityPressUrl)
				self.scrollToExtendLst(spiderForAngellist.STARTUP_ACTIVITY_NOMORE_CSS)
				self.saveCurrentPage(spiderForAngellist.getActivityPressLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
				#save Followers page
				elementFollowersTab = self.__driver.find_element_by_css_selector("a.tab.followers")
				strFollowersUrl = elementFollowersTab.get_attribute("href")
				self.__driver.get(strFollowersUrl)
				self.autoClickMoreToExtendLst(spiderForAngellist.STARTUP_FOLLOWERS_MORE_CSS)
				self.saveCurrentPage(spiderForAngellist.getFollowersLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
				
				    
			appendTextFile(strUrl, spiderForAngellist.strSavedUrlFilePath(strDate, strCategory, strSubCategory))
			return True

		except Exception, e:
			print("[spiderForAngellist] Failed! ErrorMessage:" + str(e))
			appendTextFile("[" + strUrl + "] " + repr(e), spiderForAngellist.strErrorListFilePath(strDate, strCategory, strSubCategory))
			import pdb; pdb.set_trace()
			return False				

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
		print("[spiderForAngellist] Waiting for AJAX complete")
		try:
			return 0 == driver.execute_script("return jQuery.active")
		except WebDriverException:
			pass

	def autoClickMoreToExtendLst(self, strMoreCss):
		wait = WebDriverWait(self.__driver, 10)
		# element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, strMoreCss)))
		wait.until(self.ajax_complete, "Timeout waiting for page to load")
		lstElementMore = self.__driver.find_elements_by_css_selector(strMoreCss)
		print "wait CSS: " + strMoreCss + " has count: " + str(len(lstElementMore))
		intMoreCount = 0
		#while(len(lstElementMore) == 1):
		while(len(lstElementMore) >= 1):
			elementMore = lstElementMore[0]
			intMoreCount += 1
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

			#while lstElementMore == self.__driver.find_elements_by_css_selector(strMoreCss):
				# 按下 div.more_field 執行的 ajax 完成後會產生新的, 因此以判斷是不是同一個 element, 來決定是否繼續
				#print "wait..."
				#sleep(0.05)

			
			print "more #" + str(intMoreCount)
			# self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

			lstElementMore = self.__driver.find_elements_by_css_selector(strMoreCss)

			print "wait CSS: " + strMoreCss + " has count: " + str(len(lstElementMore))

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

	def getLstOfAllObjects(self, strCategory):
		wait = WebDriverWait(self.__driver, 10)
		wait.until(self.ajax_complete, "Timeout waiting for page to load")
		lstObjElement = []
		if(strCategory == "People"):
			self.autoClickMoreToExtendLst("div.more_field")
			return self.__driver.find_elements(By.CSS_SELECTOR, "div.people-list[data-_tn='people/list/row']")
		elif(strCategory == "Location"):
			#self.autoClickMoreToExtendLst("div.more.hidden")
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
			if(strSubCategory == "Taiwan"):
				strUrl = spiderForAngellist.LOCATION_TAIWAN_URL

		return strUrl

	def saveCurrentPage(self, strFilePath):
		strData = self.__driver.page_source.encode('utf8')
		overwriteTextFile(strData, strFilePath)

	@staticmethod
	def strLocalPagePath():
		if(os.name == "nt"):
			return "C:/Users/Nathan/Documents/SavedPage/"
			#return "C:/Users/Administrator.WIN-14526221294/Desktop/SavedPage/"
		elif(os.name == "posix"):
			return "/Users/yuwei/Desktop/LocalPage/kickstarter/"

	@staticmethod				
	def strSavedUrlFilePath(strDate, strCategory, strSubCategory):							#本次已抓取url列表
		return spiderForAngellist.strLocalPagePath() + "/" + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForAngellist.LOCAL_PAGE_SAVED_URLS_FILENAME + spiderForAngellist.LOCAL_PAGE_INFO_EXTENSION

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
		strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		return spiderForAngellist.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + strObjectID + "_overview" + spiderForAngellist.LOCAL_PAGE_EXTENSION

	@staticmethod
	def getActivityPressLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 	#Startup
		strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		return spiderForAngellist.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + strObjectID + "_activitypress" + spiderForAngellist.LOCAL_PAGE_EXTENSION

	@staticmethod
	def getFollowersLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 	#Startup
		strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		return spiderForAngellist.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + strObjectID + "_followers" + spiderForAngellist.LOCAL_PAGE_EXTENSION		
	
	@staticmethod
	def getCategoryMappingFilePath():
		return spiderForAngellist.strLocalPagePath() + spiderForAngellist.LOCAL_PAGR_CATEGORY_MAPPING_FILENAME

	@staticmethod
	def getPureUrl(strUrl): 										#從專案的url去掉"?ref_XXX"等字樣
		strUrl = strUrl[0:strUrl.rfind('?')]
		return strUrl

	@staticmethod
	def getCategoryMapping(driver = None):
		strFilePath = spiderForAngellist.getCategoryMappingFilePath()
		if(os.path.isfile(strFilePath)):
			dicMapping = loadObjFromJsonFile(strFilePath)
			return dicMapping
		else:
			dicMapping = { "People" : ["SyndicateLeads", "Investors"],
							"Location" : ["Taiwan"] } # TODO: add real dicMapping
			return dicMapping


	@staticmethod
	def saveAllObjectsOfCategory(strDate, strCategory, lstStrSubCategory = [], isClearSavedUrls = False):
		spider = spiderForAngellist()
		driver = webdriver.Firefox()
		
		# chromedriver = "C:/Python27/Scripts/chromedriver.exe"
		# os.environ["webdriver.chrome.driver"] = chromedriver
		# driver = webdriver.Chrome(chromedriver)

		# firefox_capabilities = DesiredCapabilities.FIREFOX
		# firefox_capabilities['marionette'] = True
		# firefox_capabilities['binary'] = 'C:/Python27/Scripts/wires.exe'
		# driver = webdriver.Firefox(capabilities=firefox_capabilities)

		driver.maximize_window()
		if len(lstStrSubCategory) == 0:
			dicMapping = spiderForAngellist.getCategoryMapping()
			for strSubCategoryInMapping in dicMapping[strCategory]:
				spider.saveProjectsToLocalFile(driver, strDate, strCategory, strSubCategoryInMapping, isClearSavedUrls)
		else:
			for strSubCategory in lstStrSubCategory:
				spider.saveObjectsToLocalFile(driver, strDate, strCategory, strSubCategory, isClearSavedUrls)


def main():
	#spiderForAngellist.saveAllObjectsOfCategory("2016-02-24", "People", ["SyndicateLeads", "Investors"])
	spiderForAngellist.saveAllObjectsOfCategory("2016-02-24", "Location", ["Taiwan"])

if __name__ == '__main__':
	main()