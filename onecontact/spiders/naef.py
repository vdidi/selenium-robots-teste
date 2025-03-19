# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests
from scrapy import Selector

#erros libs
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class NaefSpider(scrapy.Spider):
	name = "naef"
	download_delay = 5

	def __init__(self, max_page=0, *args, **kwargs):
		super(NaefSpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	def start_requests(self):
		reader = []

		#Genève
		reader.append({'start_url':'http://www.naef.ch/location-appartements/', 'type': 'rent', 'action': 'property_search_louer', 'cat': 'APP', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'apartment'})
		reader.append({'start_url':'http://www.naef.ch/location-maisons/', 'type': 'rent', 'action': 'property_search_louer', 'cat': 'MAI', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'house'})
		reader.append({'start_url':'https://www.naef.ch/louer/surface-commerciales', 'type': 'rent', 'cat': 'LCO', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'commercial', 'type_of_property':''})

		reader.append({'start_url':'http://www.naef.ch/vente-appartements/', 'action': 'property_search', 'type': 'buy', 'cat': 'APP', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'apartment'})
		reader.append({'start_url':'http://www.naef.ch/vente-maisons/', 'action': 'property_search', 'type': 'buy', 'cat': 'MAI', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'house'})
		reader.append({'start_url':'http://www.naef.ch/vente-commercial/', 'action': 'property_search', 'type': 'buy', 'cat': 'LCO', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'commercial', 'type_of_property':''})

		for row in reader:
			yield scrapy.Request(
				row['start_url'], 
				self.parse,
				errback=self.errback_httpbin, 
				meta={'dado': row, 'count': 1}, 
				dont_filter=True
				)

	#Pagina com a lista de links
	def parse(self, response):

		data = {
				'action': 'property_search_louer',
				'prop[0][name]': 'propTypehidden',
				'prop[0][value]': response.meta['dado']['type'],
				'prop[1][name]': 'property_criteria_type',
				'prop[1][value]': response.meta['dado']['cat'],
				'prop[2][name]': 'hdnRadius',
				'prop[2][value]': 5,
				'prop[3][name]': 'hdnLat',
				'prop[3][value]': 46.20496309804872,
				'prop[4][name]': 'hdnLng',
				'prop[4][value]': 6.144018173217773,
				'prop[5][name]': 'lang',
				'prop[5][value]': 'fr',
				'prop[6][name]': 'sort',
				'prop[6][value]': 'default',
				'prop[7][name]': 'pageID',
				'prop[7][value]': 7155,
				'prop[8][name]': 'avantage',
				'prop[8][value]': '',
				'prop[9][name]': 'npa',
				'prop[9][value]': '',
				'prop[10][name]': 'posta_code',
				'prop[10][value]': '',
				'prop[11][name]': 'canton_filter',
				'prop[11][value]': response.meta['dado']['state'],
				'prop[12][name]': 'property_objects_type',
				'prop[12][value]': '',
				'prop[13][name]': 'prixMinCustom',
				'prop[13][value]': '',
				'prop[14][name]': 'prixMaxCustom',
				'prop[14][value]': '',
				'prop[15][name]': 'roomMin',
				'prop[15][value]': 1,
				'prop[16][name]': 'roomMax',
				'prop[16][value]': '6+',
				'prop[17][name]': 'surfaceMinCustom',
				'prop[17][value]': '',
				'prop[18][name]': 'surfaceMaxCustom',
				'prop[18][value]': '',
				'propIds': '',
				'start': 0,
				'regionSelected': 'false',
				'propTypehidden': 'rent',
				'sort': 'default',
				'limit': 27
		}

		r = requests.post('https://www.naef.ch/wp-admin/admin-ajax.php', data=data)

		if r.status_code == 200:

			html = Selector(text=r.text)

			logging.warning("Iniciando url: " + response.url)
			anuncios_url = html.xpath('//div[contains(@class,"naef")][re:test(@id,"^(\d+)$")]')

			for anuncio_url in anuncios_url:
				url = response.urljoin(anuncio_url.xpath('.//a[contains(@class,"item-hover")]/@href').extract_first())

				if url[-1] == '/':
					cod = re.sub(r'\/$','',  url)
					cod = re.sub(r'.*?\/','',  cod)

					if re.match(r'^\d.*?\d$', cod):
						r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod + '/' + self.name)

						logging.warning("resposta requisicao cod: " + cod)

						if r_cod.status_code == 200 and int(r_cod.text) == 0:
							logging.warning('anuncio não existe no servidor então capturar!')
							yield scrapy.Request(
								url, 
								callback=self.parse_contents, 
								errback=self.errback_httpbin,
								meta={'dado': response.meta['dado'], 'cod': cod}
								)
				# else:
				# 	logging.warning('Codigo nao identificado para testar então capturar!')
				# 	yield scrapy.Request(
				# 		url, 
				# 		callback=self.parse_contents, 
				# 		errback=self.errback_httpbin,
				# 		meta={'dado': response.meta['dado']}
				# 		)


		#	-------------------------------------------------------------------------------------------------
		#	|	PAGINACAO
		#	|	Paginacao condicional se especificado o valor maximo de página em 'max_page' argumento
		#	-------------------------------------------------------------------------------------------------
		
		#next_page = response.xpath('//a[re:test(@title,"Page suivante|Next page")]/@href').extract_first()

		count = int(response.meta['count'])

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

		# anuncio['cod_anuncio'] = re.sub(r'.*?id=', '', response.url)
		# anuncio['cod_anuncio'] = re.sub(r'\-.*', '', anuncio['cod_anuncio'])
		anuncio['cod_anuncio'] = response.meta['cod']
		
		description = response.xpath('//div[contains(@class, "property-description")]').xpath('normalize-space()').extract_first()

		if len(description) < 2:
			description = ''				

		anuncio['description'] = description

		anuncio['rooms_qty'] = response.xpath('//ul[contains(@class, "property-details__meta")]/li[contains(@class, "item--room")]/div//span/text()').re_first(r'\d+')
		anuncio['floor_qty'] = None
		anuncio['surface_inner'] = response.xpath('//ul[contains(@class, "property-details__meta")]/li[contains(@class, "item")]/div[contains(@title, "Surface")]').re_first(r'\d+')
		anuncio['available_date'] = response.xpath('//ul[contains(@class, "list")]/li[contains(@class, "property-rate-list")]/span[re:test(.,"Disponibilit")]').re_first(r'\d{2}[-/]\d{2}[-/]\d+')

		anuncio['title'] = response.xpath('//h1[contains(@class, "property-details__title h3")]').xpath('normalize-space()').extract_first()
		anuncio['price'] = response.xpath('//div[contains(@class, "property-details__header-group")]/span[contains(@class, "details__price")]').xpath('normalize-space()').re_first(r'\d.*')
		anuncio['charges'] = response.xpath('//ul[contains(@class, "list")]/li[contains(@class, "property-rate-list")]/span[re:test(.,"Charges")]').re_first(r'\d.*')
		anuncio['address'] = response.xpath('//ul[contains(@class, "list")]/li[contains(@class, "property-rate-list")]/span[re:test(.,"Adresse")]/text()').extract_first()

		#adicionar em todos
		anuncio['floor_number'] = response.xpath('//ul[contains(@class, "property-details__meta")]/li[contains(@class, "item")]/div[re:test(@title, ".tage")]').re_first(r'\d+')

		if anuncio['floor_number'] is not None:
			anuncio['floor_number'] = anuncio['floor_number'].strip()

		if anuncio['address'] is not None:
			anuncio['address'] = anuncio['address'].strip()

		#anuncio['url_imgs'] = response.xpath('//figure[contains(@class,"card__picture")]/img/@data-src').extract()
		anuncio['url_imgs'] = response.xpath('//img[contains(@class, "property-media-card-img")]/@src').extract()

		anuncio['features'] = []
		features = response.xpath('//ul[contains(@class, "property-characteristics list-unstyled")]/li/text()').extract()

		for feature in features:
			if len(feature) > 0:
				anuncio['features'].append(feature)

		anuncio['contact_phone'] = []
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