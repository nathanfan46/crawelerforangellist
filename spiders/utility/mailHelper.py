#coding: utf-8

import smtplib
from email.mime.text import MIMEText

class mailHelper:
	DEFAULT_SMTP = "smtp.gmail.com:587"
	DEFAULT_ACCOUNT = "cameoinfotech.tw@gmail.com"
	DEFAULT_PASSWORD = "cameo70525198"

	@staticmethod
	def send(strSubject, strFrom, strTo, strMsg, lstStrTarget, strSmtp = None, strAccount = None, strPassword = None):
		if strSmtp == None:			
			strSmtp = mailHelper.DEFAULT_SMTP
		if strAccount == None:			
			strAccount = mailHelper.DEFAULT_ACCOUNT
		if strPassword == None:			
			strPassword = mailHelper.DEFAULT_PASSWORD
		msg = MIMEText(strMsg)
		msg['Subject'] = strSubject
		msg['From'] = strFrom
		msg['To'] = strTo
		try:
			server = smtplib.SMTP(strSmtp)
			server.ehlo()
			server.starttls()
			server.login(strAccount, strPassword)
			server.sendmail(strAccount, lstStrTarget, msg.as_string())
			server.quit()
		except Exception, e:
			print("[mailHelper] Sending mail failed! ErrorMessage:" + str(e))

