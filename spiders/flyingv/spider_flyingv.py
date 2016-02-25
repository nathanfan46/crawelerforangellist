#coding: utf-8

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from scrapy import Selector
from time import sleep
import unicodedata
import os.path
import datetime
import io
import json
import codecs
import math
import sys
import re
from progressBar import *
from utility import *
import threading
from threading import Thread

#strTypePageUrl
STR_URL_DESIGNGOODS = "https://www.flyingv.cc/category/designgoods"
STR_URL_MEDIA = "https://www.flyingv.cc/category/media"
STR_URL_STAGEPLAY = "https://www.flyingv.cc/category/stageplay"
STR_URL_ENTERTAINMENT = "https://www.flyingv.cc/category/entertainment"
STR_URL_UPUBLISH = "https://www.flyingv.cc/category/publish"
STR_URL_SOCIETY = "https://www.flyingv.cc/category/society" #flyingV這個類別的網頁壞了
STR_URL_TECHNOLOGY = "https://www.flyingv.cc/category/technology"
STR_URL_FOOD = "https://www.flyingv.cc/category/food"
STR_URL_TRAVEL = "https://www.flyingv.cc/category/travel"
STR_URL_FREEBIRD = "https://www.flyingv.cc/category/freebird"

INT_SCROLL_TIMEOUT = 10 #second

#Error message
STR_ERROR_SPONSOR_LIST_SCROLL = u"贊助者列表下捲 time out"

