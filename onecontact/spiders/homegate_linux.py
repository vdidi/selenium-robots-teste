# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests
import time

import random


#erros libs
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from scrapy.selector import Selector
from fake_useragent import UserAgent

USER_AGENTS  = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
	"Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
	"Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
]


# Other reusable constants or configuration settings
HEADLESS_OPTIONS = ["--disable-gpu", "--disable-dev-shm-usage","--window-size=1920,1080","--disable-search-engine-choice-screen"]

class UserAgentManager:
    @staticmethod
    def get_random_user_agent():
        return UserAgent().random

def fetch_html_selenium(url):
    driver = setup_selenium()
    try:
        driver.get(url)
        
        # Add random delays to mimic human behavior
        time.sleep(1)  # Adjust this to simulate time for user to read or interact
        driver.maximize_window()
        

        # Try to find and click the 'Accept Cookies' button
        # click_accept_cookies(driver)

        # Add more realistic actions like scrolling
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(random.uniform(1.1, 1.8))  # Simulate time taken to scroll and read
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/1.2);")
        time.sleep(random.uniform(1.1, 1.8))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/1);")
        time.sleep(random.uniform(1.1, 2.1))
        html = driver.page_source
        return html
    finally:
        driver.quit()

def setup_selenium():
	options = Options()

	# Randomly select a user agent from the imported list
	user_agent = random.choice(USER_AGENTS)
	options.add_argument(f"user-agent={user_agent}")
	options.add_argument("--headless=new")

	# Add other options
	for option in HEADLESS_OPTIONS:
		options.add_argument(option)

	# Specify the path to the ChromeDriver
	# service = Service(r"./chromedriver-win64/chromedriver.exe")  
	        # Configurar opções do Chrome com User Agent aleatório
	chrome_options = webdriver.ChromeOptions()
	user_agent = UserAgentManager.get_random_user_agent()
	chrome_options.add_argument(f'user-agent={user_agent}')
	chrome_options.add_argument("--headless")
	chrome_options.add_argument("--no-sandbox")
	chrome_options.add_argument("--disable-dev-shm-usage")
	chrome_options.binary_location = "/usr/bin/chromium-browser"
	# Adicionar outras opções úteis
	chrome_options.add_argument('--disable-blink-features=AutomationControlled')
	chrome_options.add_argument('--disable-extensions')
	chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
	chrome_options.add_experimental_option('useAutomationExtension', False)
        
	# Initialize the WebDriver
	service = Service(executable_path="/usr/local/bin/chromedriver")
	driver = webdriver.Chrome(options=chrome_options, service=service)
	return driver

