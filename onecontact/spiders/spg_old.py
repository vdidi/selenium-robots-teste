# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import csv
import logging
import requests
import json

#tratativa para (rent|buy) e (fr|eng) e local(city) pela url

class SpgSpider(scrapy.Spider):
	name = "spg_old"
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

		reader.append({'start_url':'http://www.spg.ch/location-appart-villas-chalets', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':''})
		reader.append({'start_url':'http://www.spg.ch/a-louer/locaux-commerciaux', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'commercial', 'type_of_property':''})
		
		reader.append({'start_url':'http://www.spg.ch/appart-villas-chalets', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':''})
		reader.append({'start_url':'http://www.spg.ch/a-vendre/locaux-commerciaux', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'commercial', 'type_of_property':''})

		for row in reader:
			yield scrapy.Request(row['start_url'], self.parse_contents, meta={'dado': row, 'count': 1})

	#Pagina com a lista de links
	def parse(self, response):
		logging.warning("Iniciando url: " + response.url)
		anuncios_url = response.xpath('//div[contains(@class, "maplocation")]')



		for anuncio_url in anuncios_url:
			url = response.urljoin(anuncio_url.xpath('./@href').extract_first())
			url = re.sub(r'(\/)$', '', url)
			cod = re.sub(r'.*?\/', '', url)

			if cod is not None:
				r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod + '/' + self.name)
				logging.warning("resposta requisicao cod: " + cod)
				if r_cod.status_code == 200 and int(r_cod.text) == 0:
					logging.warning('anuncio não existe no servidor então capturar!')
			else:
				logging.warning("Codigo nao encontrado")
			
			yield scrapy.Request(url, callback=self.parse_contents, meta={'dado': response.meta['dado']})




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

	# Pagina com todos campos que vao ser inseridos no robô
	def parse_contents(self, response):
		anuncios_url = response.xpath('//div[contains(@class, "maplocation")]')
		anuncios = []
		for anuncio_url in anuncios_url:

			anuncio = OnecontactItem()
			anuncio['name'] = self.name
			anuncio['country'] = 'Switzerland'
			anuncio['url_anuncio'] = anuncio_url.xpath('.//a[re:test(.,"[fF]iche d.taill.e")]/@href').extract_first()

			#dados inseridos do csv
			anuncio['type_of_transaction'] = response.meta['dado']['type_of_transaction']
			anuncio['state'] = response.meta['dado']['state']
			anuncio['nature_of_property'] = response.meta['dado']['nature_of_property']   # residential | commercial
			anuncio['type_of_property'] = response.meta['dado']['type_of_property']

			anuncio['cod_anuncio'] = anuncio_url.xpath('.//a[re:test(.,"[fF]iche d.taill.e")]/@href').re_first(r'ref\-(\d+.*)')
			
			cod = anuncio['cod_anuncio']
			r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod)

			logging.warning("resposta requisicao cod: " + cod)
			
			if r_cod.status_code == 200 and int(r_cod.text) == 0:

				desc = anuncio_url.xpath('.//div[contains(@class,"map_objet_bottom_mid")]').xpath('normalize-space()').re_first(r'[dD]escription[\s]?\:(.*?)[rR].f.rence[\s]?')
				desc = desc.strip()
				anuncio['description'] = desc
				
				if len(anuncio['description']) < 2:
					anuncio['description'] = ''
				
				areaInfo = anuncio_url.xpath('.//div[contains(@class,"map_objet_infos_top")]//ul')
				
				anuncio['rooms_qty'] = areaInfo.xpath('./li[1]/text()').extract_first()
				anuncio['surface_inner'] = areaInfo.xpath('./li[2]/text()').extract_first()
				anuncio['price'] = areaInfo.xpath('./li[3]/text()').extract_first()

				anuncio['charges'] = None

				if anuncio['price'] is None:
					anuncio['price'] = None
				
				anuncio['floor_qty'] = None

				title_list = anuncio_url.xpath('.//div[contains(@class,"map_objet_shortdesc")]/strong[not(re:test(.,"\w[\s]?\:"))]/text()').extract()
				title = ''
				for t in title_list:
					title += t + ' '
				
				title = title.strip()

				anuncio['title'] = title

				anuncio['available_date'] = anuncio_url.xpath('.//div[contains(@class,"map_objet_shortdesc")]').xpath('normalize-space()').re_first(r'[dD]isponibilit.[\s]?\:.*?(\d{2}[\.\/]\d{2}[\.\/]\d{4})')
				
				imgs = anuncio_url.xpath('.//div[contains(@class,"map_objet_image")][contains(@style,"background")]/@style').re(r'\([\'\"](.*?)[\'\"]\)')
				url_imgs = []
				if len(imgs):
					for img in imgs:
						url_img = re.sub('thumbnail','full', img)
						url_imgs.append(url_img)

				anuncio['url_imgs'] = url_imgs

				anuncio['address'] = anuncio_url.xpath('.//div[contains(@class,"map_objet_shortdesc")]').xpath('normalize-space()').re_first(r'.*?\s\-\s.*?\s(.*?)[dD]isponibilit.')
				
				features_final = []
				features = []
				
				for feature in features:
					if len(feature) > 0:
						features_final.append(feature)

				anuncio['features'] = []
				if features_final is not None and len(features_final) > 0:
					anuncio['features'] = features_final

				anuncio['announcer'] = None
				anuncio['announcer_site'] = None 

				anuncio['contact_phone'] = []
				c_name = anuncio_url.xpath('.//div[contains(@class,"map_objet_bottom_left")]').xpath('normalize-space()').re_first(r'[cC]ontact[\s]?\:(.*?)(t.l|\+)')
				if c_name is not None:
					c_name.strip()
				anuncio['contact_name'] = c_name

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

				anuncios.append(anuncio)

		return anuncios
