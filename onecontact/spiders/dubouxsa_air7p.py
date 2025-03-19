# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests

class DubouxSaAir7pSpider(scrapy.Spider):
	name = "dubouxsa_air7p"

	download_delay = 3

	def __init__(self, max_page=0, *args, **kwargs):
		super(DubouxSaAir7pSpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	def start_requests(self):

		reader = []
		#
		reader.append({'start_url':'http://regieduboux.ch/a-louer?field_ville_value=&field_project_type_tid=4&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=6040&field_nombre_de_pieces_value%5Bmin%5D=0&field_nombre_de_pieces_value%5Bmax%5D=6', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'appartement'})
		reader.append({'start_url':'http://regieduboux.ch/a-louer?field_ville_value=&field_project_type_tid=3&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=6040&field_nombre_de_pieces_value%5Bmin%5D=0&field_nombre_de_pieces_value%5Bmax%5D=6', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'house'}) #Maison
		reader.append({'start_url':'http://regieduboux.ch/a-louer?field_ville_value=&field_project_type_tid=6&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=6040', 'type_of_transaction': 'rent', 'nature_of_property':'commercial', 'type_of_property':''})
		reader.append({'start_url':'http://regieduboux.ch/a-louer?field_ville_value=&field_project_type_tid=8&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=6040', 'type_of_transaction': 'rent', 'nature_of_property':'commercial', 'type_of_property':'park'})
		reader.append({'start_url':'http://regieduboux.ch/a-louer?field_ville_value=&field_project_type_tid=5&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=6040', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'immeubles'}) #Immeubles = Flat
		reader.append({'start_url':'http://regieduboux.ch/a-louer?field_ville_value=&field_project_type_tid=7&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=6040', 'type_of_transaction': 'rent', 'nature_of_property':'', 'type_of_property':'field'}) #Terrain = Field
		
		reader.append({'start_url':'http://regieduboux.ch/a-vendre?field_ville_value=&field_project_type_tid=4&field_nombre_de_pieces_value%5Bmin%5D=0&field_nombre_de_pieces_value%5Bmax%5D=13&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=8500000&field_r_f_rence_value=', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'appartement'})
		reader.append({'start_url':'http://regieduboux.ch/a-vendre?field_ville_value=&field_project_type_tid=3&field_nombre_de_pieces_value%5Bmin%5D=0&field_nombre_de_pieces_value%5Bmax%5D=13&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=8500000&field_r_f_rence_value=', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'house'})
		reader.append({'start_url':'http://regieduboux.ch/a-vendre?field_ville_value=&field_project_type_tid=6&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=8500000&field_r_f_rence_value=', 'type_of_transaction': 'sell', 'nature_of_property':'commercial', 'type_of_property':''})
		reader.append({'start_url':'http://regieduboux.ch/a-vendre?field_ville_value=&field_project_type_tid=8&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=8500000&field_r_f_rence_value=', 'type_of_transaction': 'sell', 'nature_of_property':'commercial', 'type_of_property':'park'})
		reader.append({'start_url':'http://regieduboux.ch/a-vendre?field_ville_value=&field_project_type_tid=5&field_prix_value%5Bmin%5D=0&field_prix_value%5Bmax%5D=8500000&field_r_f_rence_value=', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'immeubles'}) #Immeubles = Flat
		reader.append({'start_url':'http://regieduboux.ch/a-vendre?field_ville_value=&field_project_type_tid=7&field_r_f_rence_value=	', 'type_of_transaction': 'sell', 'nature_of_property':'', 'type_of_property':'terrain'}) #Terrain

		for row in reader:
			yield scrapy.Request(row['start_url'], self.parse, meta={'dado': row, 'count': 1})

	def parse(self, response):
		anuncios_url = response.xpath('//div[contains(@class, "content-column")]//div[contains(@class, "view-content")]//div//a')
		
		for anuncio_url in anuncios_url:
			url = 'http://www.regieduboux.ch' + anuncio_url.xpath('./@href').extract_first()
			yield scrapy.Request(url, callback=self.parse_contents, meta={'dado': response.meta['dado']})

		#PAGINATION

		next_page = response.xpath('//div[contains(@class, "item-list")]//li[contains(@class, "pager-next")]//a').xpath('normalize-space()').extract_first()

		count = int(response.meta['count'])
		
		# Verifica se existe o objeto next_page
		if next_page is not None:
			print("count " + str(response.meta['count'] + 1))

			next_page = 'http://regieduboux.ch' + response.xpath('//div[contains(@class, "item-list")]//li[contains(@class, "pager-next")]//a/@href').extract_first()
			yield scrapy.Request(next_page, callback=self.parse, meta={'dado': response.meta['dado'], 'count': (count+1)})

	def parse_contents(self, response):

		anuncio = OnecontactItem()
		anuncio['name'] = self.name
		anuncio['country'] = 'Switzerland'
		anuncio['url_anuncio'] = response.url

		anuncio['type_of_transaction'] = response.meta['dado']['type_of_transaction'] # rent | buy
		anuncio['nature_of_property'] = response.meta['dado']['nature_of_property']   # residential | commercia//
		anuncio['type_of_property'] = response.meta['dado']['type_of_property']
		url_imgs = []
		contacts = []
		price = None
		surface = None
		anuncio['contact_name'] = None
		if response.meta['dado']['type_of_transaction'] == 'rent':
			
			anuncio['description'] = response.xpath('//div[contains(@class,"descLong")]').xpath('normalize-space()').extract_first()

			anuncio['cod_anuncio'] = response.xpath('//table[contains(@class, "table_info")]//tr[re:test(., "[rR].f[e.]rence")]//td').xpath('normalize-space()').extract_first()
			anuncio['available_date'] = response.xpath('//table[contains(@class, "table_info")]//tr[re:test(., "[dD]isponibilit.")]//td//div[contains(@class, "field-item")]').xpath('normalize-space()').extract_first()

			pieces = response.xpath('//table[contains(@class, "table_info")]//tr[re:test(., "[pP]i.ce")]//td').xpath('normalize-space()').extract_first()

			title = response.xpath('//div[contains(@class, "node-content")]//h2/span').xpath('normalize-space()').extract_first()
			
			if title is None or title == '':
				title = response.xpath('//div[contains(@class, "node-content")]//h2').xpath('normalize-space()').extract_first()

			anuncio['title'] = title

			price = response.xpath('//table[contains(@class, "table_info")]//tr[re:test(., "Loyer")]//td').xpath('normalize-space()').extract_first()
			anuncio['charges'] = None
			route = anuncio['title']

			surface = response.xpath('//table[contains(@class, "table_info")]//div[re:test(., "m2")]').xpath('normalize-space()').extract_first()

			if surface is not None:
				surface = re.sub(r'[\ ]m2', '', surface)

			if route is not None:
				route = re.sub(r'\,.*$', '', route)

			anuncio['address'] = route
			
			imgs = response.xpath('//div[contains(@class, "content-inner")]//section//div//div//article//div[contains(@class, "leftBien")]//section//div//div/img')
			if imgs is not None and len(imgs):
				for img in imgs:
					url = img.xpath('./@src').extract_first()
					url_imgs.append(url)

			phone = response.xpath('//table[contains(@class, "table_info")]//tr[re:test(., "T.l.phone[\ ]:")]//td').xpath('normalize-space()').extract_first()
			if phone is not None:
				phone = re.sub(r'\D+', '', phone)
				contacts.append(phone)
			else:
				contacts.append('+41(0)213215070')
				anuncio['contact_name'] = 'RÉGIE DUBOUX SA'
		else:

			anuncio['description'] = None

			sell_ref = response.xpath('//div[contains(@class, "leftBienAvendre")]//span[contains(@class, "refprix")]').xpath('normalize-space()').extract_first()
			sell_ref = re.sub(r'R[eé]f[eé]rence[\ ]:[\ ]', '', sell_ref)

			anuncio['cod_anuncio'] = sell_ref
			anuncio['available_date'] = None

			price = response.xpath('//div[contains(@class, "leftBienAvendre")]//div[contains(@class, "field-item even")]').xpath('normalize-space()').extract_first()
			anuncio['charges'] = None
			pieces = response.xpath('//div[contains(@class, "leftBienAvendre")]//li[re:test(., "pièces")]').xpath('normalize-space()').extract_first()

			surface = response.xpath('//div[contains(@class, "leftBienAvendre")]//div[re:test(., "m2")]/text()').extract_first()
			if surface is not None:
				surface = re.sub(r'\D+', '', surface)

			anuncio['title'] = response.xpath('//div[contains(@class, "leftBienAvendre")]//h3').xpath('normalize-space()').extract_first()
			anuncio['address'] = response.xpath('//div[contains(@class, "leftBienAvendre")]//strong').xpath('normalize-space()').extract_first()
			url_imgs = response.xpath('//figure[contains(@class, "clearfix")]/img/@src').extract()
			contacts.append('+41(0)213215070')
			anuncio['contact_name'] = 'RÉGIE DUBOUX SA'

		if pieces is not None:
			pieces = re.sub(r'\D+', '', pieces)
			pieces = float(pieces)/10

		if price is not None:
			price = re.sub(r'\D+', '', price)	

		anuncio['rooms_qty'] = pieces
		anuncio['floor_qty'] = None
		anuncio['price'] = price

		anuncio['surface_inner'] = surface

		anuncio['announcer'] = 'RÉGIE DUBOUX SA'
		anuncio['announcer_site'] = 'http://www.regieduboux.ch'

		anuncio['contact_phone'] = contacts 

		anuncio['url_imgs'] = url_imgs
		anuncio['features'] = []

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
		anuncio['state'] = None
		anuncio['postal_code'] = None

		anuncio['viewing_phone_number'] = []
		anuncio['contact_name'] = None
		anuncio['viewing_desc'] = None

		yield anuncio
