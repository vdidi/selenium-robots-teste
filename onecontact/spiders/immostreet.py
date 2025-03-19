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

class ImmostreetSpider(scrapy.Spider):
	name = "immostreet"
	download_delay = 5

	def __init__(self, max_page=0, *args, **kwargs):
		super(ImmostreetSpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	#Dependendo do robô pode ser feito de modo implicito
	def start_requests(self):
		reader = []

		#Genève

		#rent
		reader.append({
			'start_url':'https://www.immostreet.ch/fr/louer/appartement/canton-geneve/', 
			'state': 'Genève', 
			'type_of_transaction': 'rent', 
			'nature_of_property':'residential', 
			'type_of_property':'apartment'
			})
		reader.append({
			'start_url':'https://www.immostreet.ch/fr/louer/maison/canton-geneve/', 
			'state': 'Genève', 
			'type_of_transaction': 'rent', 
			'nature_of_property':'residential', 
			'type_of_property':'house'
			})
		reader.append({
			'start_url':'https://www.immostreet.ch/fr/louer/commerce-industrie/canton-geneve/', 
			'state': 'Genève', 
			'type_of_transaction': 'rent', 
			'nature_of_property':'commercial', 
			'type_of_property':''
			})
		
		#sell
		reader.append({
			'start_url':'https://www.immostreet.ch/fr/acheter/appartement/canton-geneve/', 
			'state': 'Genève', 
			'type_of_transaction': 'sell', 
			'nature_of_property':'residential', 
			'type_of_property':'apartment'
			})
		reader.append({
			'start_url':'https://www.immostreet.ch/fr/acheter/maison/canton-geneve/', 
			'state': 'Genève', 
			'type_of_transaction': 'sell', 
			'nature_of_property':'residential', 
			'type_of_property':'house'
			})
		reader.append({
			'start_url':'https://www.immostreet.ch/fr/acheter/commerce-industrie/canton-geneve/', 
			'state': 'Genève', 
			'type_of_transaction': 'sell', 
			'nature_of_property':'commercial', 
			'type_of_property':''
			})

		for row in reader:
			yield scrapy.Request(
				row['start_url'], 
				self.parse,
				errback=self.errback_httpbin, 
				meta={'dado': row, 'count': 1}
				)

	#Pagina com a lista de links
	def parse(self, response):
		logging.warning("Iniciando url: " + response.url)
		anuncios_url = response.xpath('//article[contains(@class,"results-item")]')

		for anuncio_url in anuncios_url:
			url = response.urljoin(anuncio_url.xpath('.//a[contains(@class,"link")]/@href').extract_first())
			cod = re.search(r'/(\d+)\?', url).group()
			cod = re.sub(r"\D+", "", cod)
   
			r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod + '/' + self.name)

			logging.warning("resposta requisicao cod: " + cod)
			

			if r_cod.status_code == 200 and int(r_cod.text) == 0:
				logging.warning('anuncio não existe no servidor então capturar!')
				yield scrapy.Request(
					url, 
					callback=self.parse_contents,
					errback=self.errback_httpbin, 
					meta={'dado': response.meta['dado']}
					)
		#	-------------------------------------------------------------------------------------------------
		#	|	PAGINACAO
		#	|	Paginacao condicional se especificado o valor maximo de página em 'max_page' argumento
		#	-------------------------------------------------------------------------------------------------
		next_page = response.xpath('//div[contains(@class,"pagination")]/nav[contains(@class,"items -direction")]/a[contains(@class,"next")]/@href').extract_first()

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
					meta={'dado': response.meta['dado'], 
					'count': (count+1)}
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

		anuncio['cod_anuncio'] = response.xpath('//ul[contains(@class,"action -detail")]//span[contains(@class,"code")]/span[contains(@class,"value")]/text()').extract_first()

		anuncio['description'] = response.xpath('//div[contains(@id,"detail-description")]/div[contains(@class,"description")]').xpath('normalize-space()').extract_first()
		
		if anuncio['description'] is not None: 
			if len(anuncio['description']) < 2:
				anuncio['description'] = ''

		areaDetails = response.xpath('//div[contains(@class,"detail-attributes")]/ul[contains(@class,"properties detail-properties")]')
		
		anuncio['rooms_qty'] = areaDetails.xpath('//li[contains(@class,"item")][./span[contains(@class,"key")][re:test(.,"[pP]i.ces")]]/span[contains(@class,"value")]/text()').extract_first()
		anuncio['floor_qty'] = None
		anuncio['surface_inner'] = areaDetails.xpath('//li[contains(@class,"item")][./span[contains(@class,"key")][re:test(.,"[sS]urface [hH]abitable")]]/span[contains(@class,"value")]/text()').extract_first()
		anuncio['available_date'] = areaDetails.xpath('//li[contains(@class,"item")][./span[contains(@class,"key")][re:test(.,"Disponible d.s")]]/span[contains(@class,"value")]/text()').extract_first()
	
		anuncio['title'] = response.xpath('//div[contains(@id,"detail-description")]/h2/text()').extract_first();
		
		areaPrice = response.xpath('//div[contains(@class,"detail-prices")][./span[contains(@class,"label")][contains(.,"Prix")]]')
		anuncio['price'] = areaPrice.xpath('.//li[./span[1][contains(@class,"key")][contains(.,"Loyer net")]]/span[2]/text()').extract_first()
		anuncio['charges'] = areaPrice.xpath('.//li[./span[1][contains(@class,"key")][re:test(.,"[cC]harges")]]/span[2]/text()').extract_first()

		if anuncio['price'] is None:
			anuncio['price'] = areaPrice.xpath('.//li[./span[1][contains(@class,"key")][contains(.,"brut")]]/span[2]/text()').extract_first()

		if anuncio['price'] is None:
			anuncio['price'] = areaPrice.xpath('//span[contains(@class,"value -wide")]').xpath('normalize-space()').extract_first()

		imgs = response.xpath('//section[contains(@class,"content")]/header/div[contains(@class,"detail-gallery")]//img/@data-image-src').extract()
		url_imgs = []
		if len(imgs):
			for img in imgs:
				#url_imgs.append(response.urljoin(img))
				url_imgs.append(img)

		anuncio['url_imgs'] = url_imgs

		anuncio['address'] = response.xpath('//div[contains(@class,"header")]//h1[contains(@class,"title")]').xpath('normalize-space()').extract_first()
		
		features_final = []
		features = response.xpath('//div[contains(@class,"detail-features")]//ul/li[contains(@class,"item")]').xpath('normalize-space()').extract()
		
		for feature in features:
			if len(feature) > 0:
				features_final.append(feature)

		anuncio['features'] = []
		if features_final is not None and len(features_final) > 0:
			anuncio['features'] = features_final

		areaAnnouncer = response.xpath('//div[contains(@class,"detail-agency detail")]')

		anuncio['announcer'] = areaAnnouncer.xpath('//span[contains(@class,"company")]/text()').extract_first()
		anuncio['announcer_site'] = None 

		anuncio['contact_phone'] = response.xpath('//div[contains(@class,"detail-agency")]/div[contains(@data-track-number,"agency_phone")]//a[re:test(@href,"^(tel)")]/@href').extract()
		anuncio['contact_name'] = None

		areaVisit = response.xpath('//div[contains(@class,"detail-visit")]')

		anuncio['viewing_phone_number'] = areaVisit.xpath('.//div/a[re:test(@href,"^(tel)")]').xpath('normalize-space()').extract()
		anuncio['viewing_desc'] = areaVisit.xpath('.//p[contains(@class,"name")]/text()').extract_first()

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
