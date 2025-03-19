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

class TuttiSpider(scrapy.Spider):
	name = "tutti"
	#start_urls = ['https://www.homegate.ch/fr']
	download_delay = 5

	custom_settings = {
		'ROBOTSTXT_OBEY': False
	}

	def __init__(self, max_page=0, *args, **kwargs):
		super(TuttiSpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	#Funcao com inicial que parseia as urls iniciais a partir do csv
	#Dependendo do robô pode ser feito de modo implicito
	def start_requests(self):
		#analisar se nao vale a pena carregar tudo na variavel e fechar arquivo e depois ir nos csvs
		#with open('homegate_start_url.csv') as f:
		#	reader = csv.DictReader(f)
		reader = []

		reader.append({'start_url':'https://www.tutti.ch/fr/li/geneve/geneve/offres/immobilier/appartements/louer?query_lang=fr&redirect=platform', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'apartment'})
		reader.append({'start_url':'https://www.tutti.ch/fr/li/geneve/geneve/offres/immobilier/maisons/louer?query_lang=fr&redirect=platform', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'house'})
		reader.append({'start_url':'https://www.tutti.ch/fr/li/geneve/geneve/immobilier/objets-commerciaux/louer?query_lang=fr&redirect=platform', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'commercial', 'type_of_property':''})
		
		reader.append({'start_url':'https://www.tutti.ch/fr/li/geneve/geneve/offres/immobilier/appartements/acheter?query_lang=fr&redirect=platform', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'apartment'})
		reader.append({'start_url':'https://www.tutti.ch/fr/li/geneve/geneve/offres/immobilier/maisons/acheter?query_lang=fr&redirect=platform', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'house'})
		reader.append({'start_url':'https://www.tutti.ch/fr/li/geneve/geneve/offres/immobilier/objets-commerciaux/acheter?query_lang=fr&redirect=platform', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'commercial', 'type_of_property':''})

		for row in reader:
			yield scrapy.Request(row['start_url'], self.parse,errback=self.errback_httpbin,meta={'dado': row, 'count': 1})

	#Pagina com a lista de links
	def parse(self, response):
		logging.warning("Iniciando url: " + response.url)
		anuncios_url = response.xpath('//div[contains(@class, "_1MojO _1ew6U _391iy _8fEqk")]/a')

		for anuncio_url in anuncios_url:
			#url = response.urljoin(anuncio_url.xpath('.//a[contains(@class,"link")]/@href').extract_first())
			url = 'https://www.tutti.ch' + anuncio_url.xpath('./@href').extract_first()
			#url = re.sub(r'(\/)$', '', url)
			#cod = re.sub(r'.*\_','',url)
			#cod = re.sub(r'\.\w{3,4}','',cod)

			#r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod)

			#logging.warning("resposta requisicao cod: " + cod)
			
			#if r_cod.status_code == 200 and int(r_cod.text) == 0:
			#	logging.warning('anuncio não existe no servidor então capturar!')
			yield scrapy.Request(url, callback=self.parse_contents,errback=self.errback_httpbin, meta={'dado': response.meta['dado']})
		

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
		check_next_page = response.xpath('//li[contains(@class, "_3bpXO")]//div//span')
		if len(check_next_page) > 0:
			next_page = response.xpath('//li[contains(@class, "_3bpXO")]//div//span')[3]

		count = int(response.meta['count'])
		
		# Verifica se existe o objeto next_page
		if next_page is not None:
			print("count " + str(response.meta['count'] + 1))
			if (count < self.max_page and self.max_page !=0) or (self.max_page == 0):
				print("Indo para pagina: " + str(count + 1))
				next_page = response.url + '&o=' + str(int(count) + 1)
				yield scrapy.Request(next_page, callback=self.parse,errback=self.errback_httpbin, meta={'dado': response.meta['dado'], 'count': (count+1)})
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

		'''
		anuncio['cod_anuncio'] = re.sub('.*/','', response.url)

		cod = response.xpath('//td[re:test(.,"R.f.rence: ")]').xpath('normalize-space()').re_first(r'R.f.rence: (\d+)')
		if cod is not None:
			anuncio['cod_anuncio'] = cod
						
		anuncio['description'] = response.xpath('//table[contains(@class,"_1b_sF")]//tr[contains(@class, "FnIV_")][2]//td').xpath('normalize-space()').extract_first()
		
		anuncio['rooms_qty'] = response.xpath('//table[contains(@class, "_1b_sF")]//td[re:test(.,"Zimmer|Pièces")]').xpath('normalize-space()').re_first(r'\d.*')
		anuncio['floor_qty'] = None
		anuncio['surface_inner'] = response.xpath('//table[contains(@class, "_1b_sF")]//td[re:test(.,"Fläche|Surface")]').xpath('normalize-space()').re_first(r'\d+')
		anuncio['address'] = response.xpath('//table[contains(@class, "_1b_sF")]//td[re:test(.,"[aA]dresse")]//dd').xpath('normalize-space()').extract_first()
	
		anuncio['title'] = response.xpath('//div[contains(@class, "_2nBz3 _1HElo _1HElo")]//h1').xpath('normalize-space()').extract_first()
		
		price = None
		price = response.xpath('//table[contains(@class, "_1b_sF")]//td[re:test(.,"CHF")]//dd').xpath('normalize-space()').extract_first()
		
		if price is not None:
			price = re.sub(r'\D+', '', price)
		
		anuncio['price'] = price
		
		anuncio['charges'] = None

		#imgs = response.xpath('//ul[contains(@id,"thumbs_list")]/li/img/@src').extract()
		url_imgs = []
		#if len(imgs):
		#	for img in imgs:
		#		url = re.sub(r'thumbs','images',img)
		#		url_imgs.append(url)

		anuncio['url_imgs'] = url_imgs
		
		#for feature in features:
		#	if len(feature) > 0:
		#		features_final.append(feature)

		anuncio['features'] = []
		#if features_final is not None and len(features_final) > 0:
		#	anuncio['features'] = features_final

		anuncio['available_date'] = None

		anuncio['announcer'] = 'Tutti Immobilier'
		anuncio['announcer_site'] = None 

		anuncio['contact_phone'] = []
		anuncio['contact_name'] = None

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
		'''
		anuncio['cod_anuncio'] = re.sub('.*/','', response.url)

		cod = response.xpath('//td[re:test(.,"R.f.rence: ")]').xpath('normalize-space()').re_first(r'R.f.rence: (\d+)')
		if cod is not None:
			anuncio['cod_anuncio'] = cod
						
		anuncio['description'] = response.xpath('//tr//td[contains(@class, "_3E1vH _100oN _3MSKw")]').xpath('normalize-space()').extract_first()
		
		anuncio['rooms_qty'] = response.xpath('//td[re:test(.,"Zimmer|Pièces")]').xpath('normalize-space()').re_first(r'\d.*')
		anuncio['floor_qty'] = None
		anuncio['surface_inner'] = response.xpath('//table//td[re:test(.,"Fläche|Surface")]').xpath('normalize-space()').re_first(r'\d+')
		
		address = []

		address2 = response.xpath('//table//td[re:test(.,"[aA]dresse")]//dd').xpath('normalize-space()').extract_first()

		if address2 is not None:
			address.append(address2)

		address3 = response.xpath('//table//td[re:test(.,"[dD]istrict")]//dd').xpath('normalize-space()').extract_first()

		if address3 is not None:
			address.append(address3)

		address4 = response.xpath('//table//td[re:test(.,"[nN][pP][aA]")]//dd').xpath('normalize-space()').extract_first()

		if address4 is not None:
			address.append(address4)

		if len(address) > 1:
			address = ', '.join(address)
		else:
			address = ''.join(address)

		anuncio['address'] = address
		
		title =  response.xpath('//h1/text()').extract_first()

		title2 =  response.xpath('//h2/text()').extract_first()

		if title2 is not None:
			title = title + ', ' + title2

		anuncio['title'] = title
		
		price = response.xpath('//table//td[re:test(.,"CHF")]//dd').xpath('normalize-space()').extract_first()
		
		if price is not None:
			price = re.sub(r'\D+', '', price)
		
		anuncio['price'] = price
		
		anuncio['charges'] = None

		#imgs = response.xpath('//ul[contains(@id,"thumbs_list")]/li/img/@src').extract()
		url_imgs = []
		#if len(imgs):
		#	for img in imgs:
		#		url = re.sub(r'thumbs','images',img)
		#		url_imgs.append(url)

		anuncio['url_imgs'] = url_imgs
		
		#for feature in features:
		#	if len(feature) > 0:
		#		features_final.append(feature)

		anuncio['features'] = []
		#if features_final is not None and len(features_final) > 0:
		#	anuncio['features'] = features_final

		anuncio['available_date'] = None

		anuncio['announcer'] = 'Tutti Immobilier'
		anuncio['announcer_site'] = None 

		anuncio['contact_phone'] = []
		anuncio['contact_name'] = None

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
