# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests

#erros libs
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class HomegateSpider(scrapy.Spider):
	name = "homegate_old"
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
		reader.append({
			'start_url':'https://www.homegate.ch/louer/maison/lieu-geneve/liste-annonces?o=dateCreated-desc', 
			'state': 'Genève', 
			'type_of_transaction': 'rent', 
			'nature_of_property':'residential',
			'type_of_property': 'house'
			})
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
		reader.append({
			'start_url':'https://www.homegate.ch/acheter/appartement/lieu-geneve/liste-annonces?o=dateCreated-desc', 
			'state': 'Genève', 
			'type_of_transaction': 'sell', 
			'nature_of_property':'residential',
			'type_of_property': 'appartement'
			})
		reader.append({
			'start_url':'https://www.homegate.ch/acheter/maison/lieu-geneve/liste-annonces?o=dateCreated-desc', 
			'state': 'Genève', 
			'type_of_transaction': 'sell', 
			'nature_of_property':'residential',
			'type_of_property': 'house'
			})
		
		for row in reader:
			yield scrapy.Request(
				row['start_url'], 
				self.parse,
				errback=self.errback_httpbin,
				meta={'dado': row, 'count': 1},
				headers={
					"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
					"Accept-Language": "en-US,en;q=0.5",
					"Accept-Encoding": "gzip, deflate",
					"Connection": "keep-alive",
					"Upgrade-Insecure-Requests": "1",
					"Sec-Fetch-Dest": "document",
					"Sec-Fetch-Mode": "navigate",
					"Sec-Fetch-Site": "none",
					"Sec-Fetch-User": "?1",
					"Cache-Control": "max-age=0",
				}
			)

	#Pagina com a lista de links
	def parse(self, response):
		logging.warning("Iniciando url: " + response.url)
		anuncios_url = response.xpath('//div[contains(@data-test, "result-list-item")]//a')

		for anuncio_url in anuncios_url:
			url = response.urljoin(anuncio_url.xpath('@href').extract_first())
			
			cod = re.sub(r'.*\/','', url)
			r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod + '/' + self.name)

			logging.warning("resposta requisicao cod: " + cod)

			if r_cod.status_code == 200 and int(r_cod.text) == 0:
				logging.warning('anuncio não existe no servidor então capturar!')
				yield scrapy.Request(
					url, 
					callback=self.parse_contents,
					errback=self.errback_httpbin,
					meta={'dado': response.meta['dado']},
					headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
					)
		#	-------------------------------------------------------------------------------------------------
		#	|	PAGINACAO
		#	|	Paginacao condicional se especificado o valor maximo de página em 'max_page' argumento
		#	-------------------------------------------------------------------------------------------------
		#next_page = response.xpath('//a[re:test(@class,"next")]/@href').extract_first()
		next_page = response.xpath('//div[contains(@class, "PaginationSelector")]/nav//a[contains(@class, "nextPreviousArrow")][./svg[re:test(@style, ".*rotate.*?180deg")]]/@href').extract_first();

		count = int(response.meta['count'])
		
		# Verifica se existe o objeto next_page
		if next_page is not None:
			print("count " + str(response.meta['count'] + 1))
			if (count < self.max_page and self.max_page !=0) or (self.max_page == 0):
				print("Indo para pagina: " + str(count + 1))
				next_page = response.urljoin(next_page)
				yield scrapy.Request(
					next_page, 
					callback=self.parse, 
					errback=self.errback_httpbin,
					meta={'dado': response.meta['dado'], 'count': (count+1)}
					)
			else:
				next_page = None

	# Pagina com todos campos que vao ser inseridos no robô
	def parse_contents(self, response):

		anuncio = OnecontactItem()
		anuncio['name'] = self.name
		anuncio['country'] = 'Switzerland'
		anuncio['url_anuncio'] = response.url

		#dados inseridos do csv
		anuncio['type_of_transaction'] = response.meta['dado']['type_of_transaction']
		anuncio['state'] = response.meta['dado']['state']
		anuncio['nature_of_property'] = response.meta['dado']['nature_of_property']   # residential | commercial
		anuncio['type_of_property'] = response.meta['dado']['type_of_property']

		anuncio['cod_anuncio'] = re.sub(r'.*\/','', response.url)
		anuncio['description'] = response.xpath('//div[contains(@class,"Description_description")]').xpath('normalize-space()').extract_first()
		
		if anuncio['description'] is not None and len(anuncio['description']) < 2:
			anuncio['description'] = ''

		#anuncio['type_of_property'] = response.xpath("//dd[preceding-sibling::dt[contains(.,'Type:')]][1]/text()").extract_first()
		
		anuncio['rooms_qty'] = response.xpath("//dd[preceding-sibling::dt[re:test(.,'[nN]ombre')][re:test(.,'[pP]i.ce')]][1]/text()").extract_first()
		anuncio['floor_qty'] = None
		anuncio['surface_inner'] = response.xpath("//dd[preceding-sibling::dt[re:test(.,'[sS]urface')]][1]/text()").extract_first()
		anuncio['available_date'] = response.xpath("//dd[preceding-sibling::dt[re:test(.,'[dD]isponibl.')]][1]/text()").re_first('\d.*')
	
		anuncio['title'] = response.xpath('//div[contains(@class,"Description_description")]/h1/text()').extract_first()
		anuncio['price'] = response.xpath("//dd[preceding-sibling::dt[re:test(.,'[lL]oyer')]][1]").xpath('normalize-space()').re_first('\d.*')
		anuncio['charges'] = response.xpath("//dd[preceding-sibling::dt[re:test(.,'[cC]harges')]][1]").xpath('normalize-space()').re_first('\d.*')

		if anuncio['charges'] is None:
			anuncio['charges'] = response.xpath("//dd[preceding-sibling::dt[re:test(.,'[fF]rais annexes')]][1]").xpath('normalize-space()').re_first('\d.*')

		if anuncio['price'] is None:
			anuncio['price'] = response.xpath("//dd[preceding-sibling::dt[re:test(.,'[pP]rix')]][1]").xpath('normalize-space()').re_first('\d.*')
		if anuncio['price'] is None:
			response.xpath("//dd[preceding-sibling::dt[re:test(.,'[mM]ontant net')]][1]").xpath('normalize-space()').re_first('\d.*')

		anuncio['url_imgs'] = []

		anuncio['address'] = response.xpath('//div[contains(@class,"AddressDetails")]/address').xpath('normalize-space()').extract_first()

		anuncio['features'] = response.xpath('//ul[contains(@class,"FeaturesFurn")]/li').xpath('normalize-space()').extract()

		#anuncio['contact_phone'] = list(set(response.xpath('//div[contains(@class, "ListerContactPhon")]//a[contains(@href, "tel")]/@href').extract()))
		anuncio['contact_phone'] = list(set(response.xpath('//div[./p[contains(@class, "ListerContactPhon")]]/div//a[contains(@href, "tel")]/@href').extract()))
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
