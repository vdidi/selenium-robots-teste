# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem

class OnecontactPipeline(object):
	def process_item(self, item, spider):
		if item['cod_anuncio'] and item['url_anuncio'] and item['name']:
			return item
		else:
			raise DropItem("Faltando cod_anuncio in %s" % item)
