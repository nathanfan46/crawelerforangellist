#coding: utf-8

from scrapy import Selector
import time
import datetime
import os.path
import io
import json
import platform
import sys
import locale
import linecache
# import geonamescache
# from geonamescache.mappers import country


sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utility'))

from utility import *
from mailHelper import *
# from geonames import *
import geonames

from spiderForAngellist import spiderForAngellist

class parserForAngellist:

	PARSE_BASE_URL = "https://angel.co"
	LOCAL_JSON_EXTENSION = ".json"
	LOCAL_PAGE_INFO_EXTENSION = ".txt"
	PARSE_ERROR_URLS_FILENAME = "errorList" 
	PARSE_SAVED_URLS_FILENAME = "parsedList"
	PARSE_SAVED_GEONAME_FILENAME = "geonamescache"

	def __init__(self):
		self.__lstSavedUrls = []
		self.__lstParsedUrls = []
		self.__strDate = ""
		self.__strCategory = ""
		self.__strSubCategory = ""
		self.__lstInverstorResult = {}
		self.__lstExperinceResult = {}
		self.__lstReferenceResult = {}
		self.__lstSyndicateResult = {}
		self.__lstStartupResult = {}
		self.__lstStartupSeriesResult = {}
		self.__lstStartupActivityPressResult = {}
		self.__geonamesCache = {}

	def parseObjectsToLocalFile(self, strDate, strCategory, strSubCategory, intCount = 0, isClearParsedUrls = False):
		strSavedDirectory = spiderForAngellist.strSavedDirectory(strDate, strCategory, strSubCategory)
		# Skip unsaved directory
		if(not os.path.isdir(strSavedDirectory)):
			return

		strParsedFileUrl = parserForAngellist.strParsedUrlFilePath(strDate, strCategory, strSubCategory)

		if(isClearParsedUrls == True and os.path.isfile(strParsedFileUrl)):
			os.remove(strParsedFileUrl)			
		self.__lstParsedUrls = loadStrListInfo(strParsedFileUrl)

		strSavedFileUrl = spiderForAngellist.strSavedUrlFilePath(strDate, strCategory, strSubCategory)
		self.__lstSavedUrls = loadStrListInfo(strSavedFileUrl)
		self.__strDate = strDate
		self.__strCategory = strCategory
		self.__strSubCategory = strSubCategory

		strSavedGeonameFilePath = parserForAngellist.strSavedGeonameFilePath(strDate, strCategory, strSubCategory)
		if(os.path.isfile(strSavedGeonameFilePath)):
			self.__geonamesCache = loadObjFromJsonFile(strSavedGeonameFilePath)

		for i in range(0, len(self.__lstSavedUrls), 1):
			if(self.__lstSavedUrls[i] not in self.__lstParsedUrls):
				self.parseSavedPagesToJson(strCategory, self.__lstSavedUrls[i])

				print("[spiderForAngellist] " + str(i + 1).encode("utf8") + "/" + str(len(self.__lstSavedUrls)).encode("utf8"))
				time.sleep(0.5)
			else:
				print("[parserForAngellist] " + self.__lstSavedUrls[i] + " has been parsed")		
			# break

		if(strCategory == "People"):
			strInvestorJsonFilePath = parserForAngellist.getInvestorJsonFilePath(self.__strDate, self.__strCategory, self.__strSubCategory)
			saveObjToJson(self.__lstInverstorResult, strInvestorJsonFilePath)

			strInvestorExperienceJsonFilePath = parserForAngellist.getInvestorExperienceJsonFilePath(self.__strDate, self.__strCategory, self.__strSubCategory)
			saveObjToJson(self.__lstExperinceResult, strInvestorExperienceJsonFilePath)

			strInvestorReferenceJsonFilePath = parserForAngellist.getInvestorReferenceJsonFilePath(self.__strDate, self.__strCategory, self.__strSubCategory)
			saveObjToJson(self.__lstReferenceResult, strInvestorReferenceJsonFilePath)

			strSyndicateJsonFilePath = parserForAngellist.getSyndicateJsonFilePath(self.__strDate, self.__strCategory, self.__strSubCategory)
			saveObjToJson(self.__lstSyndicateResult, strSyndicateJsonFilePath)
		elif(strCategory == "Location" or strCategory == "Market"):
			strStartupJsonFilePath = parserForAngellist.getStartupJsonFilePath(self.__strDate, self.__strCategory, self.__strSubCategory)
			saveObjToJson(self.__lstStartupResult, strStartupJsonFilePath)

			strStartupPressJsonFilePath = parserForAngellist.getStartupSeriesJsonFilePath(self.__strDate, self.__strCategory, self.__strSubCategory)
			saveObjToJson(self.__lstStartupSeriesResult, strStartupPressJsonFilePath)

			strStartupActivityPressJsonFilePath = parserForAngellist.getStartupActivityPressJsonFilePath(self.__strDate, self.__strCategory, self.__strSubCategory)
			saveObjToJson(self.__lstStartupActivityPressResult, strStartupActivityPressJsonFilePath)

		saveObjToJson(self.__geonamesCache, strSavedGeonameFilePath)

	def parseSavedPagesToJson(self, strCategory, strUrl):
		print("[parserForAngellist] Parsing " + strUrl)
		try:

			if(strCategory == "People"): 
				self.parsePeopleToJson(strUrl)
			elif(strCategory == "Location" or strCategory == "Market"):
				self.parseStartupToJson(strUrl)
			#appendTextFile(strUrl, parserForAngellist.strParsedUrlFilePath(strDate, strCategory, strSubCategory))
			return True
		except Exception, e:
			self.PrintException()
			print("[parserForAngellist] Failed! ErrorMessage:" + str(e))
			appendTextFile("[" + strUrl + "] " + repr(e), parserForAngellist.strErrorListFilePath(self.__strDate, self.__strCategory, self.__strSubCategory))
			import pdb; pdb.set_trace()
			return False					

	def parsePeopleToJson(self, strUrl):
		strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		dicInvestorResult = {};
		dicInvestorResult['strUrl'] = strUrl
		dicInvestorResult['strCrawlTime'] = self.__strDate

		strPeopleFilePath = spiderForAngellist.getPeopleLocalFilePath(strUrl, self.__strDate, self.__strCategory, self.__strSubCategory)
		print("[parserForAngellist] Parsing " + strPeopleFilePath)

		if(os.path.isfile(strPeopleFilePath)):
			with open(strPeopleFilePath, "rb") as file: #讀取本地端文件檔案內容到字串
				strPageSource = file.read()

			root = Selector(text=strPageSource)
			strName = root.css("h1.js-name::text").extract_first().strip()
			dicInvestorResult['strName'] = strName
			lstDivInfo = root.css("div.tags > span.tag")

			strLocation = ''
			lstStrRole = []
			for divInfo in lstDivInfo:
				if(divInfo.css('span.fontello-location.icon')):
					if(divInfo.css("::attr(title)") and (divInfo.css("::attr(title)").extract_first() != '')):	
						strAllLocation = divInfo.css("::attr(title)").extract_first().strip()
					elif(divInfo.css("::attr(oldtitle)")):
						strAllLocation = divInfo.css("::attr(oldtitle)").extract_first().strip()
					else:
						strAllLocation = divInfo.css("::text").extract_first().strip()

					lstStrLocation = strAllLocation.split(',')
					lstStrLocation = map(unicode.strip, lstStrLocation)
					strLocation = lstStrLocation[0]
				elif(divInfo.css('span.fontello-tag-1.icon')):
					if(divInfo.css("::attr(title)") and (divInfo.css("::attr(title)").extract_first() != '')):	
						strRole = divInfo.css("::attr(title)").extract_first().strip()
					elif(divInfo.css("::attr(oldtitle)")):
						strRole = divInfo.css("::attr(oldtitle)").extract_first().strip()
					else:
						strRole =divInfo.css("::text").extract_first().strip()
					lstStrRole = strRole.split(',')
					lstStrRole = map(unicode.strip, lstStrRole)

			dicInvestorResult['lstStrRole'] = lstStrRole

			dicInvestorResult['strLocation'] = strLocation
			dicLocation = self.parseLocation(strLocation)
			print("location parse complete")
			# strGeonameId = geonames.search(q=strLocation)[0]['geonameId']
			# dicGeoname = geonames.get(strGeonameId)
			# bbox = dicGeoname['bbox']
			# strCountry = dicGeoname['countryCode']
			# strContinent = dicGeoname['continentCode']
			# dicCity = geonames.findCity(north=bbox['north'], south=bbox['south'], east=bbox['east'], west=bbox['west'])[0]
			# strCity = dicCity['name']

			dicInvestorResult['strCity'] = dicLocation['strCity']
			dicInvestorResult['strCountry'] = dicLocation['strCountry']
			dicInvestorResult['strContinent'] = dicLocation['strContinent']

			intFollower = 0
			if(root.css("a.followers_count.follow_link")):
				strFollower = root.css("a.followers_count.follow_link::text").extract_first().strip()
				strFollower = strFollower.split(' ')[0].replace(",", "")
				intFollower = int(strFollower)
			dicInvestorResult['intFollower'] = intFollower

			intFollowing = 0
			if(root.css("a.following_count.follow_link")):
				strFollowing = root.css("a.following_count.follow_link::text").extract_first().strip()
				strFollowing = strFollowing.split(' ')[0].replace(",", "")
				intFollowing = int(strFollowing)
			dicInvestorResult['intFollowing'] = intFollowing

			lstStrMarket = []
			lstStrMarketIndustry = []

			lstAboutContent = root.css("div.s-grid0-colMd24.s-vgBottom2.field")
			for aboutContent in lstAboutContent:

				if(aboutContent.css("div.s-grid-colMd5 > div.u-uppercase::text").extract_first().strip() == 'Locations'):
					strLocation = aboutContent.css("div.s-grid-colMd5 > div.u-uppercase::text").extract_first().strip();
					lstStrMarket = aboutContent.css('div.s-grid-colMd17 > div.item > div.module_taggings > div.content > div.value > span.tag > a::text').extract()
				elif(aboutContent.css("div.s-grid-colMd5 > div.u-uppercase::text").extract_first().strip() == 'Markets'):
					strMarket = aboutContent.css("div.s-grid-colMd5 > div.u-uppercase::text").extract_first().strip();
					lstStrMarketIndustry = aboutContent.css('div.s-grid-colMd17 > div.item > div.module_taggings > div.content > div.value > span.tag > a::text').extract()
			
			dicInvestorResult['lstStrMarketIndustry'] = lstStrMarketIndustry
			dicInvestorResult['lstStrMarket'] = lstStrMarket

			lstExperience = []
			lstDivExperience = root.css('div.feature.startup_roles.experience')
			for divExperience in lstDivExperience:
				dicExperienceResult = {}
				dicExperienceResult['strUrl'] = strUrl
				dicExperienceResult['strName'] = strName
				strCompany = divExperience.css('a.u-unstyledLink::text').extract_first().strip()
				dicExperienceResult['strCompany'] = strCompany
				strRole = divExperience.css('div.line > span.medium-font::text').extract_first().strip()
				dicExperienceResult['strRole'] = strRole
				lstExperience.append(dicExperienceResult)

			self.__lstExperinceResult[strUrl] = lstExperience
			
			#print("[parserForAngellist] lstExperience " + str(lstExperience))

			lstReference = []
			lstDivReference = root.css('div.profiles-show.review')
			for divReference in lstDivReference:
				dicReferenceResult = {}
				dicReferenceResult['strUrl'] = strUrl
				dicReferenceResult['strName'] = strName
				strContent = divReference.css('div.review-content::text').extract_first().strip()
				dicReferenceResult['strContent'] = strContent			
				# strAuthor = divReference.css('div.annotation > div.profile-link::text').extract_first().strip() 
				# dicReferenceResult['strAuthor'] = strAuthor
				lstStrAuthorContext = divReference.css('div.annotation').xpath('.//text()').extract() 
				lstStrAuthorContext = map(unicode.strip, lstStrAuthorContext)
				lstStrAuthorContext = filter(lambda x: len(x) > 1, lstStrAuthorContext)
				strAuthor = lstStrAuthorContext[0]
				strAuthorContext = ','.join(lstStrAuthorContext)
				# strAuthorContext = divReference.css('div.annotation').extract_first().strip() 
				dicReferenceResult['strAuthor'] = strAuthor
				dicReferenceResult['strAuthorContext'] = strAuthorContext
				lstReference.append(dicReferenceResult)

			self.__lstReferenceResult[strUrl] = lstReference

			#print("[parserForAngellist] lstReference " + str(lstReference))

			
			self.__lstInverstorResult[strUrl] = dicInvestorResult
			# strInvestorJsonFilePath = parserForAngellist.getInvestorJsonFilePath(strUrl, self.__strDate, self.__strCategory, self.__strSubCategory)
			# saveObjToJson(dicInvestorResult, strInvestorJsonFilePath)
			# print("[parserForAngellist.] Result " + str(dicInvestorResult))

			dicSyndicateResult = {};
			divSyndicate = root.css("div.back_syndicate_button")
			if(divSyndicate):
				uSyndicateUrl = divSyndicate.css("a::attr(href)").extract_first().strip()
				strSyndicateUrl = parserForAngellist.PARSE_BASE_URL + str(uSyndicateUrl)
				self.parseSyndicateToJson(strUrl, strSyndicateUrl)

	def parseSyndicateToJson(self, strUrl, strSyndicateUrl):
		dicSyndicateResult = {};
		strSyndicateFilePath = spiderForAngellist.getSyndicateLocalFilePath(strUrl, self.__strDate, self.__strCategory, self.__strSubCategory)
		if(os.path.isfile(strSyndicateFilePath)):
			print("[parserForAngellist] Parsing " + strSyndicateFilePath)

			with open(strSyndicateFilePath, "rb") as file: #讀取本地端文件檔案內容到字串
				strPageSource = file.read()

			root = Selector(text=strPageSource)
			dicSyndicateResult['strUrl'] = strSyndicateUrl
			dicSyndicateResult['strCrawlTime'] = self.__strDate
			dicSyndicateResult['strName'] = root.css('div.gridspan.antialiased > h1::text').extract_first()
			dicSyndicateResult['strManager'] = root.css('div.managers > div.fixed_width.u-inlineBlock > div > a.u-uncoloredLink::text').extract()

			intTypicalInvestment = 0
			fCarryPerDeal = 0.0
			intBackerCount = 0

			strTerms = root.css('ul.syndicate_terms > li::text').extract()
			for strTerm in strTerms:
				if "Total Carry Per Deal:" in strTerm: 
					strCarryPerDeal = strTerm.replace('Total Carry Per Deal:', '').replace('%','').strip()
					fCarryPerDeal = float(strCarryPerDeal)
					dicSyndicateResult['fCarryPerDeal'] = fCarryPerDeal
				elif "Typical Investment:" in strTerm:
					# strTypicalInvestment = strTerm[strTerm.rfind('$')+1:].strip().replace(',', '')
					# intTypicalInvestment = int(strTypicalInvestment)
					# dicSyndicateResult['intTypicalInvestment'] = intTypicalInvestment
					# Use str instead
					strTypicalInvestment = strTerm[strTerm.rfind(':')+1:].strip()
					dicSyndicateResult['strTypicalInvestment'] = intTypicalInvestment
				elif "Backed by" in strTerm:
					strBackerCount = strTerm[strTerm.find('Backed by')+9:strTerm.find('Accredited Investor')].strip()
					intBackerCount = int(strBackerCount)
					dicSyndicateResult['intBackerCount'] = intBackerCount


			intBackedBy = 0
			intDealsPerYear = 0

			divSyndicateSummaryItems = root.css('ul.syndicate_summary > li')
			for divSyndicateSummaryItem in divSyndicateSummaryItems:
				strLabel = divSyndicateSummaryItem.css('div.syndicate_summary_label::text').extract_first().strip()
				if "Backed By" in strLabel:
					strBackedBy = divSyndicateSummaryItem.css('div.syndicate_summary_value::text').extract_first().strip()
					strCurrency = strBackedBy[:1]
					strBackedBy = strBackedBy[1:]

					if(strCurrency == u'$'):
						strCurrency = 'USD'
					elif (strCurrency == u'€'):
						strCurrency = 'EUR'

					intBase = 1
					if(strBackedBy[-1:] == u'K'):
						intBase = 1000
						strBackedBy = strBackedBy[:-1]
					elif(strBackedBy[-1:] == u'M'):
						intBase = 1000000
						strBackedBy = strBackedBy[:-1]

					intBackedBy = int(locale.atof(strBackedBy.replace(",", "")) * intBase)

					dicSyndicateResult['strCurrency'] = strCurrency
					dicSyndicateResult['intBackedBy'] = intBackedBy

				elif "Expected Deals/Year" in strLabel:
					strDealsPerYear = divSyndicateSummaryItem.css('div.syndicate_summary_value::text').extract_first().strip()
					intDealsPerYear = int(strDealsPerYear)
					dicSyndicateResult['intDealsPerYear'] = intDealsPerYear

			lstStrBackers = root.css('div.gridspan > div.feature > figure > h3 > a.profile-link::text').extract()
			lstOverflowBackers = root.css('div.gridspan > ul.overflow > li > h4 > a.profile-link::text').extract()
			lstStrBackers.extend(lstOverflowBackers)
			dicSyndicateResult['lstStrBackers'] = lstStrBackers

			self.__lstSyndicateResult[strSyndicateUrl] = dicSyndicateResult

			# print("[parserForAngellist] Syndicate " + str(dicSyndicateResult))
			#import pdb; pdb.set_trace()

	def parseStartupToJson(self, strUrl):
		strObjectID = getFileNameInUrl(strUrl)
		dicStartupResult = {};
		dicStartupResult['strUrl'] = strUrl
		dicStartupResult['strCrawlTime'] = self.__strDate

		strStartupFilePath = spiderForAngellist.getOverviewLocalFilePath(strUrl, self.__strDate, self.__strCategory, self.__strSubCategory)
		print("[parserForAngellist] Parsing " + strStartupFilePath)

		if(os.path.isfile(strStartupFilePath)):
			with open(strStartupFilePath, "rb") as file: #讀取本地端文件檔案內容到字串
				strPageSource = file.read()

			root = Selector(text=strPageSource)
			strCompany = root.css('div.text > div.name_holder > h1.name::text').extract_first().strip()
			dicStartupResult['strCompany'] = strCompany

			# Some company didn't have intros, and h2 has some parsing error
			strIntro = root.css('div.main.standard > div.text').css('p::text').extract_first()
			dicStartupResult['strIntro'] = strIntro

			lstStrProduct = root.css('div.product_desc > div.show.windows > div.content::text').extract()
			dicStartupResult['lstStrProduct'] = lstStrProduct

			lstStrFounders = []
			lstStrFoundersDesc = []
			divFoundersSection = root.css('div.founders.section > div.startups-show-sections >  div.startup_roles')
			if(divFoundersSection):
				lstDivFounders = divFoundersSection.css('div.text')
				for divFounder in lstDivFounders:
					strFounderName = divFounder.css('div.name > a::text').extract_first()
					lstFounderDescs = divFounder.css('div.bio > p').css('::text').extract()
					# lstFounderDescs = map(unicode.strip, lstFounderDescs)
					lstFounderDescs = filter(lambda x: len(x) > 1, lstFounderDescs)
					strFounderDesc = ''.join(lstFounderDescs)
					lstStrFounders.append(strFounderName)
					lstStrFoundersDesc.append(strFounderDesc)

				# lstStrFoundersName = divFoundersSection.css('div.text > div.name > a::text').extract()
				# lstStrFoundersName = divFoundersSection.css('div.text > div.name > a::text').extract()
				dicStartupResult['lstStrFounders'] = lstStrFounders
				dicStartupResult['lstStrFoundersDesc'] = lstStrFoundersDesc

			lstStrTeam = []
			lstStrTeamDesc = []
			divTeamSection = root.css('div.team.section > div.startups-show-sections > div.group')
			if(divTeamSection):
				lstDivTeam = divTeamSection.css('div.text')
				for divTeam in lstDivTeam:
					strTeamName = divTeam.css('div.name > a::text').extract_first()
					lstTeamDescs = divTeam.css('div.bio > p').css('::text').extract()
					lstTeamDescs = filter(lambda x: len(x) > 1, lstTeamDescs)
					strTeamDesc = ''.join(lstTeamDescs)
					lstStrTeam.append(strTeamName)
					lstStrTeamDesc.append(strTeamDesc)

				dicStartupResult['lstStrTeam'] = lstStrTeam
				dicStartupResult['lstStrTeamDesc'] = lstStrTeamDesc

			lstLocationIndustry = root.css('div.main.standard > div.text > div.tags').css('a.tag::text').extract()

			strLocation = ''
			lstIndustry = []
			if(len(lstLocationIndustry) > 0):
				strLocation = lstLocationIndustry[0]
				lstIndustry = lstLocationIndustry[1:]
			dicStartupResult['strLocation'] = strLocation
			dicStartupResult['lstIndustry'] = lstIndustry

			dicLocation = self.parseLocation(strLocation)

			dicStartupResult['strCity'] = dicLocation['strCity']
			dicStartupResult['strCountry'] = dicLocation['strCountry']
			dicStartupResult['strContinent'] = dicLocation['strContinent']

			lstStrFollowers = self.parseStartupFollowersToJson(strUrl)
			dicStartupResult['lstStrFollowers'] = lstStrFollowers

			lstStrInvestor = []
			divFundingSection = root.css('div.past_financing.section.startups-show-sections')
			if(divFundingSection):
				lstStrInvestor = divFundingSection.css('ul.roles > li.role').css('div.name > a::text').extract()

			dicStartupResult['lstStrInvestor'] = lstStrInvestor

			isFundraising = False
			divFundraisingHeader = root.css('div.fundraising.header')
			if(divFundraisingHeader):
				strFundraising = divFundraisingHeader.css('::text').extract_first()
				if "Fundraising" in strFundraising:
					isFundraising = True

			dicStartupResult['isFundraising'] = isFundraising

			lstStartupSeries = []
			if(divFundingSection):
				lstDivStartupSeries = divFundingSection.css('div.startups-show-sections.startup_rounds > ul.startup_rounds.with_rounds > li.startup_round')
				for divStartupSeries in lstDivStartupSeries:
					dicStartupSeriesResult = {}
					dicStartupSeriesResult['strUrl'] = strUrl
					dicStartupSeriesResult['strCrawlTime'] = self.__strDate
					dicStartupSeriesResult['strCompany'] = strCompany

					strSeriesType = ''
					divStartupSeriesType = divStartupSeries.css('div.details.inner_section > div.header > div.type')
					if(divStartupSeriesType):
						strSeriesType = divStartupSeriesType.css('::text').extract_first().strip()
					dicStartupSeriesResult['strSeriesType'] = strSeriesType

					strSeriesMoney = u'Unknown'
					intSeriesMoney = 0
					divStartupSeriesMoney = divStartupSeries.css('div.details.inner_section > div.raised')
					if(divStartupSeriesMoney):
						lstStrSeriesMoney = divStartupSeriesMoney.css('::text').extract()
						strSeriesMoney = "".join(lstStrSeriesMoney).strip()

					if(strSeriesMoney != u'Unknown'):
						strCurrency = strSeriesMoney[:1]
						strSeriesMoney = strSeriesMoney[1:]

						if(strCurrency == u'$'):
							strCurrency = 'USD'
						elif (strCurrency == u'€'):
							strCurrency = 'EUR'

						intBase = 1
						if(strSeriesMoney[-1:] == u'K'):
							intBase = 1000
							strSeriesMoney = strSeriesMoney[:-1]
						elif(strSeriesMoney[-1:] == u'M'):
							intBase = 1000000
							strSeriesMoney = strSeriesMoney[:-1]

						intSeriesMoney = int(locale.atof(strSeriesMoney.replace(",", "")) * intBase)

					if(intSeriesMoney == 0):
						dicStartupSeriesResult['intSeriesMoney'] = strSeriesMoney
					else:
						dicStartupSeriesResult['intSeriesMoney'] = intSeriesMoney
						dicStartupSeriesResult['strCurrency'] = strCurrency

					strSeriesDate = ''
					divStartupSeriesDate = divStartupSeries.css('div.details.inner_section > div.header > div.date_display')
					if(divStartupSeriesDate):
						strSeriesDate = divStartupSeriesDate.css('::text').extract_first()
					dicStartupSeriesResult['strSeriesDate'] = strSeriesDate

					lstStrInvestor = divStartupSeries.css('div.participant > div.text > div.name > a::text').extract()
					lstStrInvestorUrl = divStartupSeries.css('div.participant > div.text > div.name > a::attr(href)').extract()
					dicStartupSeriesResult['lstStrInvestor'] = lstStrInvestor
					dicStartupSeriesResult['lstStrInvestorUrl'] = lstStrInvestorUrl

					lstStartupSeries.append(dicStartupSeriesResult)
					# print("[parserForAngellist] Startup Series" + str(dicStartupSeriesResult))
					# import pdb; pdb.set_trace()

				self.__lstStartupSeriesResult[strUrl] = lstStartupSeries
				

			self.parseStartupActivityPressToJson(strUrl)

			self.__lstStartupResult[strUrl] = dicStartupResult
			# print("[parserForAngellist] Startup " + str(dicStartupResult))


	def parseStartupFollowersToJson(self, strUrl):
		lstStrFollowers = []
		strStartupFollowersFilePath = spiderForAngellist.getFollowersLocalFilePath(strUrl, self.__strDate, self.__strCategory, self.__strSubCategory)
		if(os.path.isfile(strStartupFollowersFilePath)):
			with open(strStartupFollowersFilePath, "rb") as file: #讀取本地端文件檔案內容到字串
				strPageSource = file.read()

			root = Selector(text=strPageSource)

			lstStrFollowers = root.css('div.text > div.name > a::text').extract()

		return lstStrFollowers

	def parseStartupActivityPressToJson(self, strUrl):
		lstActivityPress = []
		strStartupActivityPressFilePath = spiderForAngellist.getActivityPressLocalFilePath(strUrl, self.__strDate, self.__strCategory, self.__strSubCategory)
		if(os.path.isfile(strStartupActivityPressFilePath)):
			with open(strStartupActivityPressFilePath, "rb") as file: #讀取本地端文件檔案內容到字串
				strPageSource = file.read()

			root = Selector(text=strPageSource)

			lstDivActivityPress = root.css('div.startups-show-helpers.active')
			for divActivityPress in lstDivActivityPress:
				dicActivityPress = {}
				dicActivityPress['strUrl'] = strUrl
				dicActivityPress['strSourceUrl'] = divActivityPress.css('div.headline > a::attr(href)').extract_first()
				dicActivityPress['strSourceDomain'] = divActivityPress.css('div.type_and_actions > span.type::text').extract_first()
				dicActivityPress['strTitle'] = divActivityPress.css('div.headline > a::text').extract_first()
				dicActivityPress['strContent'] = divActivityPress.css('div.summary::text').extract_first()
				dicActivityPress['strDate'] = divActivityPress.css('div.timestamp > span::text').extract_first()
				lstActivityPress.append(dicActivityPress)

		self.__lstStartupActivityPressResult[strUrl] = lstActivityPress
		# print("[parserForAngellist] Startup Activity Press" + str(lstActivityPress))

	def parseLocation(self, strLocation):
		print('[parserForAngellist] Parsing location : ' + strLocation)

		if(strLocation.strip() == ''):
			dicEmptyGeoname = {}
			dicEmptyGeoname['strCity'] = ''
			dicEmptyGeoname['strCountry'] = ''
			dicEmptyGeoname['strContinent'] = ''
			return dicEmptyGeoname

		if(self.__geonamesCache.get(strLocation) == None):
			dicGeonameCache = {} 
			dicSearchResult = geonames.search(q=strLocation, maxRows=10, featureClass='P') #countryBias='US'
			lstStrLocation = strLocation.split()
			while (dicSearchResult == None or len(dicSearchResult) == 0) and len(lstStrLocation) > 1:
				del lstStrLocation[-1]
				strSubLocation = ' '.join(lstStrLocation)
				print('[parserForAngellist] Parsing location : ' + strSubLocation)
				dicSearchResult = geonames.search(q=strSubLocation, maxRows=10, featureClass='P') #countryBias='US'

			if(dicSearchResult == None or len(dicSearchResult) == 0):
				dicNotFoundGeoname = {}
				dicNotFoundGeoname['strCity'] = ''
				dicNotFoundGeoname['strCountry'] = ''
				dicNotFoundGeoname['strContinent'] = ''
				return dicNotFoundGeoname

			strGeonameId = dicSearchResult[0]['geonameId']
			# import pdb; pdb.set_trace()
			dicGeoname = geonames.get(strGeonameId)
			strFclName = dicGeoname['fclName']
			strCountry = dicGeoname['countryCode']
			strContinent = dicGeoname['continentCode']
			# import pdb; pdb.set_trace()
			strCity = ''
			if 'city' in strFclName:
				strCity = dicGeoname['name']
			elif dicGeoname.get('bbox') != None:
				bbox = dicGeoname['bbox']
				dicCity = geonames.findCity(north=bbox['north'], south=bbox['south'], east=bbox['east'], west=bbox['west'])[0]
				strCity = dicCity['name']
			else:
				strCity = strLocation
				import pdb; pdb.set_trace()
			
			dicGeonameCache['strCity'] = strCity
			dicGeonameCache['strCountry'] = strCountry
			dicGeonameCache['strContinent'] = strContinent
			self.__geonamesCache[strLocation] = dicGeonameCache

		return self.__geonamesCache[strLocation]

	def PrintException(self):
		exc_type, exc_obj, tb = sys.exc_info()
		f = tb.tb_frame
		lineno = tb.tb_lineno
		filename = f.f_code.co_filename
		linecache.checkcache(filename)
		line = linecache.getline(filename, lineno, f.f_globals)
		print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

	@staticmethod
	def strParsedResultPath():
		if(os.name == "nt"):
			# return "C:/Users/Nathan/Documents/ParsedResult/"
			return "C:/Users/Administrator/Documents/ParsedResult/"
		elif(os.name == "posix"):
			return "/Users/yuwei/Desktop/ParseResult/angellist/"

	@staticmethod				
	def strSavedGeonameFilePath(strDate, strCategory, strSubCategory):							#geonames cache
		return parserForAngellist.strParsedResultPath() + "/" + parserForAngellist.PARSE_SAVED_GEONAME_FILENAME + parserForAngellist.LOCAL_JSON_EXTENSION

	@staticmethod				
	def strParsedUrlFilePath(strDate, strCategory, strSubCategory):							#本次已抓取url列表
		return parserForAngellist.strParsedResultPath() + "/" + strDate + "/" + strCategory + "/" + strSubCategory + "/" + parserForAngellist.PARSE_SAVED_URLS_FILENAME + parserForAngellist.LOCAL_PAGE_INFO_EXTENSION

	@staticmethod				
	def strErrorListFilePath(strDate, strCategory, strSubCategory):							#error列表
		return parserForAngellist.strParsedResultPath() + "/" + strDate + "/" + strCategory + "/" + strSubCategory + "/" + parserForAngellist.PARSE_ERROR_URLS_FILENAME + parserForAngellist.LOCAL_PAGE_INFO_EXTENSION

	@staticmethod
	def getInvestorJsonFilePath(strDate, strCategory, strSubCategory): 	#People
		# strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		return parserForAngellist.strParsedResultPath() + strDate + "/" + strCategory + "/" + strSubCategory + "/angellist_investor" + parserForAngellist.LOCAL_JSON_EXTENSION

	@staticmethod
	def getInvestorExperienceJsonFilePath(strDate, strCategory, strSubCategory): 	#People
		# strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		return parserForAngellist.strParsedResultPath() + strDate + "/" + strCategory + "/" + strSubCategory + "/angellist_manager_experience" + parserForAngellist.LOCAL_JSON_EXTENSION

	@staticmethod
	def getInvestorReferenceJsonFilePath(strDate, strCategory, strSubCategory): 	#People
		# strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		return parserForAngellist.strParsedResultPath() + strDate + "/" + strCategory + "/" + strSubCategory + "/angellist_manager_reference" + parserForAngellist.LOCAL_JSON_EXTENSION

	@staticmethod
	def getSyndicateJsonFilePath(strDate, strCategory, strSubCategory): 	#People
		# strObjectID = getFileNameInUrl(spiderForAngellist.getPureUrl(strUrl))
		return parserForAngellist.strParsedResultPath() + strDate + "/" + strCategory + "/" + strSubCategory + "/angellist_syndicate" + parserForAngellist.LOCAL_JSON_EXTENSION

	@staticmethod
	def getStartupJsonFilePath(strDate, strCategory, strSubCategory): 	#Startup
		# strObjectID = getFileNameInUrl(strUrl)
		return parserForAngellist.strParsedResultPath() + strDate + "/" + strCategory + "/" + strSubCategory + "/angellist_startup" + parserForAngellist.LOCAL_JSON_EXTENSION

	@staticmethod
	def getStartupSeriesJsonFilePath(strDate, strCategory, strSubCategory): 	#Startup
		# strObjectID = getFileNameInUrl(strUrl)
		return parserForAngellist.strParsedResultPath() + strDate + "/" + strCategory + "/" + strSubCategory + "/angellist_startup_series" + parserForAngellist.LOCAL_JSON_EXTENSION

	@staticmethod
	def getStartupActivityPressJsonFilePath(strDate, strCategory, strSubCategory): 	#Startup
		# strObjectID = getFileNameInUrl(strUrl)
		return parserForAngellist.strParsedResultPath() + strDate + "/" + strCategory + "/" + strSubCategory + "/angellist_startup_press" + parserForAngellist.LOCAL_JSON_EXTENSION


	@staticmethod
	def parseAllObjectsOfCategory(strDate, strCategory, lstStrSubCategory = []):
		if len(lstStrSubCategory) == 0:
			dicMapping = spiderForAngellist.getCategoryMapping()
			for strSubCategoryInMapping in dicMapping[strCategory]:
				parser = parserForAngellist()
				parser.parseObjectsToLocalFile(strDate, strCategory, strSubCategoryInMapping)
		else:
			for strSubCategory in lstStrSubCategory:
				parser = parserForAngellist()
				parser.parseObjectsToLocalFile(strDate, strCategory, strSubCategory)

def main():
	# parserForAngellist.parseAllObjectsOfCategory("2016-02-25", "People", ["Investors"])
	# parserForAngellist.parseAllObjectsOfCategory("2016-02-25", "Location", ["Taiwan"])
	parserForAngellist.parseAllObjectsOfCategory("2016-02-25", "People", ["SyndicateLeads"])

if __name__ == '__main__':
	main()	