# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests
from datetime import datetime, timedelta
import json
from scrapy import Selector

#erros libs
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class ComptoirSpider(scrapy.Spider):
	name = "comptoir"
	download_delay = 10

	def __init__(self, max_page=0, *args, **kwargs):
		super(ComptoirSpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	#Dependendo do robô pode ser feito de modo implicito
	def start_requests(self):
		
		reader = []
		
		#rent
		reader.append({
			#'start_url':'http://www.comptoir-immo.ch/Accueil/Location/cat/app/',
			'start_url': 'https://comptoir-immo.ch/location/appartement/all/geneve/?surface-min=0&surface-max=2500%2B&rooms-min=1%2C0&rooms-max=10%2C0%2B&price-min=0&price-max=10%27000%2B&ref=&lat=&lng=&zoom=&form_nonce=9844ac39e9&sortby=published_desc',
			'category': 'APP',
			'propertyType': 'rent',
			'state': 'Genève', 
			'type_of_transaction': 'rent', 
			'nature_of_property':'residential', 
			'type_of_property':'appartement'
			}) #Appartament
		
		# reader.append({
		# 	'start_url':'http://www.comptoir-immo.ch/Accueil/Location/cat/res/',
		# 	'category': 'MAI',
		# 	'propertyType': 'rent', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'residential', 
		# 	'type_of_property':'house'
		# 	}) #Maison

		# reader.append({
		# 	'start_url':'http://www.comptoir-immo.ch/Accueil/Location/cat/lco/',
		# 	'category': 'ARC',
		# 	'propertyType': 'rent', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'rent', 
		# 	'nature_of_property':'commercial', 
		# 	'type_of_property':''
		# 	}) #Commercial
		
		#sell
		reader.append({
			#'start_url':'https://comptoir-immo.ch/vente/appartements/',
			'start_url': 'https://comptoir-immo.ch/vente/appartement/all/geneve/?surface-min=0&surface-max=2500%2B&rooms-min=1%2C0&rooms-max=10%2C0%2B&price-min=0&price-max=5%27000%27000%2B&ref=&lat=&lng=&zoom=&form_nonce=9844ac39e9&sortby=published_desc',
			'category': 'APP',
			'propertyType': 'sale', 
			'state': 'Genève', 
			'type_of_transaction': 'sell', 
			'nature_of_property':'residential', 
			'type_of_property':'appartement'
			}) #Appartament
		
		# reader.append({
		# 	'start_url':'https://comptoir-immo.ch/vente/maisons/',
		# 	'category': 'MAI',
		# 	'propertyType': 'sale', 
		# 	'state': 'Genève', 
		# 	'type_of_transaction': 'sell', 
		# 	'nature_of_property':'residential', 
		# 	'type_of_property':'house'
		# 	}) #Maison
		
		# reader.append({
		# 	'start_url':'https://comptoir-immo.ch/vente/biens-commerciaux/',
		# 	'category': 'ARC',
		# 	'propertyType': 'sale', 
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
				dont_filter= True
				)

		#yield scrapy.Request("http://www.anibis.ch/fr/immobilier-immobilier-locations-gen%C3%A8ve--418/advertlist.aspx", self.parse, meta={'dado': 'teste', 'count': 1})

	#Pagina com a lista de links
	def parse(self, response):
		logging.warning("Iniciando url: " + response.url)

		# data = {
		# 	'page_no': response.meta['count'],
		# 	'category': response.meta['dado']['category'],
		# 	'category': 'APP',
		# 	'sorting': 'prix_asc',
		# 	'propertyType': response.meta['dado']['propertyType'],
		# 	'npa': 'Genève, Suisse',
		# 	'ne_lat': '46.32560793209023',
		# 	'sw_lat': '46.084199490702105',
		# 	'sw_lon': '5.461562915234367',
		# 	'ne_lon': '6.826614184765617',
		# 	'zoom': 9,
		# 	'geo_code': '46.2043907,6.143157699999961',
		# }

		# data = {
		# 	'page_no': 1,
		# 	'category': 'APP',
		# 	'sorting': 'prix_asc',
		# 	'propertyType': 'rent',
		# 	'npa': 'Genève, Suisse',
		# 	'ne_lat': '46.32560793209023',
		# 	'sw_lat': '46.084199490702105',
		# 	'sw_lon': '5.461562915234367',
		# 	'ne_lon': '6.826614184765617',
		# 	'zoom': 9,
		# 	'geo_code': '46.2043907,6.143157699999961',
		# }

		# if response.meta['dado']['type_of_transaction'] == 'rent':
		# 	url = 'https://comptoir-immo.ch/location/'
		# else:
		# 	data['propertyType'] = 'sale'
		# 	url = 'https://comptoir-immo.ch/vente/'

		# if response.meta['dado']['category'] == 'ARC':
		# 	del data['category']
		# 	data['sub_category'] = 'ARC'

		# r = requests.get(url, params=data)

		# if r.status_code == 200:
		# html = Selector(text=r.text)
		#anuncios_url = html.xpath('//a[contains(@class, "property-title d-block")]/@href').extract()
		anuncios_url = response.xpath('//div[contains(@class, "container")]/div/article//div[contains(@class, "swiper-container")]//a/@href').extract()
		anuncios_geneve = []
  
		for anuncio_url in anuncios_url:
			if re.search('[gG]en.ve', anuncio_url):
				anuncios_geneve.append(anuncio_url)
    
		if len(anuncios_geneve) > 0:
			anuncios_geneve = list(dict.fromkeys(anuncios_geneve))
			for anuncio_geneve in anuncios_geneve:
				yield scrapy.Request(
					anuncio_geneve, 
					callback=self.parse_contents, 
					errback=self.errback_httpbin,
					meta={'dado': response.meta['dado']}
					)

		pages = response.xpath('//nav[contains(@class, "pagination")]//li/a').xpath('normalize-space()').extract()
		count = int(response.meta['count'])
		if len(pages) > 0:
			number_pages = pages[-1]
			for page_number in number_pages:
				url = 'https://comptoir-immo.ch/location/appartement/all/geneve/?page=' + page_number + '&surface-min=0&surface-max=2500%2B&rooms-min=1%2C0&rooms-max=10%2C0%2B&price-min=0&price-max=10%27000%2B&ref&lat&lng&zoom&form_nonce=9844ac39e9&sortby=published_desc'
				yield scrapy.Request(
					url, 
					callback=self.parse,
					errback=self.errback_httpbin, 
					meta={'dado': response.meta['dado'], 'count': (count+1)}
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
		# anuncio['type_of_property'] = response.xpath('//div[contains(@class, "property-category-type")]/h2/text()').re_first(r'(.*?)\s')

		anuncio['title'] = response.xpath('//h1[contains(@class,"heading-2")]/text()').extract_first()
		
		price = response.xpath('//tr[./th[re:test(.,"[lL]oyer")]]/td/text()').extract_first()

		if price is not None:
			price = re.sub(r'\D+','', price)

		anuncio['price'] = price
  
		charges = None

		charges = response.xpath('//tr[./th[re:test(.,"[cC]harge")]]/td/text()').extract_first()
		if charges is not None:
			charges = re.sub(r'\D+','', charges)
  
		anuncio['charges'] = charges

		anuncio['rooms_qty'] = response.xpath('//tr[./th[re:test(.,"[pP]i.ce")]]/td/text()').extract_first()

		surface_inner = response.xpath('//tr[./th[re:test(.,"[hH]abitable")]]/td/text()').extract_first()

		if surface_inner is not None:
			surface_inner = re.sub(r'\D+','', surface_inner)

		anuncio['surface_inner'] = surface_inner
		# anuncio['floor_number'] = response.xpath('//li[./label[re:test(.,"[eEéÉ]tage")]]/span').xpath('normalize-space()').extract_first()
		anuncio['floor_number'] = response.xpath('//tr[./th[re:test(.,".tage")]]/td/text()').re_first(r"\d+")

		anuncio['cod_anuncio'] = response.xpath('//tr[./th[re:test(.,"[rR].f.rence")]]/td/text()').extract_first()
		
		description = response.xpath('//div[contains(@class, "rich-text")]//p/text()').extract()
		if description is not None:
			description = ''.join(description)
   
		anuncio['description'] = description
		
		anuncio['available_date'] = response.xpath('//tr[./th[re:test(.,"[dD]isponib")]]/td/text()').extract_first()

		anuncio['address'] = response.xpath('//tr[./th[re:test(.,"[aA]dresse")]]/td/text()').extract_first()

		anuncio['url_imgs'] = response.xpath('//figure/img/@src').extract()
		
		anuncio['features'] = []

		contact_phone = []

		phone = response.xpath('//tr[./th[re:test(.,"Téléphone")]]/td').xpath('normalize-space()').extract_first()

		if phone is not None:
			contact_phone.append(phone)

		anuncio['contact_phone'] = contact_phone
		anuncio['contact_name'] = None

		anuncio['announcer'] = 'Comptoir Immobilier'
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