class SpiderForFlyingV:
	__PARSED_RESULT_PATH = "/Users/yuwei/Desktop/ParsedResult/flyingv/"
	__PARSED_RESULT_PROJECT_FILENAME = "projects"
	__PARSED_RESULT_UPDATE_FILENAME = "update"
	__PARSED_RESULT_COMMENT_FILENAME = "comment"
	__PARSED_RESULT_QNA_FILENAME = "qna"
	__PARSED_RESULT_REWARD_FILENAME = "reward"
	__PARSED_RESULT_SPONSORS_FILENAME = "proposer"

	__LOCAL_PAGE_PATH = "/Users/yuwei/Desktop/LocalPage/flyingv/"
	__LOCAL_PAGE_PROJECT_LIST_FILENAME = "projectList" #由於摘要只有在專案列表內才能看到，無法在專案頁看到，因此須獨立先存成dicionary，parse專案時再寫到各個專案資訊中
	__LOCAL_PAGE_SAVED_URLS_FILENAME = "savedUrls" #每次存完的網站會把url存下
	__LOCAL_PAGE_SPONSOR_FILENAME = "proposer" #file name: "proposer_id.html" 
	__LCOAL_PAGE_IGNORED_URL_FILENAME = "ignoredUrls" #若是已經結束募資的url，之後爬此網站會忽略，在parseProjectListPage函式會建立其內容
	__LOCAL_PAGE_EXTENSION = ".html"
	__LOCAL_PAGR_BLOG_SUFFIXES = "_blog"
	__LOCAL_PAGR_QA_SUFFIXES = "_qa"
	__LOCAL_PAGR_BACKERS_SUFFIXES = "_backers"
	__LOCAL_PAGR_FB_SUFFIXES = "_fb"

	__RESULT_FILE_PATH = "/Users/yuwei/Desktop/Result/flyingv"

	def __init__(self):
		self.__driver = None
		self.__lstSavedUrls = []
		self.__lstIgnoredUrl = []
		self.__lstUpdateResult = []
		self.__lstRewardResult = []
		self.__lstQnaResult = []
		self.__lstCommentResult = []
		self.__lstProjectResult = []
		self.__dicErrorMsg = {}
		self.__dicCreatorResult = {}
		self.__dicProjectInfo = {} #key: projectID, value: {"strDescription":"", "intStatus":"0=live/1=success/2=failed"}

	def saveProjectsToLocalFile(self, strTypePageUrl, driver, intStartIndex = 0, intCount = 0, isClearSavedUrls = True): #通常是爬到一半當掉繼續爬才會設定為False
		print("[FlyingV] Save to local files...")
		self.loadIgnoredUrlList(strTypePageUrl)
		self.__driver = driver
		self.__driver.get(strTypePageUrl)

		if(isClearSavedUrls == True and os.path.isfile(isClearSavedUrls) == True):
			os.remove(self.getSaveUrlFilePath(strTypePageUrl))
		self.loadSavedUrlList(strTypePageUrl)

		#儲存專案列表頁面		
		strData = self.__driver.page_source.encode('utf8')
		overwriteTextFile(strData, self.getProjectListFilePath(strTypePageUrl))
		#儲存各個專案
		contents = self.__driver.find_elements_by_css_selector(".portfolio-item > a")
		urls = []
		for content in contents:
			projectUrl = content.get_attribute("href")
			urls.append(projectUrl)
		if intCount <= 0 or intCount > len(urls):
			intCount = len(urls)
		for i in range(intStartIndex, intCount, 1): 
			url = urls[i]
			print(strTypePageUrl + " " + str(float(i) / float(intCount)*100)+ "%")
			if(url not in self.__lstSavedUrls):
				if(getFileNameInUrl(url) not in self.__lstIgnoredUrl):
					if(self.saveProjectToLocalFile(url, None)):
						appendTextFile(url, self.getSaveUrlFilePath(strTypePageUrl))
				else:
					appendTextFile(url, self.getSaveUrlFilePath(strTypePageUrl))
		self.__driver.close()

	def saveProjectToLocalFile(self, url, driver): #save project to local page by [Selenium]
		if(self.__driver == None):
			self.__driver = driver

		print("[FlyingV] Save " + url + "...")
		try:
			projectID = getFileNameInUrl(url)	
			#儲存主頁面
			self.__driver.get(url)
			strData = self.__driver.page_source.encode('utf8')
			overwriteTextFile(strData, self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGE_EXTENSION)

			#儲存更新資訊頁面
			blogPageUrl = self.__driver.find_element_by_css_selector(".projectup li > a[href*='blog']").get_attribute("href")
			self.__driver.get(blogPageUrl)
			pageHrefElements = self.__driver.find_elements_by_css_selector(".pagination > li > a")
			lstBlogPageUrl = []
			if(len(pageHrefElements) > 0):
				[lstBlogPageUrl.append(x.get_attribute("href")) for x in pageHrefElements]
			else:
				lstBlogPageUrl.append(blogPageUrl)

			for i in range(0, len(lstBlogPageUrl), 1):
				self.__driver.get(lstBlogPageUrl[i])
				strData = self.__driver.page_source.encode('utf8')
				overwriteTextFile(strData, self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGR_BLOG_SUFFIXES + "_" + str(i) + self.__LOCAL_PAGE_EXTENSION)	

			#儲存Q&A資訊頁面
			qaPageUrl = self.__driver.find_element_by_css_selector(".projectup li > a[href*='qa']").get_attribute("href")
			self.__driver.get(qaPageUrl)
			strData = self.__driver.page_source.encode('utf8')
			overwriteTextFile(strData, self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGR_QA_SUFFIXES + self.__LOCAL_PAGE_EXTENSION)
			
			#儲存贊助者頁面
			backersPageUrl = self.__driver.find_element_by_css_selector(".projectup li > a[href*='backers']").get_attribute("href")
			self.__driver.get(backersPageUrl)
			backerCount = int(self.__driver.find_element_by_css_selector(".projectup li > a[href*='backers'] > span").text)
			fTimeout = 0
			intLastCount = 0
			while len(self.__driver.find_elements_by_css_selector("#backer-container > .backer-item.well")) < backerCount:
				if(len(self.__driver.find_elements_by_css_selector("#backer-container > .backer-item.well")) == intLastCount):	
					fTimeout = fTimeout + 0.05
					if(fTimeout > INT_SCROLL_TIMEOUT):
						self.addErrorMsg(url, STR_ERROR_SPONSOR_LIST_SCROLL)
						break
				else:
					intLastCount = len(self.__driver.find_elements_by_css_selector("#backer-container > .backer-item.well"))
					fTimeout = 0
				sleep(0.05)
				self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			strData = self.__driver.page_source.encode('utf8')
			overwriteTextFile(strData, self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGR_BACKERS_SUFFIXES + self.__LOCAL_PAGE_EXTENSION)

			#儲存發起人頁面
			proposerPageUrl = self.__driver.find_element_by_css_selector(".pageDes a[href*='profile']").get_attribute("href")
			self.__driver.get(proposerPageUrl)
			strData = self.__driver.page_source.encode('utf8')
			proposerFileName = self.getCreatorFilePath(proposerPageUrl)
			overwriteTextFile(strData, proposerFileName)	

			#判斷是否有粉絲頁，若是有的話要把iframe內的資料存成另一個html檔案
			if len(self.__driver.find_elements_by_css_selector(".fanpage")) > 0:
				fbElement = self.__driver.find_element_by_css_selector(".fanpage iframe")
				self.__driver.switch_to_frame(fbElement)
				strData = self.__driver.page_source.encode('utf8')
				idIndex = url.rfind('/')+1
				overwriteTextFile(strData, self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGR_FB_SUFFIXES + self.__LOCAL_PAGE_EXTENSION)
				self.__driver.switch_to.default_content()			
			print("Success")
			return True
		except Exception, e:
			self.addErrorMsg(url, repr(e))
			print("[FlyingV] Save " + url + " failed ")
			return False

	def parseProjects(self, strTypePageUrl): #parse all projects from local pages
		print("[FlyingV] Parsing local files...")
		self.loadSavedUrlList(strTypePageUrl)
		self.parseProjectListPage(strTypePageUrl)
		for url in self.__lstSavedUrls:
			self.parseProject(url)
		
		strType = getFileNameInUrl(strTypePageUrl)

		projectFilePath = self.__PARSED_RESULT_PATH + self.__PARSED_RESULT_PROJECT_FILENAME + "_" + strType + ".json"
		saveObjToJson(self.__lstProjectResult, projectFilePath)

		updateFilePath = self.__PARSED_RESULT_PATH + self.__PARSED_RESULT_UPDATE_FILENAME + "_" + strType + ".json"
		saveObjToJson(self.__lstUpdateResult, updateFilePath)

		commentFilePath = self.__PARSED_RESULT_PATH + self.__PARSED_RESULT_COMMENT_FILENAME + "_" + strType + ".json"
		saveObjToJson(self.__lstCommentResult, commentFilePath)

		qnaFilePath = self.__PARSED_RESULT_PATH + self.__PARSED_RESULT_QNA_FILENAME + "_" + strType + ".json"
		saveObjToJson(self.__lstQnaResult, qnaFilePath)

		rewardFilePath = self.__PARSED_RESULT_PATH + self.__PARSED_RESULT_REWARD_FILENAME + "_" + strType + ".json"
		saveObjToJson(self.__lstRewardResult, rewardFilePath)

		sponsorFilePath = self.__PARSED_RESULT_PATH + self.__PARSED_RESULT_SPONSORS_FILENAME + "_" + strType + ".json"	
		saveObjToJson(self.__dicCreatorResult, sponsorFilePath)
		
		ignoredUrlsFilePath = self.getIgnoredUrlFilePath(strTypePageUrl)
		saveObjToJson(self.__lstIgnoredUrl, ignoredUrlsFilePath)
		return
	
	def parseProject(self, url): #parsing data from local project by [Scrapy]
		try:
			strPageSource = None
			idIndex = url.rfind('/')+1
			projectID = getFileNameInUrl(url)	
			dicProjectResult = {};
			#平台名稱
			dicProjectResult["strSource"] = "flyingV" 
			#來源網址
			dicProjectResult["strUrl"] = url 

			# [ 解析主頁面 ] 
			projectPageFilePath = self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGE_EXTENSION
			print(projectPageFilePath)
			with open(projectPageFilePath, "rb") as file: #讀取本地端文件檔案內容到字串
				strPageSource = file.read()
			root = Selector(text=strPageSource) #開始使用Scrapy解析字串
			#專案名稱
			strProjectName = root.css(".pagesTitle::text").extract_first().strip()
			dicProjectResult["strProjectName"] = strProjectName 	
			#地區
			dicProjectResult["strLocation"] = "Taiwan"
			#所屬國家
			dicProjectResult["strCountry"] = "ROC"
			#洲別
			dicProjectResult["strContinent"] = "Asia"
			#摘要
			dicProjectResult["strDescription"] = self.__dicProjectInfo[projectID]["strDescription"]
			#募資狀態
			dicProjectResult["intStatus"] = self.__dicProjectInfo[projectID]["intStatus"]
			if dicProjectResult["intStatus"] > 0:
				self.__lstIgnoredUrl.append(projectID)
			#介紹
			projectIntros = root.css(".project_content span::text").extract()
			strIntroduction = ""
			for intro in projectIntros:
				strIntroduction += intro.strip()
			dicProjectResult["strIntroduction"] = strIntroduction
			#提案者姓名
			strCreator = root.css(".pageDes a[href*='profile']::text").extract_first().strip()
			dicProjectResult["strCreator"] = strCreator 	
			#提案者url
			strCreatorUrl = root.css(".pageDes a[href*='profile']::attr(href)").extract_first().strip()
			dicProjectResult["strCreatorUrl"] = strCreatorUrl 	
			self.parseCreatorPage(strCreatorUrl)
			#影片數
			intVideoCount = len(root.css(".f-video-editor").extract())
			dicProjectResult["intVideoCount"] = str(intVideoCount)
			#圖片數
			intImageCount = len(root.css(".project_content img").extract())
			dicProjectResult["intImageCount"] = str(intImageCount)
			#PM嚴選
			isPMSelect = "True"
			dicProjectResult["isPMSelect"] = isPMSelect
			#類別
			strCategory = root.css(".pageDes a[href*='category']::text").extract_first().strip()
			dicProjectResult["strCategory"] = strCategory
			#類別細項
			strSubCategory = strCategory
			dicProjectResult["strSubCategory"] = strSubCategory
			#募資進度
			fFundProgress = root.css(".percentt::text").extract_first().strip()
			fFundProgress = fFundProgress[0:len(fFundProgress) - 1]
			dicProjectResult["fFundProgress"] = fFundProgress
			#目標金額
			intFundTarget = root.css(".countdes > div:last-child > div:first-child > span::text").extract_first().strip()
			intFundTarget = intFundTarget[1:(len(intFundTarget))].replace(",", "")
			dicProjectResult["intFundTarget"] = intFundTarget
			#已募金額
			intRaisedMoney = root.css(".countdes > div:first-child > div:last-child > h3::text").extract_first().strip()
			intRaisedMoney = intRaisedMoney[1:(len(intRaisedMoney))].replace(",", "")
			dicProjectResult["intRaisedMoney"] = intRaisedMoney
			#幣別
			strCurrency = "NTD"
			dicProjectResult["strCurrency"] = strCurrency
			#贊助人數
			intBacker = root.css(".countdes > div:last-child > div:last-child::text").extract_first().strip()
			intBacker = intBacker[0:len(intBacker)-3]
			dicProjectResult["intBacker"] = intBacker
			#剩餘天數
			strRemainDays = root.css(".countdes > div:last-child > div:nth-child(2)::text").extract_first().strip()
			intRemainDays = 0
			if(u"剩餘" in strRemainDays and u"天" in strRemainDays): #剩餘 x 天
				intRemainDays = strRemainDays[2:len(strRemainDays)-1].strip()
			elif(u"最後" in strRemainDays and u"小時" in strRemainDays): #最後 x 小時
				intRemainDays = int(math.ceil(float(strRemainDays[2:len(strRemainDays)-2].strip()) / 24.0))
			#結束日期 
			strStartAndEndDate = root.css(".sidebarprj > p:first-child::text").extract()[-1].strip()
			strStartAndEndDate = strStartAndEndDate[5:len(strStartAndEndDate)].strip()
			strEndDate = strStartAndEndDate[(len(strStartAndEndDate) - 10) : len(strStartAndEndDate)]
			dicProjectResult["strEndDate"] = strEndDate
			#建立日期
			strStartDate = strStartAndEndDate[0 : 10]
			dicProjectResult["strStartDate"] = strStartDate

			# [ 解析留言內容 ]
			self.parseComment(url)

			# [ 解析贊助專案 ]
			self.parseReward(url, root)

			# [ 解析Q&A資訊頁面 ]
			self.parseQnA(url)
			intComment = str(len(self.__lstQnaResult)).encode("utf8")
			dicProjectResult["intComment"] = intComment

			# [ 解析更新資訊頁面]
			self.parseUpdate(url)
			intUpdate = str(len(self.__lstUpdateResult)).encode("utf8")
			dicProjectResult["intUpdate"] = intUpdate

			# [ 解析贊助者頁面 ]
			backersPageFilePath = self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGR_BACKERS_SUFFIXES + self.__LOCAL_PAGE_EXTENSION
			strBackerPageSource = None
			#贊助人姓名列表
			lstStrBacker = []
			if os.path.isfile(backersPageFilePath) == True:
				with open(backersPageFilePath, "rb") as file: #讀取本地端文件檔案內容到字串
					strBackerPageSource = file.read()
				root = Selector(text=strBackerPageSource)
				lstStrBackerOri = root.css(".backer-item.well a[href*='profile']::text").extract()
				[lstStrBacker.append(purifyString(x)) for x in lstStrBackerOri]
				lstStrBacker = filter(None, lstStrBacker)
			dicProjectResult["lstStrBacker"] = lstStrBacker

			# [ 判斷是否有粉絲頁，若是有的話解析粉絲頁面 ] 	
			fanPageFilePath = self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGR_FB_SUFFIXES + self.__LOCAL_PAGE_EXTENSION
			strFanPageSource = None
			#FB按讚數
			intFbLike = 0
			if os.path.isfile(fanPageFilePath) == True:
				with open(fanPageFilePath, "rb") as file: #讀取本地端文件檔案內容到字串
					strFanPageSource = file.read()
				root = Selector(text=strFanPageSource) 
				strFbLike = root.css(".lfloat > div:last-child > div::text") #發現有些專案的粉絲頁顯示"錯誤：並非有效的 Facebook 粉絲專頁網址。"
				if(len(strFbLike) > 0):
					strFbLike = strFbLike.extract_first().strip()
					strFbLike = strFbLike.replace(",", "")
					if("." in strFbLike): 
						strFbLike = strFbLike[0:len(strFbLike)-6].strip()
						intFbLike = str(int(float(strFbLike) * 10000))
					else:
						intFbLike = strFbLike[0:len(strFbLike)-4].strip()
			dicProjectResult["intFbLike"] = intFbLike

			self.__lstProjectResult.append(dicProjectResult)
		except Exception, e:
			self.addErrorMsg(url, repr(e))
			print("[FlyingV] Parse " + url + " failed ")
		return 

	def parseProjectListPage(self, strTypePageUrl): #從專案列表頁面截取專案是否募資成功以及摘要資訊
		projectListFilePath = self.getProjectListFilePath(strTypePageUrl)
		strFileListPageSource = None
		with open(projectListFilePath, "rb") as file:
			strFileListPageSource = file.read()
			root = Selector(text = strFileListPageSource)
			lstProjectItem = root.css(".portfolio-item-wrapper")
			for projectItem in lstProjectItem:
				strUrl = projectItem.css(".portfolio-thumb > a[href*='project']::attr(href)").extract_first()
				strID = getFileNameInUrl(strUrl)
				strDescription = projectItem.css(".portfolio-thumb > a > .portfolio-zoom::text").extract_first()
				strDescription = purifyString(strDescription)
				intStatus = 0
				successItem = projectItem.css(".ribbon-green.rgreen")				
				failedItem = projectItem.css(".ribbon-green.rblue")
				if(len(successItem) > 0):
					intStatus = 1
				elif(len(failedItem) > 0):
					intStatus = 2
				self.__dicProjectInfo[strID] = {"strDescription":strDescription, "intStatus":intStatus}

	def parseCreatorPage(self, url):
		strLocalFilePath = self.getCreatorFilePath(url)
		dicCreatorInfo = {}
		with open(strLocalFilePath, "rb") as file:
			strCreatorPageSource = file.read()
			root = Selector(text = strCreatorPageSource)
			#名字
			strName = root.css(".pagesTitle::text").extract_first()
			dicCreatorInfo["strName"] = strName
			#簡介
			strDescription = ""
			strDescriptionOri = root.css(".userDes_inblock::text")
			if(len(strDescriptionOri) > 0):
				strDescription = purifyString(strDescriptionOri.extract_first())
			dicCreatorInfo["strDescription"] = strDescription
			#地區
			strLocation = "Taiwan"
			dicCreatorInfo["strLocation"] = strLocation
			#所屬國家
			strCountry = "ROC"
			dicCreatorInfo["strCountry"] = strCountry
			#洲別
			strContinent = "Asia"
			dicCreatorInfo["strContinent"] = strContinent
			#社群媒體url列表	flyingV沒有
			lstStrSocialNetwork = [] 
			dicCreatorInfo["lstStrSocialNetwork"] = lstStrSocialNetwork

			#是否是投資人
			#是否是發起人
			#發起過的專案名稱列表
			#發起過的專稱url列表
			#投資過的專案名稱列表
			#投資過的專案url列表
			#正在募資次數
			#過去成功募資次數
			#過去失敗募資次數
			#投資專案數
			#發起專案數
			projectListRow = root.css("#blog-wrapper > .container > .row ")
			isCreator = False
			isBacker = False
			dicCreatorInfo["lstStrCreatedProject"] = []
			dicCreatorInfo["lstStrCreatedProjectUrl"] = []	
			dicCreatorInfo["lstStrBackedProject"] = []
			dicCreatorInfo["lstStrBackedProjectUrl"] = []		
			intLiveProject = 0
			intSuccessProject = 0
			intFailedProject = 0
			dicCreatorInfo["intBackedCount"] = 0
			dicCreatorInfo["intCreatedCount"] = 0
			for projectListElement in projectListRow:
				strTitle = projectListElement.css("h1::text").extract_first()
				lstStrProject = projectListElement.css(".portfolio-content > h5::text").extract()
				lstStrProjectUrl = projectListElement.css(".portfolio-item > a[href*='project']::attr(href)").extract()
				if(strTitle == u"啟動專案"):
					dicCreatorInfo["lstStrCreatedProject"] = lstStrProject
					dicCreatorInfo["lstStrCreatedProjectUrl"] = lstStrProjectUrl
					intProject = len(lstStrProject)
					intSuccessProject = len(projectListElement.css(".ribbon-green.rgreen"))
					intFailedProject = len(projectListElement.css(".ribbon-green.rblue"))
					intLiveProject = intProject - intSuccessProject - intFailedProject
					dicCreatorInfo["intCreatedCount"] = str(len(lstStrProject)).encode("utf8")
					isCreator = True
				elif(strTitle == u"贊助專案"):
					dicCreatorInfo["lstStrBackedProject"] = lstStrProject
					dicCreatorInfo["lstStrBackedProjectUrl"] = lstStrProjectUrl
					dicCreatorInfo["intBackedCount"] = str(len(lstStrProject)).encode("utf8")
					isBacker = True
				dicCreatorInfo["isCreator"] = isCreator
				dicCreatorInfo["isBacker"] = isBacker
			dicCreatorInfo["intLiveProject"] = str(intLiveProject).encode("utf8")
			dicCreatorInfo["intSuccessProject"] = str(intSuccessProject).encode("utf8")
			dicCreatorInfo["intFailedProject"] = str(intFailedProject).encode("utf8")

			#負責人姓名
			dicCreatorInfo["strIdentityName"] = ""
			#最後登入時間
			dicCreatorInfo["strLastLoginDate"] = ""
			#朋友數(如果有FB)
			dicCreatorInfo["intFbFriends"] = 0
			
		self.__dicCreatorResult[url] = dicCreatorInfo

	def parseReward(self, strProjectUrl, root):
		lstUpdateElement = root.css(".reward")
		for updateElement in lstUpdateElement:
			dicRewardResult = {}
			#專案url
			dicRewardResult["strUrl"] = strProjectUrl
			#贊助方案內容
			strRewardContent = updateElement.css("p::text, a > p::text").extract_first()
			dicRewardResult["strRewardContent"] = purifyString(strRewardContent)
			#贊助方案金額
			intRewardMoney = updateElement.css(".price::text").extract_first()
			dicRewardResult["intRewardMoney"] = intRewardMoney[1:len(intRewardMoney)]
			#贊助方案人數
			strRewardBackersOri = updateElement.css(".pricetag small::text").extract_first()
			strRewardBackersOri = purifyString(strRewardBackersOri)
			intRewardBacker = strRewardBackersOri[0:strRewardBackersOri.index(u"人贊助")]
			dicRewardResult["intRewardBacker"] = purifyString(intRewardBacker)
			#限量人數, 會出現 "X人贊助, 已額滿" 或是 "X人贊助, 限量Y人"等字樣
			lstIntNum = re.findall('\d+', strRewardBackersOri)
			intRewardLimit = 0
			if(u"已額滿" in strRewardBackersOri):
				intRewardLimit = lstIntNum[0]
			elif(u"限量" in strRewardBackersOri):
				intRewardLimit = lstIntNum[-1]
			dicRewardResult["intRewardLimit"] = str(intRewardLimit).encode("utf8")
			#預計出貨日期
			DeliveryDateElements = updateElement.css(".duedate .deliver_data::text").extract()
			if(len(DeliveryDateElements) > 0):
				dicRewardResult["strRewardDeliveryDate"] = DeliveryDateElements[0]
			else:
				dicRewardResult["strRewardDeliveryDate"] = ""
			#可送達地點
			dicRewardResult["strRewardShipTo"] = ""
			#零售價
			intRewardRetailPrice = 0
			if(u"市" in strRewardContent and u"價" in strRewardContent):
				lstIntNum = re.findall('\d+', strRewardContent)		
				intMoney = int(dicRewardResult["intRewardMoney"]) 
				for intNum in lstIntNum:
					if int(intNum) > intMoney:
						intRewardRetailPrice = intNum
						break
			dicRewardResult["intRewardRetailPrice"] = intRewardRetailPrice

			self.__lstRewardResult.append(dicRewardResult)	

	def parseUpdate(self, strProjectUrl):
		#更新頁面的檔案名稱格式為： projectID + "_blog_" + pageIndex + ".html"
		#其中pageIndex從0開始，至少會有1個，直接判斷檔案是否存在來判斷有多少個分頁
		projectID = getFileNameInUrl(strProjectUrl)
		dicUpdateResult = {}
		i = 0
		while True:
			blogPageFilePath = self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGR_BLOG_SUFFIXES + "_" + str(i) + self.__LOCAL_PAGE_EXTENSION
			if os.path.isfile(blogPageFilePath) == True:
				with open(blogPageFilePath, "rb") as file:
					strBlogPageSource = file.read()
					root = Selector(text = strBlogPageSource)
					updateElements = root.css(".content > .well.simple")
					for updateElement in updateElements:
						dicUpdateResult["strUrl"] = strProjectUrl
						#更新資訊標題
						strUpdateTitle = updateElement.css("h2 > a::text").extract_first()
						dicUpdateResult["strUpdateTitle"] = strUpdateTitle
						#更新資訊內容
						strUpdateContent = ""
						for x in updateElement.css(".blogpost-content *::text").extract():
							strUpdateContent = strUpdateContent + purifyString(x)
						strUpdateContent = purifyString(strUpdateContent)
						dicUpdateResult["strUpdateContent"] = strUpdateContent
						#更新資訊日期
						strUpdateDate = updateElement.css("h2 > small > time::attr(datatime)").extract_first()
						dicUpdateResult["strUpdateDate"] = strUpdateDate
				i = i+1
			else:
				break
		self.__lstUpdateResult.append(dicUpdateResult)

	def parseComment(self, strProjectUrl):
		self.lstCommentResult = []

	def parseQnA(self, strProjectUrl):
		projectID = getFileNameInUrl(strProjectUrl)
		qaPageFilePath = self.__LOCAL_PAGE_PATH + projectID + self.__LOCAL_PAGR_QA_SUFFIXES + self.__LOCAL_PAGE_EXTENSION
		strQAPageSource = None
		if os.path.isfile(qaPageFilePath) == True:
			with open(qaPageFilePath, "rb") as file: #讀取本地端文件檔案內容到字串
				strQAPageSource = file.read()
			root = Selector(text=strQAPageSource)
			lstQnaElement = root.css("#openQA + h2 + div .panel.panel-default")
			for qnaElement in lstQnaElement:
				dicQnaResult = {}
				dicQnaResult["strUrl"] = strProjectUrl
				#Q&A問題
				strQnaQuestion = qnaElement.css(".panel-heading .panel-title > a::text").extract_first()
				dicQnaResult["strQnaQuestion"] = purifyString(strQnaQuestion)
				#Q&A回覆
				strQnaAnswer = qnaElement.css(".panel-collapse > .panel-body::text").extract_first()
				dicQnaResult["strQnaAnswer"] = purifyString(strQnaAnswer)
				#Q&A回覆時間
				strQnaDate = qnaElement.css(".panel-collapse > .panel-body > small::text").extract_first()
				strQnaDate = purifyString(strQnaDate)
				dicQnaResult["strQnaDate"] = strQnaDate[5:len(strQnaDate)]
				self.__lstQnaResult.append(dicQnaResult)	

	def loadSavedUrlList(self, strTypePageUrl):
		self.__lstSavedUrls = []
		if(os.path.isfile(self.getSaveUrlFilePath(strTypePageUrl)) == True):
			with open(self.getSaveUrlFilePath(strTypePageUrl)) as f:
				for line in f:
					self.__lstSavedUrls.append(purifyString(line))

	def loadIgnoredUrlList(self, strTypePageUrl):
		self.__lstIgnoredUrl = []
		if(os.path.isfile(self.getIgnoredUrlFilePath(strTypePageUrl)) == True):
			self.__lstIgnoredUrl = loadObjFromJsonFile(self.getIgnoredUrlFilePath(strTypePageUrl))

	def getSaveUrlFilePath(self, strTypePageUrl):
		strType = getFileNameInUrl(strTypePageUrl)
		return self.__LOCAL_PAGE_PATH + self.__LOCAL_PAGE_SAVED_URLS_FILENAME + "_" + strType + ".txt"

	def getProjectListFilePath(self, strTypePageUrl):
		strType = getFileNameInUrl(strTypePageUrl)
		return self.__LOCAL_PAGE_PATH + self.__LOCAL_PAGE_PROJECT_LIST_FILENAME + "_" + strType + self.__LOCAL_PAGE_EXTENSION

	def getCreatorFilePath(self, url):
		strCreatorID = getFileNameInUrl(url)
		return self.__LOCAL_PAGE_PATH + self.__LOCAL_PAGE_SPONSOR_FILENAME + "_" + strCreatorID + self.__LOCAL_PAGE_EXTENSION

	def getIgnoredUrlFilePath(self, strTypePageUrl):
		strType = getFileNameInUrl(strTypePageUrl)
		return self.__LOCAL_PAGE_PATH + self.__LCOAL_PAGE_IGNORED_URL_FILENAME + "_" + strType + ".json"

	def addErrorMsg(self, strUrl, strErrMsg):
		if strUrl not in self.__dicErrorMsg:
			self.__dicErrorMsg[strUrl] = []
		self.__dicErrorMsg[strUrl].append(strErrMsg)
		print("[Error " + strUrl + "]: " + strErrMsg)

def main():
	spiderForFlyingV = SpiderForFlyingV()

	#spiderForFlyingV.saveProjectsToLocalFile(STR_URL_TRAVEL, webdriver.Firefox(), isClearSavedUrls = False)
	spiderForFlyingV.parseProjects(STR_URL_TRAVEL)
	#spiderForFlyingV.parseProjectListPage(STR_URL_DESIGNGOODS)
	#spiderForFlyingV.parseProject("https://www.flyingv.cc/project/4585.html")

def createChromeDriver():
	option = webdriver.ChromeOptions()
	option.add_argument('test-type')
	driver = webdriver.Chrome("/Users/yuwei/Documents/Webdriver/chromedriver")
	return driver

if __name__ == '__main__':
	main()
