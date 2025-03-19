# -*- coding: utf-8 -*-
import scrapy
from w3lib.http import basic_auth_header
#import csv
import logging
import requests
from datetime import datetime, timedelta
import json
from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP

class CheckSpidersProxySpider(scrapy.Spider):
	name = "check_spiders_proxy"
	download_delay = 5
	api_key = '8f418557803c451ab42e5d7b77ea45ce'

	#api_key = sys.argv[1]
    #api_key = '8f418557803c451ab42e5d7b77ea45ce'
    #project_id = '219365' proxy
    #project_id = '256572' no_proxy

	def __init__(self, max_page=0, *args, **kwargs):
		super(CheckSpidersProxySpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

		#deleting jobs
		url_job = 'https://storage.scrapinghub.com/jobq/219365/list?format=json&state=finished&spider=' + self.name
		robot_jobs = requests.get(url_job, auth=(self.api_key,''))

		if robot_jobs.status_code == 200:
			delete_jobs = json.loads(robot_jobs.text)
			for d_jobs in delete_jobs:
				try:
					r_deljob = requests.post('https://app.scrapinghub.com/api/jobs/delete.json', 
											 auth=(self.api_key,''), 
											 data={'project': '219365', 'job': d_jobs['key']})
					if r_deljob.status_code == 200:
						logging.warning('Deletado com sucesso')
				except:
					logging.error('Erro ao deletar')

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	#Dependendo do robô pode ser feito de modo implicito
	def start_requests(self):
		
		reader = []
		auth = basic_auth_header(self.api_key, '')
		
		#scrapy
		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=anibis&state=deleted',
			'robot': 'anibis' 
		}) # anibis 
		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=comptoir&state=deleted',
			'robot': 'comptoir'
		}) # comptoir
		
		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=homegate&state=deleted',
			'robot': 'homegate'
		}) # homegate

		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=immobilier&state=deleted',
			'robot': 'immobilier'
		}) # immobilier

		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=immobilier2&state=deleted',
			'robot': 'immobilier2'
		}) # immobilier2
		
		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=immoscout24&state=deleted',
			'robot': 'immoscout24'
		}) # immoscout24

		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=immostreet&state=deleted',
			'robot': 'immostreet'
		}) # immostreet

		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=m3v2&state=deleted',
			'robot': 'm3v2'
		}) # m3v2
		
		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=naef&state=deleted',
			'robot': 'naef'
		}) # naef
		
		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=newhome&state=deleted',
			'robot': 'newhome' 
		}) # newhome

		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=spg&state=deleted',
			'robot': 'spg'
		}) # spg

		reader.append({
			'start_url':'https://app.scrapinghub.com/api/jobs/list.json?' 
						+'project=219365&spider=tutti&state=deleted',
			'robot': 'tutti'
		}) # tutti
		
		for row in reader:

			yield scrapy.Request(
				row['start_url'], 
				self.parse, 
				meta={'dado': row, 'count': 1}, 
				headers={'Authorization': auth}
				)

	#Pagina com a lista de links
	def parse(self, response):
		logging.warning("Iniciando url: " + response.url)
		response_json = json.loads(response.text)
		log = ''
		logs = ['','']

		scrapy_logs = []
		for r_json in response_json['jobs']:
			scrapy_logs.append(r_json)

		logs[0] = scrapy_logs[-1]
		logs[1] = scrapy_logs[-2]

		for r_json in logs:
			if r_json['errors_count'] > 0:
				log += 'Spider: ' + r_json['spider'] + '\n'
				log += 'Id: ' + r_json['id'] + '\n'
				log += 'Items scraped: ' + str(r_json['items_scraped']) + '\n'
				log += 'Errors: ' + str(r_json['errors_count']) + '\n'
				log += 'Started time: ' + r_json['started_time'] + '\n'
				log += 'Finished time: ' + r_json['updated_time'] + '\n'
				log += '\n'
		
		if log is not '':
			print(log)
			
			msg = MIMEText(log, 'plain')
			msg['Subject'] = '(Error) ' + r_json['spider'] + " - Error Robot log"
			me ='robot@1contact.ch'
			msg['To'] = 'vitor.hugo@ce7p.com'

			try:
				conn = SMTP('ce7p.com')
				#conn.set_debuglevel(True)
				conn.login('sender@ce7p.com','1ContactSender')
				try:
					conn.sendmail('robot@1contact.ch', ['vitor.hugo@ce7p.com'], msg.as_string())
				finally:
					conn.close()
			except:
				print('erro ao enviar email')
			
		else:
			print('Não existe erros para ' + response.meta['dado']['robot'])
		