class HomegateSpider(scrapy.Spider):
	name = "homegate_linux"
	handle_httpstatus_list = [404, 400, 401, 403]
	#start_urls = ['https://www.homegate.ch/fr']
	download_delay = 5
	max_page = 1

	def __init__(self, max_page=1, *args, **kwargs):
		super(HomegateSpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	#Dependendo do robô pode ser feito de modo implicito
	def start_requests(self):
		#analisar se nao vale a pena carregar tudo na variavel e fechar arquivo e depois ir nos csvs
		#with open('homegate_start_url.csv') as f:
		#	reader = csv.DictReader(f)
		reader = []

		#Genève
		reader.append({
			'start_url':'https://www.homegate.ch/louer/appartement/lieu-geneve/liste-annonces?o=dateCreated-desc', 
			'state': 'Genève', 
			'type_of_transaction': 'rent', 
			'nature_of_property':'residential',
			'type_of_property': 'appartement'
			})
		#Genève
		# reader.append({
		# 	'start_url':'https://www.homegate.ch/louer/maison/lieu-geneve/liste-annonces?o=dateCreated-desc', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'residential',
		# 	'type_of_property': 'house'
		# 	})
		# reader.append({
		# 	'start_url':'https://www.homegate.ch/louer/depot/liste-annonces?loc=Gen%C3%A8ve%20%5BCanton%5D', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'commercial',
		# 	'type_of_property': ''
		# 	})
		# reader.append({
		# 	'start_url':'https://www.homegate.ch/louer/place-de-parc-garage/liste-annonces?loc=Gen%C3%A8ve%20%5BCanton%5D', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'commercial',
		# 	'type_of_property': ''
		# 	})
		# reader.append({
		# 	'start_url':'https://www.homegate.ch/louer/bureau/liste-annonces?loc=Gen%C3%A8ve%20%5BCanton%5D', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'commercial',
		# 	'type_of_property': ''
		# 	})

		#sell
		# reader.append({
		# 	'start_url':'https://www.homegate.ch/acheter/appartement/lieu-geneve/liste-annonces?o=dateCreated-desc', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'sell', 
		# 	'nature_of_property':'residential',
		# 	'type_of_property': 'appartement'
		# 	})
		# reader.append({
		# 	'start_url':'https://www.homegate.ch/acheter/maison/lieu-geneve/liste-annonces?o=dateCreated-desc', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'sell', 
		# 	'nature_of_property':'residential',
		# 	'type_of_property': 'house'
		# 	})
		for row in reader:
			html = fetch_html_selenium(row['start_url'])
			time.sleep(1)  # Adjust this to simulate time for user to read or interact
			response = Selector(text=html)
			yield scrapy.Request(
				'https://www.scrapethissite.com/pages/', 
				callback=self.parse,
				errback=self.errback_httpbin,
				meta={'dado': row, 'count': 1, 'response': response},
				headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
			)
	
		# finally:	
		# 		driver.quit()
		
		# for row in reader:
		# 	yield scrapy.Selector(
		# 		row['start_url'], 
		# 		self.parse,
		# 		errback=self.errback_httpbin,
		# 		meta={'dado': row, 'count': 1},
		# 		headers={
		# 			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
		# 			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
		# 			"Accept-Language": "en-US,en;q=0.5",
		# 			"Accept-Encoding": "gzip, deflate",
		# 			"Connection": "keep-alive",
		# 			"Upgrade-Insecure-Requests": "1",
		# 			"Sec-Fetch-Dest": "document",
		# 			"Sec-Fetch-Mode": "navigate",
		# 			"Sec-Fetch-Site": "none",
		# 			"Sec-Fetch-User": "?1",
		# 			"Cache-Control": "max-age=0",
		# 		}
		# 	)

	#Pagina com a lista de links e html
	def parse(self, response):
		# logging.warning("Iniciando url: " + response.url) | logging.warning("coletando html do anuncio: " + response.html)
		anuncios_url = response.meta['response'].xpath('//div[contains(@data-test, "result-list-item")]//a')

		# Continuar daqui
		for anuncio_url in anuncios_url:
			time.sleep(1)  # Adjust this to simulate time for user to read or interact
			endpoint = anuncio_url.xpath('@href').extract_first()
			url = "https://www.homegate.ch" + endpoint
			html_do_anuncio = fetch_html_selenium(url)
			response_anuncio = Selector(text=html_do_anuncio)
			cod = re.sub(r'.*\/','', url)
			r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod + '/' + self.name)
			time.sleep(1)  # Adjust this to simulate time for user to read or interact
   
			logging.warning("resposta requisicao cod: " + cod)

			if r_cod.status_code == 200 and int(r_cod.text) == 0:
				logging.warning('anuncio não existe no servidor então capturar!')
				anuncio = OnecontactItem()
				anuncio['name'] = "homegate"
				anuncio['country'] = 'Switzerland'
				anuncio['url_anuncio'] = url

				#dados inseridos do csv
				anuncio['type_of_transaction'] = response.meta['dado']['type_of_transaction']
				anuncio['state'] = 'Genève',
				anuncio['nature_of_property'] = response.meta['dado']['nature_of_property']   # residential | commercial
				anuncio['type_of_property'] = response.meta['dado']['type_of_property']

				anuncio['cod_anuncio'] = re.sub(r'.*\/','', url)
				anuncio['description'] = response_anuncio.xpath('//div[contains(@class,"Description_description")]').xpath('normalize-space()').extract_first()
				
				if anuncio['description'] is not None and len(anuncio['description']) < 2:
					anuncio['description'] = ''

				#anuncio['type_of_property'] = response_anuncio.xpath("//dd[preceding-sibling::dt[contains(.,'Type:')]][1]/text()").extract_first()
				
				anuncio['rooms_qty'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[nN]ombre')][re:test(.,'[pP]i.ce')]][1]/text()").extract_first()
				anuncio['floor_qty'] = None
				anuncio['surface_inner'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[sS]urface')]][1]/text()").extract_first()
				anuncio['available_date'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[dD]isponibl.')]][1]/text()").re_first('\d.*')
			
				anuncio['title'] = response_anuncio.xpath('//div[contains(@class,"Description_description")]/h1/text()').extract_first()
				anuncio['price'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[lL]oyer')]][1]").xpath('normalize-space()').re_first('\d.*')
				anuncio['charges'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[cC]harges')]][1]").xpath('normalize-space()').re_first('\d.*')

				if anuncio['charges'] is None:
					anuncio['charges'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[fF]rais annexes')]][1]").xpath('normalize-space()').re_first('\d.*')

				if anuncio['price'] is None:
					anuncio['price'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[pP]rix')]][1]").xpath('normalize-space()').re_first('\d.*')
				if anuncio['price'] is None:
					response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[mM]ontant net')]][1]").xpath('normalize-space()').re_first('\d.*')

				anuncio['url_imgs'] = []

				anuncio['address'] = response_anuncio.xpath('//div[contains(@class,"AddressDetails")]/address').xpath('normalize-space()').extract_first()

				anuncio['features'] = response_anuncio.xpath('//ul[contains(@class,"FeaturesFurn")]/li').xpath('normalize-space()').extract()

				#anuncio['contact_phone'] = list(set(response_anuncio.xpath('//div[contains(@class, "ListerContactPhon")]//a[contains(@href, "tel")]/@href').extract()))
				anuncio['contact_phone'] = list(set(response_anuncio.xpath('//div[./p[contains(@class, "ListerContactPhon")]]/div//a[contains(@href, "tel")]/@href').extract()))
				anuncio['contact_name'] = None

				anuncio['announcer'] = 'homegate'
				anuncio['announcer_site'] = 'https://www.homegate.ch'

				anuncio['viewing_phone_number'] = []
				anuncio['viewing_desc'] = None

				#campos qty number
				anuncio['bedrooms_qty'] = None
				anuncio['toilets_qty'] = None
				anuncio['bathrooms_qty'] = None
				anuncio['surface_outer'] = None

				#tipos: rent | owner | professional
				anuncio['type_of_announcer'] = None

				#--------------------------------------------
				#address - string campo
				#--------------------------------------------
				anuncio['street_number'] = None
				anuncio['route'] = None
				anuncio['complement'] =  None
				anuncio['neighborhood'] = None
				anuncio['city'] = None
				anuncio['postal_code'] = None

				yield anuncio
				# yield scrapy.Request(
				# 	'https://www.scrapethissite.com/pages/', 
				# 	callback=self.parse_contents,
				# 	errback=self.errback_httpbin,
				# 	meta={'dado': response.meta['dado'], 'response': response_anuncio, 'url': url},
				# 	headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
				# )
		#	-------------------------------------------------------------------------------------------------
		#	|	PAGINACAO
		#	|	Paginacao condicional se especificado o valor maximo de página em 'max_page' argumento
		#	-------------------------------------------------------------------------------------------------
		
		next_page = response.meta['response'].xpath('//div[contains(@class, "PaginationSelector")]/nav//a[contains(@class, "nextPreviousArrow")][./svg[re:test(@style, ".*rotate.*?180deg")]]/@href').extract_first();

		count = int(response.meta['count'])
		
		# Verifica se existe o objeto next_page
		if next_page is not None:
			print("count " + str(response.meta['count'] + 1))
			if (count < self.max_page and self.max_page !=0) or (self.max_page == 0):
				print("Indo para pagina: " + str(count + 1))
				next_page = response.urljoin(next_page)
				url = "https://www.homegate.ch" + next_page
				html_do_anuncio = fetch_html_selenium(url)
				response_anuncio = Selector(text=html_do_anuncio)
				anuncio = OnecontactItem()
				anuncio['name'] = "homegate"
				anuncio['country'] = 'Switzerland'
				anuncio['url_anuncio'] = url

				#dados inseridos do csv
				anuncio['type_of_transaction'] = response.meta['dado']['type_of_transaction']
				anuncio['state'] = "Genève",
				anuncio['nature_of_property'] = response.meta['dado']['nature_of_property']   # residential | commercial
				anuncio['type_of_property'] = response.meta['dado']['type_of_property']

				anuncio['cod_anuncio'] = re.sub(r'.*\/','', url)
				anuncio['description'] = response_anuncio.xpath('//div[contains(@class,"Description_description")]').xpath('normalize-space()').extract_first()
				
				if anuncio['description'] is not None and len(anuncio['description']) < 2:
					anuncio['description'] = ''

				#anuncio['type_of_property'] = response_anuncio.xpath("//dd[preceding-sibling::dt[contains(.,'Type:')]][1]/text()").extract_first()
				
				anuncio['rooms_qty'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[nN]ombre')][re:test(.,'[pP]i.ce')]][1]/text()").extract_first()
				anuncio['floor_qty'] = None
				anuncio['surface_inner'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[sS]urface')]][1]/text()").extract_first()
				anuncio['available_date'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[dD]isponibl.')]][1]/text()").re_first('\d.*')
			
				anuncio['title'] = response_anuncio.xpath('//div[contains(@class,"Description_description")]/h1/text()').extract_first()
				anuncio['price'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[lL]oyer')]][1]").xpath('normalize-space()').re_first('\d.*')
				anuncio['charges'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[cC]harges')]][1]").xpath('normalize-space()').re_first('\d.*')

				if anuncio['charges'] is None:
					anuncio['charges'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[fF]rais annexes')]][1]").xpath('normalize-space()').re_first('\d.*')

				if anuncio['price'] is None:
					anuncio['price'] = response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[pP]rix')]][1]").xpath('normalize-space()').re_first('\d.*')
				if anuncio['price'] is None:
					response_anuncio.xpath("//dd[preceding-sibling::dt[re:test(.,'[mM]ontant net')]][1]").xpath('normalize-space()').re_first('\d.*')

				anuncio['url_imgs'] = []

				anuncio['address'] = response_anuncio.xpath('//div[contains(@class,"AddressDetails")]/address').xpath('normalize-space()').extract_first()

				anuncio['features'] = response_anuncio.xpath('//ul[contains(@class,"FeaturesFurn")]/li').xpath('normalize-space()').extract()

				#anuncio['contact_phone'] = list(set(response_anuncio.xpath('//div[contains(@class, "ListerContactPhon")]//a[contains(@href, "tel")]/@href').extract()))
				anuncio['contact_phone'] = list(set(response_anuncio.xpath('//div[./p[contains(@class, "ListerContactPhon")]]/div//a[contains(@href, "tel")]/@href').extract()))
				anuncio['contact_name'] = None

				anuncio['announcer'] = 'homegate'
				anuncio['announcer_site'] = 'https://www.homegate.ch'

				anuncio['viewing_phone_number'] = []
				anuncio['viewing_desc'] = None

				#campos qty number
				anuncio['bedrooms_qty'] = None
				anuncio['toilets_qty'] = None
				anuncio['bathrooms_qty'] = None
				anuncio['surface_outer'] = None

				#tipos: rent | owner | professional
				anuncio['type_of_announcer'] = None

				#--------------------------------------------
				#address - string campo
				#--------------------------------------------
				anuncio['street_number'] = None
				anuncio['route'] = None
				anuncio['complement'] =  None
				anuncio['neighborhood'] = None
				anuncio['city'] = None
				anuncio['postal_code'] = None

				yield anuncio
			else:
				next_page = None

	# Pagina com todos campos que vao ser inseridos no robô
	def parse_contents(self, response):
		anuncio = OnecontactItem()
		anuncio['name'] = "homegate"
		anuncio['country'] = 'Switzerland'
		anuncio['url_anuncio'] = response.meta['url']

		#dados inseridos do csv
		anuncio['type_of_transaction'] = response.meta['dado']['type_of_transaction']
		anuncio['state'] = "Genève",
		anuncio['nature_of_property'] = response.meta['dado']['nature_of_property']   # residential | commercial
		anuncio['type_of_property'] = response.meta['dado']['type_of_property']

		anuncio['cod_anuncio'] = re.sub(r'.*\/','', response.meta['url'])
		anuncio['description'] = response.meta['response'].xpath('//div[contains(@class,"Description_description")]').xpath('normalize-space()').extract_first()
		
		if anuncio['description'] is not None and len(anuncio['description']) < 2:
			anuncio['description'] = ''

		#anuncio['type_of_property'] = response.meta['response'].xpath("//dd[preceding-sibling::dt[contains(.,'Type:')]][1]/text()").extract_first()
		
		anuncio['rooms_qty'] = response.meta['response'].xpath("//dd[preceding-sibling::dt[re:test(.,'[nN]ombre')][re:test(.,'[pP]i.ce')]][1]/text()").extract_first()
		anuncio['floor_qty'] = None
		anuncio['surface_inner'] = response.meta['response'].xpath("//dd[preceding-sibling::dt[re:test(.,'[sS]urface')]][1]/text()").extract_first()
		anuncio['available_date'] = response.meta['response'].xpath("//dd[preceding-sibling::dt[re:test(.,'[dD]isponibl.')]][1]/text()").re_first('\d.*')
	
		anuncio['title'] = response.meta['response'].xpath('//div[contains(@class,"Description_description")]/h1/text()').extract_first()
		anuncio['price'] = response.meta['response'].xpath("//dd[preceding-sibling::dt[re:test(.,'[lL]oyer')]][1]").xpath('normalize-space()').re_first('\d.*')
		anuncio['charges'] = response.meta['response'].xpath("//dd[preceding-sibling::dt[re:test(.,'[cC]harges')]][1]").xpath('normalize-space()').re_first('\d.*')

		if anuncio['charges'] is None:
			anuncio['charges'] = response.meta['response'].xpath("//dd[preceding-sibling::dt[re:test(.,'[fF]rais annexes')]][1]").xpath('normalize-space()').re_first('\d.*')

		if anuncio['price'] is None:
			anuncio['price'] = response.meta['response'].xpath("//dd[preceding-sibling::dt[re:test(.,'[pP]rix')]][1]").xpath('normalize-space()').re_first('\d.*')
		if anuncio['price'] is None:
			response.meta['response'].xpath("//dd[preceding-sibling::dt[re:test(.,'[mM]ontant net')]][1]").xpath('normalize-space()').re_first('\d.*')

		anuncio['url_imgs'] = []

		anuncio['address'] = response.meta['response'].xpath('//div[contains(@class,"AddressDetails")]/address').xpath('normalize-space()').extract_first()

		anuncio['features'] = response.meta['response'].xpath('//ul[contains(@class,"FeaturesFurn")]/li').xpath('normalize-space()').extract()

		#anuncio['contact_phone'] = list(set(response.meta['response'].xpath('//div[contains(@class, "ListerContactPhon")]//a[contains(@href, "tel")]/@href').extract()))
		anuncio['contact_phone'] = list(set(response.meta['response'].xpath('//div[./p[contains(@class, "ListerContactPhon")]]/div//a[contains(@href, "tel")]/@href').extract()))
		anuncio['contact_name'] = None

		anuncio['announcer'] = 'homegate'
		anuncio['announcer_site'] = 'https://www.homegate.ch'

		anuncio['viewing_phone_number'] = []
		anuncio['viewing_desc'] = None

	    #campos qty number
		anuncio['bedrooms_qty'] = None
		anuncio['toilets_qty'] = None
		anuncio['bathrooms_qty'] = None
		anuncio['surface_outer'] = None

	    #tipos: rent | owner | professional
		anuncio['type_of_announcer'] = None

		#--------------------------------------------
	    #address - string campo
	    #--------------------------------------------
		anuncio['street_number'] = None
		anuncio['route'] = None
		anuncio['complement'] =  None
		anuncio['neighborhood'] = None
		anuncio['city'] = None
		anuncio['postal_code'] = None

		yield anuncio

	def errback_httpbin(self, failure):
		 # log all failures
		self.logger.error(repr(failure))

		# in case you want to do something special for some errors,
		# you may need the failure's type:

		if failure.check(HttpError):
			# these exceptions come from HttpError spider middleware
			# you can get the non-200 response
			response = failure.value.response
			self.logger.error('HttpError on %s', response.url)

		elif failure.check(DNSLookupError):
			# this is the original request
			request = failure.request
			self.logger.error('DNSLookupError on %s', request.url)

		elif failure.check(TimeoutError, TCPTimedOutError):
			request = failure.request
			self.logger.error('TimeoutError on %s', request.url)