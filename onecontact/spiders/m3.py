# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests
from datetime import datetime, timedelta

class M3Spider(scrapy.Spider):
	name = "m3"
	download_delay = 5

	def __init__(self, max_page=0, *args, **kwargs):
		super(M3Spider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	#Dependendo do robô pode ser feito de modo implicito
	def start_requests(self):
		
		reader = []		
		reader.append({'start_url':'https://www.m-3.com/fr/recherche/biens-a-louer?property_type=APPT', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'apartment'}) #Appartament
		reader.append({'start_url':'https://www.m-3.com/fr/recherche/biens-a-louer?property_type=HOUSE', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'house'}) #Maison
		reader.append({'start_url':'https://www.m-3.com/fr/recherche/biens-a-louer?property_type=INDUS', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'commercial', 'type_of_property':''}) #Commercial

		reader.append({'start_url':'https://www.m-3.com/fr/recherche/biens-a-vendre?property_type=APPT', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'apartment'}) #Appartament
		reader.append({'start_url':'https://www.m-3.com/fr/recherche/biens-a-vendre?property_type=HOUSE', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'house'}) #Maison
		reader.append({'start_url':'https://www.m-3.com/fr/recherche/biens-a-vendre?property_type=INDUS', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'commercial', 'type_of_property':''}) #Commercial

		for row in reader:
			yield scrapy.Request(row['start_url'], self.parse, meta={'dado': row, 'count': 1})

	#Pagina com a lista de links
	def parse(self, response):
		logging.warning("Iniciando url: " + response.url)
		anuncios_url = response.xpath('//div[contains(@id,"properties-page")]/article[contains(@class,"item")]')
		logging.warning('Total anuncio: ' + str(len(anuncios_url)))
		logging.warning('Start URL: ' + str(response.url))

		for anuncio_url in anuncios_url:
			url = anuncio_url.xpath('.//div[contains(@class,"jsPointer")]/@onclick').extract_first()
			url = re.sub(r'.*?href=\'', '', url)
			url = re.sub(r'\'', '', url)
			url = response.urljoin(url)
			#cod = re.sub(r'(\/)$','',url)
			#cod = re.sub(r'.*?\-\-','',cod)
			#logging.warning("Checando se anuncio ja existe.")
			#r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod)

			#if r_cod.status_code == 200 and int(r_cod.text) == 0:
			#	logging.warning("Datas estao ok e anuncio nao existe no servidor entao ir capturar!")
			#logging.warning("Nao possui codigo para checar então capturar todos!")
			yield scrapy.Request(url, callback=self.parse_contents, meta={'dado': response.meta['dado']})


		#	-------------------------------------------------------------------------------------------------
		#	|	PAGINACAO
		#	|	Paginacao condicional se especificado o valor maximo de página em 'max_page' argumento
		#	-------------------------------------------------------------------------------------------------
		#next_page = response.xpath('//a[contains(@id, "_lnkNext")][contains(@class,"right")]/@href').extract_first()

		count = int(response.meta['count'])

		res = response.xpath('//h1[contains(@class,"properties-title")]/text()').re_first('(\d+)')
		
		if res is not None:
			pages = int(res)//18
			if int(res)/18 > pages:
				pages = (int(res)//18)+1

			logging.warning('Paginas total: ' + str(pages))

			# Verifica se existe o objeto next_page
			if pages > 0 and count <= pages:
				print("Indo para pagina: " + str(count))
				next_page = response.url + '&page=' + str(count)
				yield scrapy.Request(next_page, callback=self.parse, meta={'dado': response.meta['dado'], 'count': (count+1)})


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

		anuncio['title'] = response.xpath('//div[contains(@class,"product__fixed")]//div[contains(@class,"product__title")]/h1/text()').extract_first()
		anuncio['price'] = response.xpath('//div[contains(@class,"product__fixed")]//p[contains(@class,"price")]').xpath('normalize-space()').re_first(r'CHF(.*)')
		anuncio['charges'] = response.xpath('//div[contains(@class,"product__fixed")]//p[contains(@class,"charges")]/text()').extract_first()

		if anuncio['charges'] is not None:
			anuncio['charges'] = re.sub(r'[\(\)]','',anuncio['charges'])
			anuncio['charges'] = re.sub(r'[cC]harge[s]?','', anuncio['charges'])
			anuncio['charges'] = re.sub(r'^(\+)','',anuncio['charges'])
			anuncio['charges'] = anuncio['charges'].strip()

		anuncio['rooms_qty'] = response.xpath('//div[./p/i[contains(@class,"icon-room")]]/p[re:test(.,"[pP]i.ces")]/text()').re_first(r'(\d.*?)\s')

		anuncio['surface_inner'] = response.xpath('//div[./p/i[contains(@class,"icon-surface")]]/p[re:test(.,"m")]/text()').extract_first()
		anuncio['floor_number'] = response.xpath('//p[contains(@class,"feature")][./span[1][re:test(.,".tage")]]/span[2]/text()').extract_first()

		anuncio['cod_anuncio'] = response.xpath('//div/p[re:test(.,"Ref\.")]').xpath('normalize-space()').re_first(r'R.f\.[\s]?(.*)')
		anuncio['description'] = response.xpath('//div[contains(@class,"print-page")][./h2[re:test(.,"[Dd]escription")]]').xpath('normalize-space()').extract_first()
		anuncio['available_date'] = response.xpath('//p[contains(@class,"feature")][./span[1][re:test(.,"[dD]isponibilit")]]/span[2]/text()').extract_first()

		if anuncio['description'] is None:
			anuncio['description'] = ''
		elif len(anuncio['description']) < 2:
			anuncio['description'] = ''
		else:
			anuncio['description'] = re.sub(r'^([dD]escription)', '', anuncio['description'])
			anuncio['description'] = anuncio['description'].strip()

		anuncio['address'] = response.xpath('//div[contains(@class,"product__fixed")]//div[contains(@class,"product__title")]/p').xpath('normalize-space()').extract_first()
		if anuncio['address'] is not None:
			anuncio['address'] = anuncio['address'].strip()

		imgs = response.xpath('//div[contains(@class,"popup-gallery")]//img/@src').extract()

		anuncio['url_imgs'] = imgs
		
		anuncio['features'] = response.xpath('//div[contains(@class,"product__body item")]/ul/li/text()').extract()

		if len(anuncio['features']) > 0:
			for i in range(0, len(anuncio['features'])):
				anuncio['features'][i] = anuncio['features'][i].strip()

		anuncio['contact_phone'] = response.xpath('//p[contains(@class,"feature")][./span[1][re:test(.,"[tT].l.phone")]]/span[2]/text()').extract()
		anuncio['contact_name'] = response.xpath('//p[contains(@class,"feature")][./span[1][re:test(.,"[cC]ontact")]]/span[2]/text()').extract_first()

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
