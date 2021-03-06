# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo

from scrapy.conf import settings
from scrapy.exceptions import DropItem
from scrapy import log
from SearchIndex import SearchIndex
from pybloomfilter import BloomFilter

class MongoDBPipeline(object):

    def __init__(self):
        connection = pymongo.MongoClient(
            settings['MONGODB_SERVER'],
            settings['MONGODB_PORT']
        )
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_COLLECTION']]
        self.bf = BloomFilter(10000000, 0.01, 'filter.bloom')
        self.si = SearchIndex()
        self.si.SearchInit()
        
    def process_item(self, item, spider):
        if self.bf.add(item['link']):#True if item in the BF
            raise DropItem("Duplicate item found: %s" % item)
        else:
            for data in item:
                if not data:
                    raise DropItem("Missing data!")
            self.collection.update({'link': item['link']}, dict(item), upsert=True)
            log.msg("Question added to MongoDB database!",level=log.DEBUG, spider=spider)
            self.si.AddIndex(item)
            return item
        
    def __del__(self):
        self.si.IndexDone()
