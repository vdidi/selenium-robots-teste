# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests
from datetime import datetime, timedelta
import json

#erros libs
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class AnibisSpider(scrapy.Spider):
	name = "anibis"
	download_delay = 5
	concurrent_requests = 1
 
	def __init__(self, max_page=2, *args, **kwargs):
		super(AnibisSpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	#Dependendo do robô pode ser feito de modo implicito
	def start_requests(self):
		
		reader = []
		#Genève

		#sell
		reader.append({
			'start_url':'https://www.anibis.ch/fr/q/immobilier-geneve-apartment-rent/Ak8CqcmVhbEVzdGF0ZZSSkqtsaXN0aW5nVHlwZalhcGFydG1lbnSSqXByaWNlVHlwZaRSRU5UwMCRk6hsb2NhdGlvbq9nZW8tY2l0eS1nZW5ldmXA?sorting=newest&page=1', 
			'state': 'Genève', 
			'type_of_transaction': 'rent', 
			'nature_of_property':'residential', 
			'type_of_property':'appartement'
			}) #Appartament
		# reader.append({
		# 	'start_url':'http://www.anibis.ch/fr/immobilier-immobilier-locations--410/advertlist.aspx?sct=ge&aidl=867&action=filter', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'residential', 
		# 	'type_of_property':'house'
		# 	}) #Maison
		# reader.append({
		# 	'start_url':'http://www.anibis.ch/fr/immobilier-immobilier-locations--410/advertlist.aspx?sct=ge&aidl=869&action=filter', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'commercial', 
		# 	'type_of_property':''
		# 	}) #Commercial
		# reader.append({
		# 	'start_url':'http://www.anibis.ch/fr/immobilier-immobilier-locations--410/advertlist.aspx?sct=ge&aidl=869&action=filter', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'commercial', 
		# 	'type_of_property':'parking'
		# 	}) #Commercial

		# #sell
		# reader.append({
		# 	'start_url':'http://www.anibis.ch/fr/immobilier-immobilier-ventes--438/advertlist.aspx?sct=ge&aidl=866&action=filter', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'sell', 
		# 	'nature_of_property':'residential', 
		# 	'type_of_property':'appartement'
		# 	}) #Appartament
		# reader.append({
		# 	'start_url':'http://www.anibis.ch/fr/immobilier-immobilier-ventes--438/advertlist.aspx?sct=ge&aidl=867&action=filter', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'sell', 
		# 	'nature_of_property':'residential', 
		# 	'type_of_property':'house'
		# 	}) #Maison
		# reader.append({
		# 	'start_url':'http://www.anibis.ch/fr/immobilier-immobilier-ventes--438/advertlist.aspx?sct=ge&aidl=869&action=filter', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'sell', 
		# 	'nature_of_property':'commercial', 
		# 	'type_of_property':''
		# 	}) #Commercial

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
	
	# def parse_token (self, response):
	# 	data = response.xpath("//script[contains(text(), 'searchToken')]/text()").extract_first()
	# 	json_data = json.loads(data)
	# 	try:
	# 		token = json_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['searchListingsByQuery']['searchToken']
	# 		url = 'https://www.anibis.ch/fr/q/immobilier-geneve-apartment-rent/Ak8CqcmVhbEVzdGF0ZZSSkqtsaXN0aW5nVHlwZalhcGFydG1lbnSSqXByaWNlVHlwZaRSRU5UwMCRk6hsb2NhdGlvbq9nZW8tY2l0eS1nZW5ldmXA?sorting=newest&page=1'
	# 		yield scrapy.Request(
	# 				url, 
	# 				self.parse, 
	# 				errback=self.errback_httpbin,
	# 				meta={'dado': response.meta['dado']},
	# 				headers={
	# 					"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
	# 					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
	# 					"Accept-Language": "en-US,en;q=0.5",
	# 					"Accept-Encoding": "gzip, deflate",
	# 					"Connection": "keep-alive",
	# 					"Upgrade-Insecure-Requests": "1",
	# 					"Sec-Fetch-Dest": "document",
	# 					"Sec-Fetch-Mode": "navigate",
	# 					"Sec-Fetch-Site": "none",
	# 					"Sec-Fetch-User": "?1",
	# 					"Cache-Control": "max-age=0",
	# 				}
	# 			)
	# 		total_pages_number = 0
	# 		pages = response.xpath('//nav[contains(@class, "MuiPagination-root MuiPagination-text")]//ul//li/button[contains(@aria-label, "Go to page")]/text()').extract()
	# 		for page in pages:
	# 			total_pages_number = page

	# 		for page_number in range(total_pages_number):
	# 			url = 'https://www.anibis.ch/fr/q/immobilier-geneve-apartment-rent/Ak8CqcmVhbEVzdGF0ZZSSkqtsaXN0aW5nVHlwZalhcGFydG1lbnSSqXByaWNlVHlwZaRSRU5UwMCRk6hsb2NhdGlvbq9nZW8tY2l0eS1nZW5ldmXA?sorting=newest&page=' + page_number
	# 			yield scrapy.Request(
	# 					url, 
	# 					self.parse, 
	# 					errback=self.errback_httpbin,
	# 					meta={'dado': response.meta['dado']},
	# 					headers={
	# 						"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
	# 						"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
	# 						"Accept-Language": "en-US,en;q=0.5",
	# 						"Accept-Encoding": "gzip, deflate",
	# 						"Connection": "keep-alive",
	# 						"Upgrade-Insecure-Requests": "1",
	# 						"Sec-Fetch-Dest": "document",
	# 						"Sec-Fetch-Mode": "navigate",
	# 						"Sec-Fetch-Site": "none",
	# 						"Sec-Fetch-User": "?1",
	# 						"Cache-Control": "max-age=0",
	# 					}
	# 				)
	# 	except Exception as e:
	# 		self.logger.error('Erro ao buscar token')
	# 		self.logger.error(e)

	#Pagina com a lista de links
	def parse(self, response):
		logging.warning("Iniciando url: " + response.url)
		anuncios_url = response.xpath('//*[@id="pageContainer"]/div[2]/div/div[1]/div/div/div[2]/div[2]/div[1]/div[4]/div')
		for anuncio_url in anuncios_url:
			url = anuncio_url.xpath("./div/a/@href").extract_first()
			if url is None:
				continue
			url = response.urljoin(anuncio_url.xpath("./div/a/@href").extract_first())
			
			cod = re.sub(r'.*\/','', url)
			
			try:
				r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod + '/' + self.name)
				logging.warning("Checando se anuncio ja existe.")
				logging.warning("resposta requisicao cod: " + cod)
				if r_cod.status_code == 200 and int(r_cod.text) == 0 :
					logging.warning("Anuncio nao existe no servidor entao ir capturar!")
					
					yield scrapy.Request(
						url, 
						callback=self.parse_contents,
						errback=self.errback_httpbin,
						meta={'dado': response.meta['dado']},
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
				else:
					logging.warning("Anúncio ja existe!")
			except Exception as e:
				logging.warning("Ocorreu um erro ")
				logging.warning(type(e))
				logging.warning(e.args)
				logging.warning(e)
    
		#TODO ajustar paginação
		pages = response.xpath('//nav[contains(@class, "MuiPagination-root MuiPagination-text")]//ul//li/button[contains(@aria-label, "Go to page")]/text()').extract()
		count = int(response.meta['count'])
		total_pages_number = 1
		
		for page in pages:
			total_pages_number = page

		total_pages_number = int(total_pages_number)
		for page_number in range(total_pages_number):
			# token = json_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['searchListingsByQuery']['searchToken']
			if (count < self.max_page and self.max_page !=0) or (self.max_page == 0):
				url = 'https://www.anibis.ch/fr/q/immobilier-geneve-apartment-rent/Ak8CqcmVhbEVzdGF0ZZSSkqtsaXN0aW5nVHlwZalhcGFydG1lbnSSqXByaWNlVHlwZaRSRU5UwMCRk6hsb2NhdGlvbq9nZW8tY2l0eS1nZW5ldmXA?sorting=newest&page=' + str(page_number + 1)
				# try:
				# 	r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod + '/' + self.name)
				# 	logging.warning("Checando se anuncio ja existe.")
				# 	logging.warning("resposta requisicao cod: " + cod)
				# 	if r_cod.status_code == 200 and int(r_cod.text) == 0 :
				# 		logging.warning("Anuncio nao existe no servidor entao ir capturar!")
						
				yield scrapy.Request(
					url, 
					callback=self.parse,
					errback=self.errback_httpbin,
					meta={'dado': response.meta['dado'], 'count': (count+1)},
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
			# 	else:
			# 		logging.warning("Anúncio ja existe!")
			# except Exception as e:
			# 	logging.warning("Ocorreu um erro ")
			# 	logging.warning(type(e))
			# 	logging.warning(e.args)
			# 	logging.warning(e)
    
			# url = 'https://www.anibis.ch/fr/q/immobilier-geneve-apartment-rent/Ak8CqcmVhbEVzdGF0ZZSSkqtsaXN0aW5nVHlwZalhcGFydG1lbnSSqXByaWNlVHlwZaRSRU5UwMCRk6hsb2NhdGlvbq9nZW8tY2l0eS1nZW5ldmXA?sorting=newest&page=' + response.meta['count']
			# yield scrapy.Request(
			# 		url, 
			# 		self.parse_contents, 
			# 		errback=self.errback_httpbin,
			# 		meta={'dado': response.meta['dado'], 'count': (count+1)},
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
		#	-------------------------------------------------------------------------------------------------
		#	|	PAGINACAO
		#	|	Paginacao condicional se especificado o valor maximo de página em 'max_page' argumento
		#	-------------------------------------------------------------------------------------------------
		#next_page = response.xpath('//a[contains(@id, "_lnkNext")][contains(@class,"right")]/@href').extract_first()
		# next_page = response.xpath('//div[contains(@direction, "min")]/a[contains(@aria-current, "page")][contains(@iconname, "Right")]/@href').extract_first()

		# count = int(response.meta['count'])
		
		# # Verifica se existe o objeto next_page
		# if next_page is not None:
		# 	print("count " + str(response.meta['count'] + 1))
		# 	if (count < self.max_page and self.max_page !=0) or (self.max_page == 0):
		# 		print("Indo para pagina: " + str(count + 1))
		# 		next_page = response.urljoin(next_page)
		# 		yield scrapy.Request(
		# 			next_page, 
		# 			callback=self.parse,
		# 			errback=self.errback_httpbin,
		# 			meta={'dado': response.meta['dado'], 'count': (count+1)}
		# 			)
		# 	else:
		# 		next_page = None

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

		# scope = response.xpath('//div[@itemscope][contains(@itemtype,"Product")]') MuiTypography-root
		anuncio['title'] = response.xpath('//h1[contains(@class, "MuiTypography-root")]/text()').extract_first()
		
		price = response.xpath('//h2[contains(@class, "MuiTypography-root")]/text()').extract_first()
		if price is not None:
			price = re.sub(r"\D+", "", price)

		anuncio['price'] = price

		# if scope is not None or len(scope) > 0:
		# 	anuncio['title'] = scope.xpath('//meta[contains(@itemprop, "name")]/@content').extract_first()
		# 	anuncio['price'] = scope.xpath('//meta[@itemprop="price"]/@content').extract_first()

		# else:
		# 	anuncio['title'] = response.xpath('//h1[contains(@class,"title")]').xpath('normalize-space()').extract_first()
		# 	#anuncio['price'] = response.xpath('//div[contains(@class,"price")]').xpath('normalize-space()').extract_first()
		# 	anuncio['price'] = response.xpath('//li[./div[re:test(.,"[lL]oyer")]]/div[2]/span/text()').re_first(r'\d.*')
		# TODO ajustar para pegar dinamicamente
		anuncio['type_of_property'] = response.meta['dado']['type_of_property']
		anuncio['rooms_qty'] = response.xpath("//dt[re:test(.,'[pP]i.ces')]//following-sibling::dd/span/text()").extract_first()
		anuncio['surface_inner'] = response.xpath("//dt[re:test(.,'[sS]urface')]//following-sibling::dd/span/text()").extract_first()
		anuncio['cod_anuncio'] = re.sub(r'.*\/','', response.url)
		desc = response.xpath('//div[contains(@class, "MuiBox-root mui-style-dzlblt")]/div/div/span[contains(@class, "MuiTypography-root MuiTypography-body1 ecqlgla1 mui-style-qwt0eq")]/text()').extract()
		if desc is not None:
			desc = ''.join(desc)
		anuncio['description'] = desc
  
		#scope address
		# scope_address = response.xpath('//div[@itemscope][contains(@itemtype,"Postal")]')
		# anuncio['address'] = scope_address.xpath('./meta[contains(@itemprop,"streetAddress")]/@content').extract_first()
		# locality = scope_address.xpath('./meta[contains(@itemprop,"addressLocality")]/@content').extract_first()
		address = response.xpath("//dt[re:test(.,'[aA]dresse')]//following-sibling::dd/span/text()").extract_first()
		if address is not None:
			address += ' Genève'
   
		anuncio['address'] = address
  
		#anuncio['url_imgs'] = response.xpath('//a[contains(@data-gallery-media-type,"image")]/@href').extract()
		anuncio['url_imgs'] = response.xpath("//button/div/img[contains(@alt, 'Image vide')]/@src").extract()
		
		anuncio['features'] = []

		anuncio['contact_phone'] = []
	
		anuncio['contact_name'] = None

		anuncio['announcer'] = None
		anuncio['announcer_site'] = None

		anuncio['viewing_phone_number'] = []
		anuncio['viewing_desc'] = None

		anuncio['charges'] = None
		anuncio['available_date'] = None

	    #campos qty number
		anuncio['bedrooms_qty'] = None
		anuncio['toilets_qty'] = None
		anuncio['bathrooms_qty'] = None
		anuncio['surface_outer'] = None

		anuncio['floor_qty'] = None

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
