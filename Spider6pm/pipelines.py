# -*- coding: utf-8 -*-
import pymongo
from scrapy.exceptions import DropItem


class Spider6PmPipeline(object):
    def process_item(self, item, spider):
        return item


class MongoDBPipeline(object):
    def __init__(self):
        client = pymongo.MongoClient('localhost', 27017)
        db = client['6pm']
        self.Spider6PmItem = db['products']
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['productId'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            try:
                self.Spider6PmItem.insert(item)
            except:
                pass
            self.ids_seen.add(item['productId'])
        return item
