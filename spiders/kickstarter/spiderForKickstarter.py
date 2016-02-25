#coding: utf-8

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
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

class spiderForKickstarter:

	START_PAGE_URL = "https://www.kickstarter.com/discover/categories/art?ref=discover_index"
	LOCAL_PAGR_CATEGORY_MAPPING_FILENAME = "categroyMapping.json"
	LOCAL_PAGE_PROJECT_FOLDER = "Projects/"
	LOCAL_PAGE_PROFILE_FOLDER = "Profiles/"
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
		self.__lstIgnoredUrl = []

	def saveProjectsToLocalFile(self, driver, strDate, strCategory, strSubCategory, intCount = 0, isClearSavedUrls = False):
		self.__driver = driver
		self.__driver.get(self.START_PAGE_URL)
		
		strSavedFileUrl = spiderForKickstarter.strSavedUrlFilePath(strDate, strCategory, strSubCategory)
		strIgnoredFileUrl = spiderForKickstarter.strIgnoredUrlFilePath(strCategory, strSubCategory)
		if(isClearSavedUrls == True and os.path.isfile(strSavedFileUrl)):
			os.remove(strSavedFileUrl)			

		self.__lstSavedUrls = loadStrListInfo(strSavedFileUrl)
		self.__lstIgnoredUrl = loadStrListInfo(strIgnoredFileUrl)

		if self.setFilter(strCategory, strSubCategory) == False:
			return
		lstStrUrl = []

		strPageBaseUrl = self.__driver.current_url
		strPageBaseUrl = strPageBaseUrl[0:strPageBaseUrl.rfind('=')+1]
		intPageIndex = 1
		intTotalProjectCount = 0
		while intPageIndex <= 200: #kickstarter最多生成200頁
			strPageUrl = strPageBaseUrl + str(intPageIndex).encode("utf8")
			print("[spiderForKickstarter] page " + str(intPageIndex).encode("utf8"))
			self.__driver.get(strPageUrl)
			#Chech if is 404 page
			lstErrorElement = self.__driver.find_elements_by_css_selector(".content > .grey-frame > .grey-frame-inner > h1")
			if(len(lstErrorElement) > 0 and u"404" in lstErrorElement[0].text):
				break
			lstErrorElement = self.__driver.find_elements_by_css_selector(".general_empty_state > p")
			if(len(lstErrorElement) > 0 and u"Oops" in lstErrorElement[0].text):
				break

			lstProjectElement = self.__driver.find_elements_by_css_selector(".project.col.col-3.mb4")
			intCurProjectCount = len(lstProjectElement)
			if(intCount > 0 and intCount - intTotalProjectCount < intCurProjectCount):
				intCurProjectCount = intCount - intTotalProjectCount
			intTotalProjectCount = intTotalProjectCount + intCurProjectCount
			for i in range(0, intCurProjectCount, 1):
				strUrl = lstProjectElement[i].find_element_by_css_selector("a").get_attribute("href")
				strUrl = spiderForKickstarter.getPureUrl(strUrl)
				lstStrUrl.append(strUrl)										
			intPageIndex = intPageIndex + 1
			if(intCount > 0 and intTotalProjectCount >= intCount):
				break

		for i in range(0, len(lstStrUrl), 1):
			if(lstStrUrl[i] not in self.__lstSavedUrls and lstStrUrl[i] not in self.__lstIgnoredUrl):
				self.saveProjectToLocalFile(lstStrUrl[i], strDate, strCategory, strSubCategory)
				print("[spiderForKickstarter] " + str(i + 1).encode("utf8") + "/" + str(len(lstStrUrl)).encode("utf8"))
			else:
				print("[spiderForKickstarter] " + lstStrUrl[i] + " has been saved")

	def saveProjectToLocalFile(self, strUrl, strDate, strCategory, strSubCategory, driver = None):
		if(self.__driver == None):
			self.__driver = webdriver.Firefox()
			self.__driver.maximize_window()
		print("[spiderForKickstarter] Saving " + strUrl + "...")			
		try:
			self.__driver.get(strUrl)
			#儲存Description頁面
			strProjectDescriptionUrl = self.__driver.find_element_by_css_selector(".project-nav__links > a[data-content='description']").get_attribute("href")
			self.__driver.get(strProjectDescriptionUrl)
			self.saveCurrentPage(spiderForKickstarter.getProjectDescriptionLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
			#儲存Update頁面
			strProjectUpdateUrl = self.__driver.find_element_by_css_selector(".project-nav__links > a[data-content='updates']").get_attribute("href")
			self.__driver.get(strProjectUpdateUrl)
			self.saveCurrentPage(spiderForKickstarter.getProjectUpdateLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
			#儲存Comment頁面
			strProjectCommentUrl = self.__driver.find_element_by_css_selector(".project-nav__links > a[data-content='comments']").get_attribute("href")
			self.__driver.get(strProjectCommentUrl)
			self.scrollProjectCommentToBottom()
			self.saveCurrentPage(spiderForKickstarter.getProjectCommentLocalFilePath(strUrl, strDate, strCategory, strSubCategory))	
			#儲存Reward頁面
			strProjectRewardUrl = self.__driver.find_element_by_css_selector(".project-nav__links > a[data-content='rewards']").get_attribute("href")
			self.__driver.get(strProjectRewardUrl)
			self.saveCurrentPage(spiderForKickstarter.getProjectRewardLocalFilePath(strUrl, strDate, strCategory, strSubCategory))
			#若是creator名字內含"(deleted)"表示此人已不存在於kickstarter
			lstCreatorElement = self.__driver.find_elements_by_css_selector("a[href*='creator_bio']")
			isCreatorExist = True
			for createElement in lstCreatorElement:
				strCreatorName = createElement.get_attribute("text")
				if u"(deleted)" in strCreatorName:
					isCreatorExist = False
					break
			#儲存點開作者資訊的頁面
			strProjectCreatorBioUrl = self.__driver.find_element_by_css_selector("a[href*='creator_bio']").get_attribute("href")
			self.__driver.get(strProjectCreatorBioUrl)
			self.saveCurrentPage(spiderForKickstarter.getProjectCreatorInfoFilePath(strUrl, strDate, strCategory, strSubCategory))
			if isCreatorExist == False:
				#print("[spiderForKickstarter] " + strCreatorName + " is no longer active on kickstarter ")
				appendTextFile(strUrl, spiderForKickstarter.strSavedUrlFilePath(strDate, strCategory, strSubCategory))
				return True
			#儲存發起人Backed頁面
			strProfileUrl = self.__driver.find_element_by_css_selector("a[href*='profile']").get_attribute("href")
			self.__driver.get(strProfileUrl)
			self.scrollForCreatingAllItem(".col.col-3 > .project-card-mini-wrap")
			self.saveCurrentPage(spiderForKickstarter.getProfileBackedFilePath(strProfileUrl, strDate, strCategory, strSubCategory))
			#儲存發起人Created頁面
			strProfileCreatedUrl = self.__driver.find_element_by_css_selector("a[href*='created']").get_attribute("href")
			self.__driver.get(strProfileCreatedUrl)
			self.scrollForCreatingAllItem(".project-card-list.NS_user__projects_list.list > mb2")
			self.saveCurrentPage(spiderForKickstarter.getProfileCreatedFilePath(strProfileUrl, strDate, strCategory, strSubCategory))
			#儲存發起人Comments頁面
			strProfileCommentUrl = self.__driver.find_element_by_css_selector("a[href*='comments']").get_attribute("href")
			self.__driver.get(strProfileCommentUrl)
			self.scrollForCreatingAllItem(".activity-comment-project, .activity-comment-post")
			self.saveCurrentPage(spiderForKickstarter.getProfileCommentsFilePath(strProfileUrl, strDate, strCategory, strSubCategory))	
			#儲存發起人詳細介紹頁面
			if(checkElementExist(self.__driver, "a[href$='/bio']")):
				strProfileFullBioUrl = self.__driver.find_element_by_css_selector("a[href$='/bio']").get_attribute("href")
				self.__driver.get(strProfileFullBioUrl)
				self.saveCurrentPage(spiderForKickstarter.getProfileFullBiographyFilePath(strProfileUrl, strDate, strCategory, strSubCategory))		    
			appendTextFile(strUrl, spiderForKickstarter.strSavedUrlFilePath(strDate, strCategory, strSubCategory))
			return True

		except Exception, e:
			print("[spiderForKickstarter] Failed! ErrorMessage:" + str(e))
			appendTextFile("[" + strUrl + "] " + repr(e), spiderForKickstarter.strErrorListFilePath(strDate, strCategory, strSubCategory))
			return False
		
	#strSort = magic / popularity / newest / end_date / most_funded
	def setFilter(self, strCategory, strSubCategory, strSort = u"newest"): #在瀏覽器中設定專案篩選器
		print("[spiderForKickstarter]: Set filter to " + strCategory + "/" + strSubCategory)
		self.__driver.find_element_by_css_selector(".js-refine-and-sort.refine-and-sort a").click()
		while len(self.__driver.find_elements_by_css_selector("#category_filter")) <= 0:
			sleep(0.1)
		self.__driver.find_element_by_css_selector("#category_filter").click()
		print("[spiderForKickstarter] Wait for selecting category")
		while len(self.__driver.find_elements_by_css_selector(".category > a")) <= 0:
			sleep(0.1)
		lstCategoryElement = self.__driver.find_elements_by_css_selector(".category > a")
		for categoryElement in lstCategoryElement:
			if categoryElement.text == strCategory:
				categoryElement.click()
				break
		print("[spiderForKickstarter] Wait for selecting subcategory")
		while len(self.__driver.find_elements_by_css_selector(".subcategory > a")) <= 0:
			sleep(0.1)
		lstSubCategoryElement = self.__driver.find_elements_by_css_selector(".subcategory > a")
		for subCategoryElement in lstSubCategoryElement:
			if subCategoryElement.text == strSubCategory:
				subCategoryElement.click()
				break
		print("[spiderForKickstarter] Wait for clicking sort")
		while len(self.__driver.find_elements_by_css_selector("#sorts")) <= 0:
			sleep(0.1)
		self.__driver.find_element_by_css_selector("#sorts").click()
		print("[spiderForKickstarter] Wait for selecting sort method " + strSort)
		while len(self.__driver.find_elements_by_css_selector("li[data-sort='" + strSort + "']")) <= 0:
			sleep(0.1)
		self.__driver.find_element_by_css_selector("li[data-sort='" + strSort + "'] > a").click()
		while len(self.__driver.find_elements_by_css_selector(".relative.border-top.pt2.loading")) > 0:
			print("[spiderForKickstarter]: Wait for page loading...")
			sleep(0.1)
		return True

	def scrollProjectCommentToBottom(self):
		isScrollToBottom = False
		while isScrollToBottom == False:
			self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			sleep(0.5)
			if(len(self.__driver.find_elements_by_css_selector(".older_comments")) > 0):
				loadMoreElement = self.__driver.find_element_by_css_selector(".older_comments")
				if(loadMoreElement.is_displayed()):
					loadMoreElement.click()
				else:
					isScrollToBottom = True
			else:
				isScrollToBottom = True

	def scrollForCreatingAllItem(self, strItemCss): #適用於網頁往下滑即可產生列表物件的頁面，輸入生成物件的css selector字串
		fCurTime = 0
		intLastItemCount = 0
		while True:
			intCurItemCount = len(self.__driver.find_elements_by_css_selector(".col.col-3 > .project-card-mini-wrap"))
			if fCurTime > self.INT_SCROLL_TIMEOUT:
				break
			elif intCurItemCount > intLastItemCount:
				intLastItemCount = intCurItemCount
				self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
				fCurTime = 0
			else:
				fCurTime = fCurTime + 0.5
				sleep(0.5)

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
		return spiderForKickstarter.strLocalPagePath() + "/" + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_SAVED_URLS_FILENAME + spiderForKickstarter.LOCAL_PAGE_INFO_EXTENSION
	
	@staticmethod				
	def strErrorListFilePath(strDate, strCategory, strSubCategory):							#error列表
		return spiderForKickstarter.strLocalPagePath() + "/" + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_ERROR_URLS_FILENAME + spiderForKickstarter.LOCAL_PAGE_INFO_EXTENSION
	
	@staticmethod
	def strIgnoredUrlFilePath(strCategory, strSubCategory): 								#本類別已募資完成專案url列表
		return spiderForKickstarter.strLocalPagePath() + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_IGNORED_URL_FILENAME + spiderForKickstarter.LOCAL_PAGE_INFO_EXTENSION
	
	@staticmethod
	def getProjectDescriptionLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 	#Project Description 頁面路徑
		strProjectID = getFileNameInUrl(strUrl)
		return spiderForKickstarter.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_PROJECT_FOLDER + strProjectID + "_description" + spiderForKickstarter.LOCAL_PAGE_EXTENSION
	
	@staticmethod
	def getProjectCommentLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 		#Project Comment 頁面路徑
		strProjectID = getFileNameInUrl(strUrl)
		return spiderForKickstarter.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_PROJECT_FOLDER + strProjectID + "_comment" + spiderForKickstarter.LOCAL_PAGE_EXTENSION
	
	@staticmethod
	def getProjectUpdateLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 		#Project Update 頁面路徑
		strProjectID = getFileNameInUrl(strUrl)
		return spiderForKickstarter.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_PROJECT_FOLDER + strProjectID + "_update" + spiderForKickstarter.LOCAL_PAGE_EXTENSION
	
	@staticmethod
	def getProjectRewardLocalFilePath(strUrl, strDate, strCategory, strSubCategory): 		#Project Reward 頁面路徑
		strProjectID = getFileNameInUrl(strUrl)
		return spiderForKickstarter.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_PROJECT_FOLDER + strProjectID + "_reward" + spiderForKickstarter.LOCAL_PAGE_EXTENSION
	
	@staticmethod
	def getProjectCreatorInfoFilePath(strUrl, strDate, strCategory, strSubCategory): 		#Project 點開作者資訊時的頁面
		strProjectID = getFileNameInUrl(strUrl)
		return spiderForKickstarter.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_PROJECT_FOLDER + strProjectID + "_creator" + spiderForKickstarter.LOCAL_PAGE_EXTENSION
	
	@staticmethod
	def getProfileFullBiographyFilePath(strUrl, strDate, strCategory, strSubCategory):		#Profile 點開詳細傳記時的頁面
		strProfileID = getFileNameInUrl(strUrl)
		return spiderForKickstarter.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_PROFILE_FOLDER + strProfileID + "_biography" + spiderForKickstarter.LOCAL_PAGE_EXTENSION
	
	@staticmethod
	def getProfileBackedFilePath(strUrl, strDate, strCategory, strSubCategory):				#Profile backed 頁面路徑
		strProfileID = getFileNameInUrl(strUrl)
		return spiderForKickstarter.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_PROFILE_FOLDER + strProfileID + "_backed" + spiderForKickstarter.LOCAL_PAGE_EXTENSION
	
	@staticmethod
	def getProfileCreatedFilePath(strUrl, strDate, strCategory, strSubCategory):			#Profile created 頁面路徑
		strProfileID = getFileNameInUrl(strUrl)
		return spiderForKickstarter.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_PROFILE_FOLDER + strProfileID + "_created" + spiderForKickstarter.LOCAL_PAGE_EXTENSION
	
	@staticmethod
	def getProfileCommentsFilePath(strUrl, strDate, strCategory, strSubCategory):			#Profile comments 頁面路徑
		strProfileID = getFileNameInUrl(strUrl)
		return spiderForKickstarter.strLocalPagePath() + strDate + "/" + strCategory + "/" + strSubCategory + "/" + spiderForKickstarter.LOCAL_PAGE_PROFILE_FOLDER + strProfileID + "_comments" + spiderForKickstarter.LOCAL_PAGE_EXTENSION

	@staticmethod
	def getCategoryMappingFilePath():
		return spiderForKickstarter.strLocalPagePath() + spiderForKickstarter.LOCAL_PAGR_CATEGORY_MAPPING_FILENAME

	@staticmethod
	def getPureUrl(strUrl): 										#從專案的url去掉"?ref_XXX"等字樣
		strUrl = strUrl[0:strUrl.rfind('?')]
		return strUrl

	@staticmethod
	def loadCategorys():
		return loadObjFromJsonFile(spiderForKickstarter.getCategoryMappingFilePath())

	@staticmethod
	def getCategoryMapping(driver = None):
		strFilePath = spiderForKickstarter.getCategoryMappingFilePath()
		if(os.path.isfile(strFilePath)):
			dicMapping = loadObjFromJsonFile(strFilePath)
			return dicMapping
		else:
			if(driver == None):
				driver = webdriver.Firefox()
				driver.maximize_window()
			dicMapping = {};
			driver.get("https://www.kickstarter.com/discover/advanced")
			driver.find_element_by_css_selector(".js-refine-and-sort.refine-and-sort a").click()
			driver.find_element_by_css_selector("#category_filter").click()
			while len(driver.find_elements_by_css_selector(".category > a")) <= 0:
				sleep(0.5)
			lstCategroyElement = driver.find_elements_by_css_selector(".category > a")
			for categoryElement in lstCategroyElement:
				strCategory = categoryElement.text
				categoryElement.click()
				while len(driver.find_elements_by_css_selector(".subcategory > a")) <= 0:
					sleep(0.5)
				lstSubCategory = driver.find_elements_by_css_selector(".subcategory > a")
				lstStrSubCategoryName = []
				for strSubCategory in lstSubCategory:
					if(strSubCategory.is_displayed() and "All of " not in strSubCategory.text):
						lstStrSubCategoryName.append(strSubCategory.text)
				dicMapping[strCategory] = lstStrSubCategoryName
			saveObjToJson(dicMapping, strFilePath)
			return dicMapping

	@staticmethod
	def saveAllProjectsOfCategory(strDate, strCategory, lstStrSubCategory = [], isClearSavedUrls = False):
		spider = spiderForKickstarter()
		driver = webdriver.Firefox()
		driver.maximize_window()
		if len(lstStrSubCategory) == 0:
			dicMapping = spiderForKickstarter.getCategoryMapping()
			for strSubCategoryInMapping in dicMapping[strCategory]:
				spider.saveProjectsToLocalFile(driver, strDate, strCategory, strSubCategoryInMapping, isClearSavedUrls)
		else:
			for strSubCategory in lstStrSubCategory:
				spider.saveProjectsToLocalFile(driver, strDate, strCategory, strSubCategory, isClearSavedUrls)



def main():
	spiderForKickstarter.saveAllProjectsOfCategory("2016-02-07", "Film & Video", ["Drama", "Experimental", "Family", "Fantasy", "Festivals", "Horror", "Movie Theaters", "Music Videos", "Narrative Film", "Romance", "Science Fiction", "Shorts", "Television", "Thrillers", "Webseries"])

	'''
	spider = spiderForKickstarter()
	driver = webdriver.Firefox()
	driver.maximize_window()

	strDate = str(datetime.date.today()).encode('utf8')
	dicMapping = spider.getCategoryMapping(driver, spiderForKickstarter.getCategoryMappingFilePath())
	for strCategory in dicMapping:
		for strSubCategory in dicMapping[strCategory]:
			print(strCategory + " " + strSubCategory)
			spider.saveProjectsToLocalFile(driver, strDate, strCategory, strSubCategory, isClearSavedUrls = False)
	
	spider.saveProjectsToLocalFile(driver, "Art", "Ceramics", isClearSavedUrls = False)
	spider.getCategoryMapping(driver, spiderForKickstarter.getCategoryMappingFilePath())
	for i in range(1, len(lstStrCategories), 1):
		spider.saveProjectsToLocalFile(driver, lstStrCategories[i], isClearSavedUrls = False)

	spider = spiderForKickstarter()
	driver = webdriver.Firefox()
	driver.maximize_window()
	spider.saveProjectToLocalFile(u"https://www.kickstarter.com/projects/iambigbird/i-am-big-bird", str(datetime.date.today()).encode('utf8'), "Film & Video", "Animation", driver)
	
	driver.close()
	'''

if __name__ == '__main__':
	main()
