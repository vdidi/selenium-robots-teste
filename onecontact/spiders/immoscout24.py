# -*- coding: utf-8 -*-
import csv
import logging
import re

import requests
import scrapy

# erros libs
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TCPTimedOutError, TimeoutError

from onecontact.items import OnecontactItem


class Immoscout24Spider(scrapy.Spider):
    name = "immoscout24"
    # start_urls = ['https://www.homegate.ch/fr']
    download_delay = 5

    def __init__(self, max_page=4, *args, **kwargs):
        super(Immoscout24Spider, self).__init__(*args, **kwargs)
        self.max_page = int(max_page)

    # Funcao com inicial que parseia as urls iniciais a partir do csv
    # Dependendo do robô pode ser feito de modo implicito
    def start_requests(self):
        # analisar se nao vale a pena carregar tudo na variavel e fechar arquivo e depois ir nos csvs
        # with open('homegate_start_url.csv') as f:
        # 	reader = csv.DictReader(f)
        reader = []

        # Genève
        reader.append(
            {
                "start_url": "https://www.immoscout24.ch/fr/appartement/louer/lieu-geneve?se=16",
                "state": "Genève",
                "type_of_transaction": "rent",
                "nature_of_property": "residential",
                "type_of_property": "appartement",
            }
        )
        reader.append(
            {
                "start_url": "https://www.immoscout24.ch/fr/maison/louer/lieu-geneve?se=16",
                "state": "Genève",
                "type_of_transaction": "rent",
                "nature_of_property": "residential",
                "type_of_property": "house",
            }
        )
        reader.append(
            {
                "start_url": "https://www.immoscout24.ch/fr/bureau-commerce-industrie/louer/lieu-geneve?se=16",
                "state": "Genève",
                "type_of_transaction": "rent",
                "nature_of_property": "commercial",
                "type_of_property": "",
            }
        )

        # sell
        reader.append(
            {
                "start_url": "https://www.immoscout24.ch/fr/appartement/acheter/lieu-geneve?se=16",
                "state": "Genève",
                "type_of_transaction": "sell",
                "nature_of_property": "residential",
                "type_of_property": "appartement",
            }
        )
        reader.append(
            {
                "start_url": "https://www.immoscout24.ch/fr/maison/acheter/lieu-geneve?se=16",
                "state": "Genève",
                "type_of_transaction": "sell",
                "nature_of_property": "residential",
                "type_of_property": "house",
            }
        )
        reader.append(
            {
                "start_url": "https://www.immoscout24.ch/fr/bureau-commerce-industrie/acheter/lieu-geneve?se=16",
                "state": "Genève",
                "type_of_transaction": "sell",
                "nature_of_property": "commercial",
                "type_of_property": "",
            }
        )

        for row in reader:
            yield scrapy.Request(
                row["start_url"],
                self.parse,
                errback=self.errback_httpbin,
                meta={"dado": row, "count": 1},
                headers= {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "max-age=259200",
                    "Forwarded": "for=23.236.230.6;proto=http",
                    "Host": "httpbin.scrapinghub.com",
                    "Sec-Ch-Ua": "\" Not;A Brand\";v=\"99\", \"Google Chrome\";v=\"91\", \"Chromium\";v=\"91\"",
                    "Sec-Ch-Ua-Mobile": "?1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; moto g(9) play) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
                }
            )

    # Pagina com a lista de links
    def parse(self, response):
        logging.warning("Iniciando url: " + response.url)
        anuncios_url = response.xpath('//div[@role="listitem"]/div/a/@href').extract()

        for anuncio_url in anuncios_url:
            url = response.urljoin(anuncio_url)
            yield scrapy.Request(
                url,
                headers= {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "max-age=259200",
                    "Forwarded": "for=23.236.230.6;proto=http",
                    "Host": "httpbin.scrapinghub.com",
                    "Sec-Ch-Ua": "\" Not;A Brand\";v=\"99\", \"Google Chrome\";v=\"91\", \"Chromium\";v=\"91\"",
                    "Sec-Ch-Ua-Mobile": "?1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; moto g(9) play) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
                },
                callback=self.parse_contents,
                errback=self.errback_httpbin,
                meta={"dado": response.meta["dado"]},
            )
        # 	-------------------------------------------------------------------------------------------------
        # 	|	PAGINACAO
        # 	|	Paginacao condicional se especificado o valor maximo de página em 'max_page' argumento
        # 	-------------------------------------------------------------------------------------------------
        next_page = response.xpath('//a[contains(@class, "HgPaginationSelector_nextPreviousArrow")]/@href').extract_first()
        count = int(response.meta['count'])

		# Verifica se existe o objeto next_page
        if next_page is not None:
            if (count < self.max_page and self.max_page != 0) or (self.max_page == 0):
                next_page = re.sub('se=16','pn=' + str(count+1), response.url)
                yield scrapy.Request(
                    next_page,
                    headers= {
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Cache-Control": "max-age=259200",
                        "Forwarded": "for=23.236.230.6;proto=http",
                        "Host": "httpbin.scrapinghub.com",
                        "Sec-Ch-Ua": "\" Not;A Brand\";v=\"99\", \"Google Chrome\";v=\"91\", \"Chromium\";v=\"91\"",
                        "Sec-Ch-Ua-Mobile": "?1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "same-origin",
                        "Sec-Fetch-User": "?1",
                        "Upgrade-Insecure-Requests": "1",
                        "User-Agent": "Mozilla/5.0 (Linux; Android 10; moto g(9) play) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
                    },
                    callback=self.parse_contents,
                    errback=self.errback_httpbin,
                    meta={"dado": response.meta["dado"]},
                )

    # Pagina com todos campos que vao ser inseridos no robô
    def parse_contents(self, response):
        anuncio = OnecontactItem()
        
        areaInfo = response.xpath(
            '//*[@id="app"]/main/div/div[2]/div/div[1]/div[2]/div[1]/div[3]/section[1]/div[1]/h1'
        )

        anuncio["announcer"] = areaInfo.xpath("./h1").extract_first()

        if (
            anuncio["announcer"] is not None
            and not re.search(r"1Contact\sS", anuncio["announcer"])
        ) or anuncio["announcer"] is None:
            anuncio["name"] = self.name
            anuncio["country"] = "Switzerland"
            anuncio["url_anuncio"] = response.url

            # dados inseridos do csv
            anuncio["type_of_transaction"] = response.meta["dado"][
                "type_of_transaction"
            ]
            anuncio["state"] = response.meta["dado"]["state"]
            anuncio["nature_of_property"] = response.meta["dado"][
                "nature_of_property"
            ]  # residential | commercial
            anuncio["type_of_property"] = response.meta["dado"]["type_of_property"]

            # anuncio['cod_anuncio'] = response.xpath('//*[@id="app"]/main/div/div[2]/div/div[1]/div[2]/div[1]/div[3]/section[1]/dl/dd/text()').extract_first()
            anuncio["cod_anuncio"] = response.xpath(
                '//dl[re:test(., "[aA]nnonce")]//dd/text()'
            ).extract_first()
            anuncio["description"] = response.xpath(
                '//*[@id="app"]/main/div/div[2]/div/div[1]/div[2]/div[1]/div[3]/section[1]/section/div/text()'
            ).extract_first()

            if anuncio["description"] is None:
                anuncio["description"] = ""

            if len(anuncio["description"]) < 2:
                anuncio["description"] = ""

            anuncio["rooms_qty"] = response.xpath(
                'normalize-space(//*[@id="app"]/main/div/div[2]/div/div[1]/div[2]/div[1]/div[3]/section[1]/div[1]/div/div[1]/div[2]/text())'
            ).extract_first()
            # ToDo ajustar problema de ASCII characters
            # anuncio["floor_number"] = response.xpath('//tr[./td[1][re:test(.,"[eEéÉ]tage")]]/td[2]/text()').re_first("\d+")
            anuncio["floor_number"] = response.xpath('//tr[./td[1][re:test(.,".tage")]]/td[2]/text()').re_first(r"\d+")
            anuncio["surface_inner"] = (
                response.xpath(
                    '//*[@id="app"]/main/div/div[2]/div/div[1]/div[2]/div[1]/div[3]/section[1]/div[1]/div/div[2]/div[2]'
                )
                .xpath("normalize-space()")
                .re_first(r"\d+.")
            )
            # ToDo
            anuncio["available_date"] = response.xpath(
                '//tr[./td[1][re:test(.,"[dD]isponibilit")]]/td[2]/text()'
            ).re_first(r"(\d+[\.\/\-]\d+[\/\-\.]\d+)")

            anuncio["title"] = response.xpath(
                '//div[contains(@class, "spotlight-components")]/h1/text()'
            ).extract_first()

            price = response.xpath(
                '//div[contains(@class, "SpotlightAttributesPrice_priceItem")]//span'
            ).extract()
            if price is not None and len(price) > 1:
                price = response.xpath(
                    '//div[contains(@class, "SpotlightAttributesPrice_priceItem")]//span'
                ).extract()[1]
                price = re.sub(r"\D+", "", price)
            else:
                price = None

            anuncio["price"] = price
            charges = response.xpath(
                '//div[contains(@data-test, "costs")]//dd[2]//span/text()'
            ).extract()

            if len(charges) > 1:
                charges = response.xpath(
                    '//div[contains(@data-test, "costs")]//dd[2]//span/text()'
                ).extract()[1]
                charges = re.sub(r"\D+", "", charges)
            else:
                charges = None

            anuncio["charges"] = charges

            anuncio["url_imgs"] = response.xpath(
                '//div[contains(@class, "ImageGallery_slider")]//img/@src'
            ).extract()

            address = response.xpath(
                '//div[contains(@class, "AddressDetails_address")]//span/text()'
            ).extract()
            anuncio["address"] = "".join(address)

            areaInfo = response.xpath('//article[./h2[re:test(.,"[aA]nnonce")]]')
            # ?? anuncio = response.xpath('//h1[contains(@class, "ListingTitle_spotlightTitle")]/text()').extract_first()
            anuncio["announcer"] = "Immo Scout24"
            anuncio["announcer_site"] = areaInfo.xpath(
                './table//a[re:test(.,"[sS]ite web de")]/@href'
            ).extract_first()
            
            contact_phone = []

            # phone = response.xpath(
            #     '//div[contains(@class, "PhoneNumber_buttonDefault")]//a/@href'
            # ).extract_first()
            # if phone is not None:
            #     phone = re.sub(r"tel:\+", "", phone)
                
            #TODO ajustar lista de phones
            anuncio["contact_phone"] = contact_phone
            anuncio["contact_name"] = None

            areaVisite = response.xpath(
                '//div[contains(@class,"contact-tour content")]'
            )

            anuncio["viewing_phone_number"] = areaVisite.xpath(
                './/div[contains(@class,"textlist")]/ul/li[contains(@class,"labeled-text")]/span/text()'
            ).extract()
            if (
                anuncio["contact_phone"] is None
                and anuncio["viewing_phone_number"] is not None
            ):
                anuncio["contact_phone"] = anuncio["viewing_phone_number"]

            anuncio["viewing_desc"] = areaVisite.xpath(
                './/div[contains(@class,"textlist")]/ul/li[2]/text()'
            ).extract_first()
            # TODO
            anuncio['features'] = []
            # campos qty number
            anuncio["bedrooms_qty"] = None
            anuncio["toilets_qty"] = None
            anuncio["bathrooms_qty"] = None
            anuncio["floor_qty"] = None
            anuncio["surface_outer"] = None

            # tipos: rent | owner | professional
            anuncio["type_of_announcer"] = None

            # --------------------------------------------
            # address - string campo
            # --------------------------------------------
            anuncio["street_number"] = None
            anuncio["route"] = None
            anuncio["complement"] = None
            anuncio["neighborhood"] = None
            anuncio["city"] = None
            anuncio["postal_code"] = None

            yield anuncio

    def errback_httpbin(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can extract_first the non-200 response
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error("DNSLookupError on %s", request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error("TimeoutError on %s", request.url)
