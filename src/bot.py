import argparse
from bs4 import BeautifulSoup
import logging
import os
import pandas as pd
from pathlib import Path
import random
import requests
import sys
import tweepy

class Bot:
	def __init__(self):
		auth = tweepy.OAuthHandler(os.environ.get('TWITTER_API_KEY'),
			os.environ.get('TWITTER_API_SECRET_KEY'))
			
		auth.set_access_token(os.environ.get('TWITTER_API_TOKEN'),
			os.environ.get('TWITTER_API_SECRET_TOKEN'))

		self.api = tweepy.API(auth)
		
		self.data = pd.read_csv("bird_data/bird_urls.csv")
		
	def run(self):
		self.verify_credentials()
		
		URL = self.get_random()
		self.send_bird(URL)
		
	def get_random(self):
		logging.info('picking a random bird')
		
		number = random.randint(0, self.data.shape[0])
		
		URL = self.data['BIRD URLs'][number]
		logging.info(f'{Path(URL).stem} picked')
		return URL
		
	def send_bird(self, URL):
		page = requests.get(URL)
		soup = BeautifulSoup(page.content, 'html.parser')
		
		image_sent = False
		
		try:
			result = soup.find('div',class_="bird-guide-image")
			img_url = result.find('img')['src']
			img = requests.get(img_url)
			file = open('bird_data/bird.jpg', 'wb')
			file.write(img.content)
			file.close()

			image = 'bird_data/bird.jpg'
			tweet_status = self.api.update_with_media(image, status=URL)
			image_sent = True
			
			os.remove("bird_data/bird.jpg")
			
		except Exception as e:
			logging.error(e, exc_info=True)
			logging.info(URL + ', problem with bird image')
			image_sent = False
			
			if (os.path.exists("bird_data/bird.jpg")):
				os.remove("bird_data/bird.jpg")
		
		if not image_sent:
			return False
		
		try:
			result = soup.find('div', class_="hide-for-tiny hide-for-small hide-for-medium")
			text = result.text.strip('\t \n')
			if len(text) > 275:
				text = self.trim_text(text)
			self.api.update_status(status=text, in_reply_to_status_id=tweet_status.id)
			
		except Exception as e:
			logging.error(e, exc_info=True)
			logging.info(URL + ', problem with bird text')

	def trim_text(self, text):
		text = text.split(".")
		text.pop()
		while len('.'.join(text) + '.') > 275:
			text.pop()
		text = '.'.join(text)
		text = text + '.'
		
		return text

	def verify_credentials(self):
		try:
			self.api.verify_credentials()
			logging.info("All clear")
			
		except Exception as e:
			logging.error(e, exc_info=True)
			logging.info("error during authentication")
	
def prep_log(debug,console):
	log_format = '%(asctime)s %(funcName)s()_%(lineno)s %(levelname)s: %(message)s'
	date_format = '%m/%d/%Y %I:%M:%S %p'

	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	formatter = logging.Formatter(log_format, datefmt=date_format)
	if console:
		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
		console_handler.setFormatter(formatter)
		logger.addHandler(console_handler)

	file_handler = logging.FileHandler('logs/log.log')
	file_handler.setLevel(logging.INFO)
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)
	
def parser():
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--debug", help="DEBUG MODE", action="store_true")
	parser.add_argument("-c", "--console", help="LOG TO CONSOLE", action="store_true")
	argv = parser.parse_args()
	
	prep_log(argv.debug, argv.console)
	
if __name__ == "__main__":
	parser()
	bird = Bot()
	bird.run()