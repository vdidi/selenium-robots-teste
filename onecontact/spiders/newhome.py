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

class NewhomeSpider(scrapy.Spider):
	name = "newhome"
	download_delay = 3

	def __init__(self, max_page=0, *args, **kwargs):
		super(NewhomeSpider, self).__init__(*args, **kwargs)
		self.max_page = int(max_page)

	def start_requests(self):

		headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}

		reader = []

		#Genève
		reader.append({'start_url':'https://www.newhome.ch/fr/louer/recherche/appartement/localite-geneve/liste.aspx?pc=new', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'apartment'})
		reader.append({'start_url':'https://www.newhome.ch/fr/louer/recherche/maison/localite-geneve/liste.aspx?pc=new', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'residential', 'type_of_property':'house'})
		reader.append({'start_url':'https://www.newhome.ch/fr/louer/recherche/commerce/localite-geneve/liste.aspx?pc=new', 'state': 'Genève', 'type_of_transaction': 'rent', 'nature_of_property':'commercial', 'type_of_property':''})
		
		reader.append({'start_url':'https://www.newhome.ch/fr/acheter/recherche/appartement/localite-geneve/liste.aspx?pc=new', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'apartment'})
		reader.append({'start_url':'https://www.newhome.ch/fr/acheter/recherche/maison/localite-geneve/liste.aspx?pc=new', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'residential', 'type_of_property':'house'})
		reader.append({'start_url':'https://www.newhome.ch/fr/acheter/recherche/commerce/localite-geneve/liste.aspx?pc=new', 'state': 'Genève', 'type_of_transaction': 'sell', 'nature_of_property':'commercial', 'type_of_property':''})

		for row in reader:
			yield scrapy.Request(row['start_url'], self.parse, meta={'dado': row, 'count': 1}, headers=headers)

	def parse(self, response):
		anuncios_url = response.xpath('//div[contains(@class,"details")][./a]')
		headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
		
		for anuncio_url in anuncios_url:
			url = response.urljoin(anuncio_url.xpath('./a[contains(@href,"detail")][./div[contains(@class,"title")]]/@href').extract_first())
			yield scrapy.Request(
				url, 
				callback=self.parse_contents, 
				errback=self.errback_httpbin,
				meta={'dado': response.meta['dado']}, 
				headers=headers
				)

		next_page = response.xpath('//li[contains(@class,"next pager")][ not(contains(@class,"disabled")) ]/a[ contains(@aria-label,"Next") ]/@href').extract_first()
		
		count = int(response.meta['count'])

		# Verifica se existe o objeto next_page
		if next_page is not None:
			print("count " + str(response.meta['count'] + 1))
			if (count < self.max_page and self.max_page !=0) or (self.max_page == 0):
				print("Indo para pagina: " + str(count + 1))
				yield scrapy.Request(
					next_page, 
					callback=self.parse,
					errback=self.errback_httpbin,
					meta={'dado': response.meta['dado'], 'count': (count+1)}, 
					headers=headers
					)
			else:
				next_page = None


	def parse_contents(self, response):

		anuncio = OnecontactItem()
		anuncio['name'] = self.name
		anuncio['country'] = 'Switzerland'
		anuncio['url_anuncio'] = response.url

		anuncio['type_of_transaction'] = response.meta['dado']['type_of_transaction'] # rent | buy
		anuncio['nature_of_property'] = response.meta['dado']['nature_of_property']   # residential | commercia//l 

		anuncio['description'] = response.xpath('//div[contains(@class,"content-section description")]/div[contains(@class,"row")]').xpath('normalize-space()').extract_first()

		#areaGlance
		areaGlance = response.xpath('//div[contains(@class,"content-section details")]')
		
		immo_code = areaGlance.xpath('.//div[contains(@id,"fiImmocode")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()
		property_code = areaGlance.xpath('.//div[contains(@id,"ctl14_fiObjektnummer")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()
		anuncio['cod_anuncio'] = str(immo_code)

		if property_code is not None and len(property_code) > 0:
			property_code = re.sub('^(\.\.[\.]?)','', property_code)
			anuncio['cod_anuncio'] += '_' + str(property_code)


		cod = anuncio['cod_anuncio']
		r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod)

		logging.warning("resposta requisicao cod: " + cod)
		
		if r_cod.status_code == 200 and int(r_cod.text) == 0:
			logging.warning('anuncio não existe no servidor então capturar!')

			anuncio['type_of_property'] = areaGlance.xpath('//div[contains(@id,"fiUnterobjektart")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()

			anuncio['rooms_qty'] = areaGlance.xpath('.//div[contains(@id,"fiZimmer")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()
			anuncio['floor_qty'] = areaGlance.xpath('.//div[contains(@id,"fiEtagen")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()
			
			price_liquido = areaGlance.xpath('.//div[re:test(@id,"(fiNetto[Mm]ieteProMonat)")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()
			price_mensal = areaGlance.xpath('.//div[re:test(@id,"(fiMieteProMonat)")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()

			if price_liquido != None:
				anuncio['price'] = price_liquido
			elif price_mensal != None:
				anuncio['price'] = price_mensal
			else:
				anuncio['price'] = areaGlance.xpath('.//div[re:test(@id,"(fiMieteProM2ProJahr)")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()


			anuncio['charges'] = areaGlance.xpath('.//div[re:test(@id,"fi[nN]ebenkosten")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()

			anuncio['surface_inner'] = areaGlance.xpath('.//div[contains(@id,"fiWohnflaeche")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()
			anuncio['available_date'] = areaGlance.xpath('.//div[contains(@id,"fiBezug")]/div[contains(@class,"right")]').xpath('normalize-space()').extract_first()

			anuncio['title'] = response.xpath('//h1/span[contains(@itemprop,"name")]/text()').extract_first()

			areaProvider = response.xpath('//div[contains(@id,"ucKontakt_dAnbieterInfo")]')
			
			anuncio['announcer'] = areaProvider.xpath('//span[contains(@id,"ucKontakt_lFirmaName")]/text()').extract_first()
			anuncio['contact_phone'] = areaProvider.xpath('//div[contains(@id,"_ucKontakt_dPhone")]/div[contains(@id,"cphContent")][contains(@id,"ucKontakt_fiTelefon")]//div[contains(@class,"right")]').xpath('normalize-space()').extract()

			anuncio['address'] = response.xpath('//span[contains(@itemprop,"address")]').xpath('normalize-space()').extract_first()

			features_final = response.xpath('//div[contains(@class,"detail-list")]/div[re:test(@id,"(dDetailInnen|dDetailsAussen)")]/div[contains(@class,"row")]/div/div[contains(@id,"cphContent")]').xpath('normalize-space()').extract()

			imgs = response.xpath('//img[contains(@src,"resources")][contains(@src,"bildid")]/@src').extract()
			url_imgs = []
			if imgs is not None and len(imgs):
				for img in imgs:
					uri = re.sub(r"format=2","format=1",img)
					url_imgs.append(uri)

			anuncio['url_imgs'] = url_imgs
			features_final2 = areaGlance.xpath('./div[contains(@class,"detail-list")][contains(@class,"form")]/div/div[contains(@class,"col")]/div[contains(@id,"cphContent")]').xpath('normalize-space()').extract()
			anuncio['features'] = features_final + features_final2
			anuncio['type_of_transaction'] = response.meta['dado']['type_of_transaction'] # rent | buy

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
			anuncio['state'] = 'Genève'
			anuncio['postal_code'] = None

			anuncio['viewing_phone_number'] = []
			anuncio['contact_name'] = None
			anuncio['announcer_site'] = None
			anuncio['viewing_desc'] = None

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
