# -*- coding: utf-8 -*-
import scrapy
from onecontact.items import OnecontactItem
import re
import logging
import requests

# erros libs
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError


# Immobilier commercial
class Immobilier2Spider(scrapy.Spider):
    name = "immobilier2"
    download_delay = 5

    def __init__(self, max_page=1, *args, **kwargs):
        super(Immobilier2Spider, self).__init__(*args, **kwargs)
        self.max_page = int(max_page)

    # Dependendo do robô pode ser feito de modo implicito
    def start_requests(self):

        reader = []
        # Genève
        # rent
        reader.append({
            'start_url': 'https://www.immobilier.ch/fr/carte/louer/commercial/geneve/page-1?t=rent&c=4&p=s40&nb=false',
            'state': 'Genève',
            'type_of_transaction': 'rent',
            'nature_of_property': 'commercial',
            'type_of_property': ''
        })  # Commercial

        reader.append({
            'start_url': 'https://www.immobilier.ch/fr/carte/louer/bureau/geneve/page-1?t=rent&c=5&p=s40&nb=false',
            'state': 'Genève',
            'type_of_transaction': 'rent',
            'nature_of_property': 'commercial',
            'type_of_property': 'bureau'
        })  # Commercial
        reader.append({
            'start_url': 'https://www.immobilier.ch/fr/carte/louer/industriel/geneve/page-1?t=rent&c=7&p=s40&nb=false',
            'state': 'Genève',
            'type_of_transaction': 'rent',
            'nature_of_property': 'commercial',
            'type_of_property': ''
        })  # Commercial

        # sell
        reader.append({
            'start_url': 'https://www.immobilier.ch/fr/carte/acheter/commercial/geneve/page-1?t=sale&c=4&p=s40&nb=false',
            'state': 'Genève',
            'type_of_transaction': 'sell',
            'nature_of_property': 'commercial',
            'type_of_property': ''
        })  # Commercial
        reader.append({
            'start_url': 'https://www.immobilier.ch/fr/carte/acheter/bureau/geneve/page-1?t=sale&c=5&p=s40&nb=false',
            'state': 'Genève',
            'type_of_transaction': 'sell',
            'nature_of_property': 'commercial',
            'type_of_property': 'bureau'
        })  # Commercial
        reader.append({
            'start_url': 'https://www.immobilier.ch/fr/carte/acheter/industriel/geneve/page-1?t=sale&c=7&p=s40&nb=false',
            'state': 'Genève',
            'type_of_transaction': 'sell',
            'nature_of_property': 'commercial',
            'type_of_property': ''
        })  # Commercial

        logging.warning("Iniciando start urls...")

        for row in reader:
            yield scrapy.Request(
                row['start_url'],
                self.parse,
                errback=self.errback_httpbin,
                meta={'dado': row, 'count': 1}
            )

    # Pagina com a lista de links
    def parse(self, response):
        logging.warning("Iniciando url: " + response.url)
        # anuncios_url = response.xpath('//div[contains(@class,"filter-results")]/div[not(contains(@id, "city-guide"))][contains(@id,"item")]')
        anuncios_url = response.xpath(
            '//div[contains(@class, "filter-results-holder")]//div[contains(@class, "filter-item")]//@href').extract()
        count_item = 1;
        logging.warning("Quantidade de item no link: " + str(len(anuncios_url)))

        for anuncio_url in anuncios_url:
            # url = anuncio_url.xpath('./a[re:test(@category, "([lL]ocation|[vV]ente)")]/@href').extract_first()
            url = response.urljoin(anuncio_url)
            # cod = re.sub(r'(\/)$','',url)
            # cod = re.sub(r'.*?\-\-','',cod)
            # logging.warning("Checando se anuncio ja existe.")
            # r_cod = requests.get('https://1contact.ch/api/object/exist/' + cod)

            # if r_cod.status_code == 200:
            #	logging.warning("Datas estao ok e anuncio nao existe no servidor entao ir capturar!")
            # logging.warning("Nao possui codigo para checar então capturar todos!")
            # logging.warning('anuncio: ' + str(count_item))
            count_item += 1
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
        atual_page = response.xpath('//ul[contains(@class, "pages")]//li[contains(@class, "selected")]').xpath(
            'normalize-space()').extract_first()
        count = int(response.meta['count'])

        # Verifica se existe o objeto next_page
        if atual_page is not None:
            atual_page = int(atual_page)
            print("count " + str(response.meta['count'] + 1))
            if (count < self.max_page and self.max_page != 0) or (self.max_page == 0):
                nb_page = response.xpath(
                    '//ul[contains(@class, "pages")]//li[re:test(.,"' + str(atual_page + 1) + '")]').xpath(
                    'normalize-space()').extract_first()
                if nb_page is not None:
                    print("Indo para pagina: " + str(count + 1))
                    next_page = response.meta['dado']['start_url'] + '-' + nb_page
                    yield scrapy.Request(
                        next_page,
                        callback=self.parse,
                        errback=self.errback_httpbin,
                        meta={'dado': response.meta['dado'], 'count': (count + 1)}
                    )
            else:
                next_page = None

    # Pagina com todos campos que vao ser inseridos no robô
    def parse_contents(self, response):
        logging.warning('Iniciando captura item...')
        anuncio = OnecontactItem()
        anuncio['name'] = self.name
        anuncio['country'] = 'Switzerland'
        anuncio['url_anuncio'] = response.url

        # dados inseridos do csv
        anuncio['type_of_transaction'] = response.meta['dado']['type_of_transaction']
        anuncio['state'] = response.meta['dado']['state']
        anuncio['nature_of_property'] = response.meta['dado']['nature_of_property']  # residential | commercial
        anuncio['type_of_property'] = response.meta['dado']['type_of_property']

        anuncio['title'] = response.xpath('//div[contains(@class,"Content__body")]/h2/text()').extract_first()

        if anuncio['title'] is not None:
            if len(anuncio['title']) > 100:
                anuncio['title'] = response.xpath('//header/h1/text()').extract_first()

        areaDetalhe = response.xpath(
            '//div[contains(@class,"im__assets__table")][preceding-sibling::header/h2[re:test(.,"[aA] propos de")]][1]')

        price = areaDetalhe.xpath('.//li//span[re:test(.,"[lL]oyer")]').xpath('normalize-space()').extract_first()
        if price is None:
            price = response.xpath('//div[contains(@class,"price")]/span[contains(@class,"postDetails__price")]').xpath(
                'normalize-space()').re_first(r'[pP]rix[\s]?\:[\s]?(.*)')

        if price is not None:
            price = re.sub(r'[lL]oyer[\s]?\:', '', price)
            price = price.strip()
        else:
            price = 0

        anuncio['price'] = price

        charges = areaDetalhe.xpath('.//li//span[re:test(.,"[cC]harge")]').xpath('normalize-space()').extract_first()

        if charges is not None:
            charges = re.sub(r'[cC]harge.*?\:', '', charges)
            charges = charges.strip()
        else:
            charges = None

        anuncio['charges'] = charges

        anuncio['rooms_qty'] = areaDetalhe.xpath(
            './/li[re:test(.,"pi.ces")]/span/span[re:test(.,"pi.ces")]/text()').re_first(r'\d+')

        anuncio['surface_inner'] = areaDetalhe.xpath('.//li/span/span[re:test(.,"\d+[\s]?m")]/text()').extract_first()
        anuncio['floor_number'] = areaDetalhe.xpath('.//li/span/span[re:test(.,".tage")]/text()').re_first(r'\d+')

        anuncio['cod_anuncio'] = areaDetalhe.xpath('.//li/span/span[re:test(.,"[rR].f.rence")]/text()').re_first(
            '[rR].f.rence[\s]?(.*)')
        anuncio['cod_anuncio'] = anuncio['cod_anuncio'].strip()

        logging.warning('Capturando com codigo item: ' + str(anuncio['cod_anuncio']))
        logging.warning('Start_url: ' + response.url)

        anuncio['description'] = response.xpath('//div[contains(@class,"postContent__body")]/p').xpath(
            'normalize-space()').extract_first()
        anuncio['available_date'] = None

        if anuncio['description'] is None:
            anuncio['description'] = ''
        elif len(anuncio['description']) < 2:
            anuncio['description'] = ''

        anuncio['address'] = areaDetalhe.xpath(
            './/li/span/span[re:test(.,"([rR]ue|[cC]hemin|[rR]oute|[aA]venue)")]/text()').extract_first()

        if anuncio['address'] is None:
            anuncio['address'] = areaDetalhe.xpath('.//li[2]/span/span/text()').extract_first()

        if anuncio['address'] is not None:
            anuncio['address'] = anuncio['address'].strip()
            a2 = areaDetalhe.xpath('.//li[2]/span/span/br/following-sibling::text()').extract_first()
            if a2 is not None:
                a2 = a2.strip()
                if a2 is not '':
                    anuncio['address'] = anuncio['address'] + ', ' + a2

        imgs = response.xpath('//div[contains(@class,"im__banner")][.//figure]//img/@data-lazy').extract()
        for i in range(0, len(imgs)):
            imgs[i] = response.urljoin(imgs[i])

        anuncio['url_imgs'] = imgs

        areaFeatures = response.xpath(
            '//div[contains(@class,"im__assets__table")][preceding-sibling::header/h2[re:test(.,".quipement")]][1]')
        anuncio['features'] = areaFeatures.xpath('.//li/span/span').xpath('normalize-space()').extract()

        if len(anuncio['features']) > 0:
            for i in range(0, len(anuncio['features'])):
                anuncio['features'][i] = anuncio['features'][i].strip()

        contacts = response.xpath('//a[contains(@phone-for, "Agence")]/@data-tel-num').extract()
        if len(contacts) > 1:
            contacts = []
            contacts.append(response.xpath('//a[contains(@phone-for, "Agence")]/@data-tel-num').extract()[1])

        anuncio['contact_phone'] = contacts
        anuncio['contact_name'] = None

        anuncio['announcer'] = response.xpath(
            '//div[contains(@class,"postDetails__contact")]/address/strong/text()').extract_first()
        anuncio['announcer_site'] = None

        anuncio['viewing_phone_number'] = []
        anuncio['viewing_desc'] = response.xpath('//li[contains(@class,"address-info visit")]/address').xpath(
            'normalize-space()').extract_first()

        # campos qty number
        anuncio['bedrooms_qty'] = None
        anuncio['toilets_qty'] = None
        anuncio['bathrooms_qty'] = None
        anuncio['surface_outer'] = None
        anuncio['floor_qty'] = None

        # tipos: rent | owner | professional
        anuncio['type_of_announcer'] = None

        # --------------------------------------------
        # address - string campo
        # --------------------------------------------
        anuncio['street_number'] = None
        anuncio['route'] = None
        anuncio['complement'] = None
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
