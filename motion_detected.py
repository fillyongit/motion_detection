#!/usr/bin/env python3.2

import os
import logging
import glob
import time
import smtplib
import subprocess
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class CONSTANTS:
	LOGFILE = os.path.join('/home/pi', 'motion_detection.log')
	SOUNDFILE = os.path.join('/home/pi', 'example.mp3')
	CAPTURE_VIDEO_TIME = 0.5 # minuti
	NEXT_NOTIFY_TIME = 5 # minuti
	FROMADDRESS = "filippini.alessio@gmail.com"
	TOADDRESS = "filippini.alessio@gmail.com"

	# il metodo magico seguente inibisce il set di una proprietà.
	def __setattr__(self, *_):
		pass

CONST = CONSTANTS()

logging.basicConfig(filename=CONST.LOGFILE, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%d/%m/%Y %H:%M:%S', filemode='w', level=logging.DEBUG)

logging.info("MotionDetection avviato alle " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

bodytemplate = "Individuato movimento dalla webcam del tinello il %s"
body = ""

def getSize(path):
	start_time = time.time()
	total_size = 0
	if os.path.isdir(path):
		for dirpath, dirnames, filenames in os.walk(path):
			for filename in filenames:
				fp = os.path.join(dirpath, filename)
				total_size += os.path.getsize(fp)
		#print(time.time() - start_time, "seconds")
		return total_size
	else:
		return os.path.getsize(path)

def getLastSwf(path):
	files = sorted(filter(os.path.isfile, glob.glob(path + '/*.swf')), key=lambda item: os.path.getmtime(os.path.join(path, item)), reverse=True)
	return files[0]

path = '/tmp/motion'
oldsize = 0
while (os.path.exists(path) is False):
	time.sleep(5)

oldsize = getSize(path)

newsize = 0
lastnotification = None
notificationsnum = 0
while True:
	newsize = getSize(path)
	diff = datetime.now() - (lastnotification or datetime(1970, 1, 1)) 
	logging.debug("{0:.2f}".format(diff.seconds / 60))
	if (newsize > oldsize): 
		oldsize = newsize
		if (diff.seconds > CONST.NEXT_NOTIFY_TIME * 60 * ):
			lastnotification = datetime.now()
			logging.debug(lastnotification)		
			
			notificationsnum+=1
			#p = subprocess.Popen(["omxplayer", "-o", "local", CONST.SOUNDFILE], subprocess.PIPE)

			time.sleep(CONST.CAPTURE_VIDEO_TIME * 60) # diamo il tempo a motion di registrare un swf un pò più corposo.
			lastswf = getLastSwf(path)
		
			msg = MIMEMultipart()
			msg['From'] = CONST.FROMADDRESS
			msg['To'] = CONST.TOADDRESS
			msg['Subject'] = "Notifica da fillyhome webcam tinello"

			body = bodytemplate % (time.strftime("%c"))
			msg.attach(MIMEText(body, 'plain'))
			
			logging.info('rilevato movimento!')
			logging.info('spedizione notifica')
			logging.debug(lastswf)
		
			attachment = open(os.path.join(path, lastswf), "rb")
			part = MIMEBase('application', 'octet-stream')
			part.set_payload(attachment.read())
			encoders.encode_base64(part)
			part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(lastswf)) 
			msg.attach(part)

			text = msg.as_string()

			server = smtplib.SMTP('smtp.gmail.com', 587)
			server.starttls()
			server.login('filippini.alessio@gmail.com', 'angurp-95')
			server.sendmail('filippini.alessio@gmail.com', 'filippini.alessio@gmail.com', text)
			server.quit()
		else:
			logging.info("rilevato movimento ma non sono ancora passati " + str(CONST.NEXT_NOTIFY_TIME) + " minuti dall'ultima notifica")
	time.sleep(5)
	
	
