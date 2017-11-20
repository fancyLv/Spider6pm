# -*- coding: utf-8 -*-

import scrapy


class Spider6PmItem(scrapy.Item):
    brandName = scrapy.Field()  # 商品品牌
    productId = scrapy.Field()  # 标题商品id
    productName = scrapy.Field()  # 标题
    description = scrapy.Field()  # 产品信息
    skus = scrapy.Field()  # skus，包括每个 SKU 的属性，价格，库存，图片，链接
