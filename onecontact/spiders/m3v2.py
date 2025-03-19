# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests
import base64
from datetime import datetime, timedelta
import json
import math

#erros libs
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class M3V2Spider(scrapy.Spider):
	name = "m3v2"
	download_delay = 5

	def __init__(self, max_page=0, *args, **kwargs):
		super(M3V2Spider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	#Dependendo do robô pode ser feito de modo implicito
	def start_requests(self):
		
		reader = []

		#rent		
		reader.append({
			# 'start_url':'https://www.m-3.com/recherche/biens-a-louer/?object_category=appt&location=Genève&radius=4%2B&surface_min=0&surface_max=400%2B&rent_min=0&rent_max=12+000%2B&sort=&search=1', 
			'start_url': 'https://www.m-3.com/louer/appartement/page1/?location=&rooms_min=&rent_max=&ref=',
			'state': 'Genève', 
			'type_of_transaction': 'rent', 
			'nature_of_property':'residential', 
			'type_of_property':'apartment',
			'cat':'appt',
			'property_type': 'location'
			}) #Appartament
		
		reader.append({
			'start_url':'https://www.m-3.com/recherche/biens-a-louer/?object_category=house&location=Genève&radius=4%2B&surface_min=0&surface_max=400%2B&rent_min=0&rent_max=12+000%2B&sort=&search=1', 
			'state': 'Genève', 
			'type_of_transaction': 'rent', 
			'nature_of_property':'residential', 
			'type_of_property':'house',
			'cat' : 'house',
			'property_type': 'location'
			}) #Maison
		
		# reader.append({
		# 	'start_url':'https://www.m-3.com/recherche/biens-a-louer/?object_category=indus&location=Genève&radius=4%2B&surface_min=0&surface_max=400%2B&rent_min=0&rent_max=12+000%2B&sort=&search=1', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'commercial', 
		# 	'type_of_property':'',
		# 	'cat': 'indus',
		# 	'property_type': 'location'
		# 	}) #Commercial

		# reader.append({
		# 	'start_url':'https://www.m-3.com/recherche/biens-a-louer/?object_category=park&location=Genève&radius=4%2B&surface_min=0&surface_max=400%2B&rent_min=0&rent_max=12+000%2B&sort=&search=1', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'commercial', 
		# 	'type_of_property':'',
		# 	'cat': 'park',
		# 	'property_type': 'location'
		# 	}) #Commercial
		
		#sell
		reader.append({
			'start_url':'https://www.m-3.com/recherche/biens-a-vendre/?object_category=appt&location=Genève&radius=4%2B&surface_min=0&surface_max=400%2B&rent_min=0&rent_max=6+000+000%2B&rooms=&sort=&search=1', 
			'state': 'Genève', 
			'type_of_transaction': 'sell', 
			'nature_of_property':'residential', 
			'type_of_property':'apartment',
			'cat':'appt',
			'property_type': 'vente'
			}) #Appartament
		reader.append({
			'start_url':'https://www.m-3.com/recherche/biens-a-vendre/?object_category=house&location=Genève&radius=4%2B&surface_min=0&surface_max=400%2B&rent_min=0&rent_max=6+000+000%2B&sort=&search=1', 
			'state': 'Genève', 
			'type_of_transaction': 'sell', 
			'nature_of_property':'residential', 
			'type_of_property':'house',
			'cat' : 'house',
			'property_type': 'vente'
			}) #Maison
		# reader.append({
		# 	'start_url':'https://www.m-3.com/recherche/biens-a-vendre/?object_category=indus&location=Genève&radius=4%2B&surface_min=0&surface_max=400%2B&rent_min=0&rent_max=6+000+000%2B&sort=&search=1', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'sell', 
		# 	'nature_of_property':'commercial', 
		# 	'type_of_property':'',
		# 	'cat': 'indus',
		# 	'property_type': 'vente'
		# 	}) #Commercial
		# reader.append({
		# 	'start_url':'https://www.m-3.com/recherche/biens-a-vendre/?object_category=park&location=Genève&radius=4%2B&surface_min=0&surface_max=400%2B&rent_min=0&rent_max=6+000+000%2B&sort=&search=1', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'sell', 
		# 	'nature_of_property':'commercial', 
		# 	'type_of_property':'',
		# 	'cat': 'park',
		# 	'property_type': 'vente'
		# 	}) #Commercial
		
		for row in reader:
			yield scrapy.Request(
				row['start_url'], 
				self.parse,
				errback=self.errback_httpbin, 
				meta={'dado': row, 'count': 1},
				dont_filter=True
				)
	#TODO ajustar parse
	#Pagina com a lista de links
	def parse(self, response):
		pages = response.xpath('//h3[contains(@class, "block__title")]').xpath('normalize-space()').re_first(r'\d+')

		url = 'https://www.m-3.com/wp-admin/admin-ajax.php'

		data = {'action': 'property_listing',
				'property_type': response.meta['dado']['property_type'],
				'paged': 1,
				'object_category': response.meta['dado']['cat'],
				'location': 'Genève'
				}
		if response.meta['dado']['nature_of_property'] != 'commercial':
			data['radius']      = '4+'
			data['surface_min'] = 0
			data['surface_max'] = '400+'
			data['rent_min']    = 0
			data['rent_max']    = '12 000+'
			data['sort'] 		=  ''
			data['search']      = 1
   
		data = {'action': 'property_listing',
				'property_type': 'rent',
				'paged': 1,
				'object_category': 'appt',
				'location': 'Genève'
				}
  
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

		if pages is not None:

			pages = math.ceil(int(pages)/18)

			for p in range(pages):
				data['paged'] = p
				r = requests.get(url, params=data, headers={headers})

				if r.status_code == 200:
					objects = json.loads(r.text)
					for obj in objects['properties']:
						yield scrapy.Request(
							obj['link'], 
							callback=self.parse_contents,
							errback=self.errback_httpbin, 
							meta={'dado': response.meta['dado']} 
							)

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

		anuncio['title'] = response.xpath('//h2[contains(@class, "property-details-card__title")]/text()').extract_first()

		anuncio['price'] = response.xpath('//div[contains(@class, "h2 property-details-card__price text-primary-alt")]/span[2]/text()').extract_first()
		
		charges = response.xpath('//div[contains(@class, "charges text-primary-alt mb-1 mb-md-2")]/text()').extract_first()
		
		if charges is not None:
			charges = re.sub(r'\D+', '', charges)

		anuncio['charges'] = charges

		anuncio['rooms_qty'] = response.xpath('//div[contains(@class, "col-sm-12 col-md-9 mr-md-auto")]//strong[re:test(.,"pi.ce")]').xpath('normalize-space()').re_first(r'\d+')

		anuncio['surface_inner'] = response.xpath('//div[contains(@class, "col-sm-12 col-md-9 mr-md-auto")]//strong[re:test(.,"pi.ce")]').xpath('normalize-space()').re_first(r'\d+')

		anuncio['floor_number'] = None
		cod = response.xpath('//div[contains(@class, "row align-items-center")]//h4').xpath('normalize-space()').extract_first()

		try:
			cod = re.sub(r'R.f\. ', '', cod)
		except:
			logging.error('cod_anuncio is not in right format')

		anuncio['cod_anuncio'] = cod

		anuncio['description'] = response.xpath('//article[contains(@class, "entry-card mb-3 mb-md-4")]').xpath('normalize-space()').extract_first()
		
		anuncio['available_date'] = None

		address = response.xpath('//h4[contains(@class, "property-details-card__location text-uppercase text-white pr-3 mb-2 mb-md-3")]').xpath('normalize-space()').extract_first()

		if address is None:
			logging.error('Address is null')

		anuncio['address'] = address

		anuncio['url_imgs'] = response.xpath('//div[contains(@class, "hero-slider-card")]//figure/img/@src').extract()
		
		anuncio['features'] = None

		anuncio['contact_phone'] = response.xpath('//div[contains(@class, "property-details-card__body mb-2 mb-sm-4 mb-lg-8 pb-2 pb-md-5")]//address/a').xpath('normalize-space()').extract()
		anuncio['contact_name'] = None

		anuncio['announcer'] = None
		anuncio['announcer_site'] = None

		anuncio['viewing_phone_number'] = []
		anuncio['viewing_desc'] = None

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
