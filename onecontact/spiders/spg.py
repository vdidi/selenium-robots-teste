# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests
import json

#erros libs
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class SpgSpider(scrapy.Spider):
	name = "spg"
	#start_urls = ['https://www.homegate.ch/fr']
	download_delay = 5

	custom_settings = {
		'ROBOTSTXT_OBEY': False
	}

	def __init__(self, max_page=0, *args, **kwargs):
		super(SpgSpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	#Dependendo do robô pode ser feito de modo implicito
	def start_requests(self):
		#analisar se nao vale a pena carregar tudo na variavel e fechar arquivo e depois ir nos csvs

		reader = []

		#Genève
		reader.append({'start_url':'https://www.spg-rytz.ch/location?formatted_address=Gen%C3%A8ve,%20Suisse&current_page=1&per_page=20&location%5Bradius%5D%5Bcenter%5D%5Blat%5D=46.2180073&location%5Bradius%5D%5Bcenter%5D%5Blng%5D=6.121692499999995&location%5Bradius%5D%5Bdistance%5D=&location%5Bboundary%5D%5Bsouth_west%5D%5Blat%5D=45.90255270275367&location%5Bboundary%5D%5Bsouth_west%5D%5Blng%5D=5.644210648437479&location%5Bboundary%5D%5Bnorth_east%5D%5Blat%5D=46.58824354451148&location%5Bboundary%5D%5Bnorth_east%5D%5Blng%5D=6.621993851562479&extras%5Brooms%5D=&extras%5Bbathrooms%5D=&extras%5Bbedrooms%5D=&characteristics%5Bparking%5D=&characteristics%5Banimal_allowed%5D=&categories%5B%5D%5B0%5D=1', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'apartment'})
		reader.append({'start_url':'https://www.spg-rytz.ch/location?formatted_address=Gen%C3%A8ve,%20Suisse&current_page=1&per_page=20&location%5Bradius%5D%5Bcenter%5D%5Blat%5D=46.2043907&location%5Bradius%5D%5Bcenter%5D%5Blng%5D=6.143157699999961&location%5Bradius%5D%5Bdistance%5D=&location%5Bboundary%5D%5Bsouth_west%5D%5Blat%5D=46.17431460947396&location%5Bboundary%5D%5Bsouth_west%5D%5Blng%5D=6.1053789094970625&location%5Bboundary%5D%5Bnorth_east%5D%5Blat%5D=46.23573594913632&location%5Bboundary%5D%5Bnorth_east%5D%5Blng%5D=6.182798190502922&extras%5Brooms%5D=&extras%5Bbathrooms%5D=&extras%5Bbedrooms%5D=&characteristics%5Bparking%5D=&characteristics%5Banimal_allowed%5D=&categories%5B%5D%5B0%5D=2', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'house'})		
		reader.append({'start_url':'https://www.spg-rytz.ch/location?formatted_address=Gen%C3%A8ve,%20Suisse&current_page=1&per_page=20&location%5Bradius%5D%5Bcenter%5D%5Blat%5D=46.2043907&location%5Bradius%5D%5Bcenter%5D%5Blng%5D=6.143157699999961&location%5Bradius%5D%5Bdistance%5D=&location%5Bboundary%5D%5Bsouth_west%5D%5Blat%5D=46.16212601443635&location%5Bboundary%5D%5Bsouth_west%5D%5Blng%5D=6.062721057324211&location%5Bboundary%5D%5Bnorth_east%5D%5Blat%5D=46.24790204907465&location%5Bboundary%5D%5Bnorth_east%5D%5Blng%5D=6.2254560426757735&extras%5Brooms%5D=&characteristics%5Bparking%5D=&categories%5B%5D%5B0%5D=4&categories%5B%5D%5B1%5D=5', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'commercial', 'type_of_property':''})
		
		reader.append({'start_url':'https://www.spg-rytz.ch/vente?formatted_address=Gen%C3%A8ve,%20Suisse&current_page=1&per_page=20&location%5Bradius%5D%5Bcenter%5D%5Blat%5D=46.2043907&location%5Bradius%5D%5Bcenter%5D%5Blng%5D=6.143157699999961&location%5Bradius%5D%5Bdistance%5D=&location%5Bboundary%5D%5Bsouth_west%5D%5Blat%5D=46.14357818630962&location%5Bboundary%5D%5Bsouth_west%5D%5Blng%5D=6.066669268994133&location%5Bboundary%5D%5Bnorth_east%5D%5Blat%5D=46.26642086718352&location%5Bboundary%5D%5Bnorth_east%5D%5Blng%5D=6.221507831005852&extras%5Brooms%5D=&extras%5Bbathrooms%5D=&extras%5Bbedrooms%5D=&characteristics%5Bparking%5D=&characteristics%5Bnew_construction%5D=&categories%5B%5D%5B0%5D=11', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'apartment'})
		reader.append({'start_url':'https://www.spg-rytz.ch/vente?formatted_address=Gen%C3%A8ve,%20Suisse&current_page=1&per_page=20&location%5Bradius%5D%5Bcenter%5D%5Blat%5D=46.2043907&location%5Bradius%5D%5Bcenter%5D%5Blng%5D=6.143157699999961&location%5Bradius%5D%5Bdistance%5D=&location%5Bboundary%5D%5Bsouth_west%5D%5Blat%5D=46.14357818630962&location%5Bboundary%5D%5Bsouth_west%5D%5Blng%5D=6.066669268994133&location%5Bboundary%5D%5Bnorth_east%5D%5Blat%5D=46.26642086718352&location%5Bboundary%5D%5Bnorth_east%5D%5Blng%5D=6.221507831005852&extras%5Brooms%5D=&extras%5Bbathrooms%5D=&extras%5Bbedrooms%5D=&characteristics%5Bparking%5D=&characteristics%5Bnew_construction%5D=&categories%5B%5D%5B0%5D=12', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'house'})		
		reader.append({'start_url':'https://www.spg-rytz.ch/vente?formatted_address=Gen%C3%A8ve,%20Suisse&current_page=1&per_page=20&location%5Bradius%5D%5Bcenter%5D%5Blat%5D=46.2043907&location%5Bradius%5D%5Bcenter%5D%5Blng%5D=6.143157699999961&location%5Bradius%5D%5Bdistance%5D=&location%5Bboundary%5D%5Bsouth_west%5D%5Blat%5D=46.17431460947396&location%5Bboundary%5D%5Bsouth_west%5D%5Blng%5D=6.1053789094970625&location%5Bboundary%5D%5Bnorth_east%5D%5Blat%5D=46.23573594913632&location%5Bboundary%5D%5Bnorth_east%5D%5Blng%5D=6.182798190502922&extras%5Brooms%5D=&characteristics%5Bparking%5D=&categories%5B%5D%5B0%5D=19&categories%5B%5D%5B1%5D=20', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'commercial', 'type_of_property':''})
		
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

		data_load = {
			'formatted_address':'Genève, Suisse',
			'type':'rentals',
			'current_page':'1',
			'per_page':'500',
			'location[radius][center][lat]':'46.2043907',
			'location[radius][center][lng]':'6.143157699999961',
			'location[boundary][south_west][lat]':'46.13941771928568',
			'location[boundary][south_west][lng]':'5.9892499879882735',
			'location[boundary][north_east][lat]':'46.2705766302573',
			'location[boundary][north_east][lng]':'6.298927112011711',
			'categories[][0]':'1'
		}

		if response.meta['dado']['type_of_transaction'] == 'sell':
			data_load['type'] = 'sales'
			if response.meta['dado']['type_of_property'] == 'apartment':
				data_load['categories[][0]'] = '11'
			elif response.meta['dado']['type_of_property'] == 'house':
				data_load['categories[][0]'] = '12'
			else:
				data_load['categories[][0]'] = '19'
				data_load['categories[][1]'] = '20'
		else:
			if response.meta['dado']['type_of_property'] == 'apartment':
				data_load['categories[][0]'] = '1'
			elif response.meta['dado']['type_of_property'] == 'house':
				data_load['categories[][0]'] = '2'
			else:
				data_load['categories[][0]'] = '4'
				data_load['categories[][1]'] = '5'


		#'categories[][0]':'1' - appt - rentals
		#'categories[][0]':'2' - house
		#'categories[][0]':'4' | 'categories[][0]':'5'  - commercial


		#sales
		#'categories[][0]':'11' apartment
		#'categories[][0]':'12' house
		#'categories[][0]':19 | 'categories[][1]':'20'

		#rentals - rent
		#sales - venda

		url = 'https://www.spg-rytz.ch/app/fr/api/v1/search'

		r = requests.post(url, data=data_load)

		if r.status_code == 200:

			res = json.loads(r.text)
			anuncios_url = res['data']

			logging.warning('quantidade: ' + str(len(anuncios_url)))
			logging.warning('transacao: ' + response.meta['dado']['type_of_transaction'])
			logging.warning('property: ' + response.meta['dado']['type_of_property'])

			for anuncio_url in anuncios_url:
				url = response.urljoin(anuncio_url['property_url'])
				
				yield scrapy.Request(
					url, 
					callback=self.parse_contents, 
					errback=self.errback_httpbin,
					meta={'dado': response.meta['dado']}
					)

		#so para testar primeiro link
		#url = response.urljoin(anuncios_url[0].xpath('.//a[contains(@class,"link")]/@href').extract_first())
		#url = re.sub(r'(\/)$', '', url)
		#cod = re.sub(r'.*?\/', '', url)
		
		#r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod)

		#logging.warning("resposta requisicao cod: " + cod)

		#if r_cod.status_code == 200 and int(r_cod.text) == 0:
		#	logging.warning('anuncio não existe então capturar!')
		#	yield scrapy.Request(url, callback=self.parse_contents, meta={'dado': response.meta['dado']})

		#	-------------------------------------------------------------------------------------------------
		#	|	PAGINACAO
		#	|	Paginacao condicional se especificado o valor maximo de página em 'max_page' argumento
		#	-------------------------------------------------------------------------------------------------
		'''
		next_page = None

		count = int(response.meta['count'])
		
		# Verifica se existe o objeto next_page
		if next_page is not None:
			print("count " + str(response.meta['count'] + 1))
			if (count < self.max_page and self.max_page !=0) or (self.max_page == 0):
				print("Indo para pagina: " + str(count + 1))
				next_page = response.urljoin(next_page)
				yield scrapy.Request(next_page, callback=self.parse, meta={'dado': response.meta['dado'], 'count': (count+1)})
			else:
				next_page = None
		'''

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

		areaSidebar = response.xpath('//div[contains(@class,"l-property-details")]')

		anuncio['cod_anuncio'] = areaSidebar.xpath('.//td[./strong[re:test(.,"[iI]d [oO]bjet")]]/span/text()').extract_first()

		anuncio['description'] = response.xpath('//p[preceding-sibling::div[contains(@id,"description_list")]]/small').xpath('normalize-space()').extract_first()
		
		if len(anuncio['description']) < 2:
			anuncio['description'] = ''
		
		anuncio['rooms_qty'] = response.xpath('//p[./strong[re:test(.,"[nN]ombre de pi.ces")]]/span/text()').re_first('\d+.*')
		anuncio['surface_inner'] = response.xpath('//strong[contains(@title,"Surface")]/span/text()').re_first('([^\n]*)')
		anuncio['price'] = areaSidebar.xpath('.//h3[contains(@class,"price")]/text()').re_first('\d+.*')

		anuncio['charges'] = response.xpath('//p[./strong[re:test(.,"[cC]harges")]]/span/text()').re_first('\d+.*')

		if anuncio['price'] is None:
			anuncio['price'] = response.xpath('//p[./strong[re:test(.,"[pP]rix")]]/span/text()').re_first('\d+.*')
		
		if anuncio['price'] is not None:
			anuncio['price'] = re.sub('\.','',anuncio['price'])
			anuncio['price'] = re.sub('\,','.',anuncio['price'])
			anuncio['price'] = re.sub('\.','',anuncio['price'])


		if anuncio['charges'] is not None:
			anuncio['charges'] = re.sub('\.','', anuncio['charges'])
			anuncio['charges'] = re.sub('\,','.',anuncio['charges'])
			anuncio['charges'] = re.sub('\.','',anuncio['charges'])

		anuncio['floor_qty'] = None

		anuncio['title'] = response.xpath('//h1[contains(@class,"text")][preceding-sibling::h4][following-sibling::h3]/text()').extract_first()
		if anuncio['title'] is not None:
			anuncio['title'] = anuncio['title'].strip()

		anuncio['available_date'] = areaSidebar.xpath('.//td[./strong[re:test(.,"[dD]isponibilit.")]]/span/text()').re_first('\d+[\/\.\-]\d+[\/\.\-]\d{4}')
		
		imgs = response.xpath('//div[contains(@class,"content-gallery")]/ul/li/a/@href').extract()
		url_imgs = []
		if imgs is not None:
			for img in imgs:
				url_img = response.urljoin(img)
				url_imgs.append(url_img)

		anuncio['url_imgs'] = url_imgs

		anuncio['address'] = areaSidebar.xpath('.//address/span[./span[following-sibling::a]]').xpath('normalize-space()').re_first('(.*?)[\s]?voir sur')
		
		features_final = []
		features = response.xpath('//div[contains(@id,"description_list")]//li/text()').extract()
		features2 = response.xpath('//div[contains(@id,"info-characteris")]/p[./span[re:test(.,"([Oo]ui|([1-9]))")]]/strong[ not(re:test(.,"[nN]ombre de pi")) ]/text()').extract()
		
		for feature in features:
			if len(feature) > 0:
				features_final.append(feature)

		for feature in features2:
			if len(feature) > 0:
				features_final.append(feature)

		anuncio['features'] = []
		if features_final is not None and len(features_final) > 0:
			anuncio['features'] = features_final

		anuncio['announcer'] = 'SPG-RYTZ'
		anuncio['announcer_site'] = 'https://www.spg-rytz.ch'

		anuncio['contact_phone'] = ['+41 58 810 30 00']
		anuncio['contact_name'] = ''

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
