# -*- coding: utf-8 -*-
import json
import re

from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class Spider6pmSpider(CrawlSpider):
    name = 'spider6pm'
    allowed_domains = ['6pm.com', 'api.zcloudcat.com']
    start_urls = ['https://www.6pm.com/']
    classifyLinkEx = LinkExtractor(allow=r'www\.6pm\.com.+/desc/.+', restrict_css='.header-nav > ul .lists a')
    pageLinkEx = LinkExtractor(allow=r'www\.6pm\.com.+p=\d+', restrict_css='.pagination a')
    productLinkEx = LinkExtractor(allow=r'www\.6pm\.com.+/product/\d+/', restrict_css='#searchResults > a')
    rules = (
        Rule(classifyLinkEx, follow=True),
        Rule(pageLinkEx, follow=True),
        Rule(productLinkEx, follow=True, callback="parse_item"),
    )

    def parse_item(self, response):
        skuId = re.findall('product/(\d+)', response.url)[0] if re.findall('product/(\d+)', response.url) else None
        print skuId
        if not skuId:
            return
        link = 'https://api.zcloudcat.com/v3/productBundle?productId={}&siteId=2&includeImages=true&includeSizing=true&includeBrand=true&includes=[%22preferredSubsite%22]&autolink=[%22description%22,%22brandProductName%22,%22summary%22,%22otherShoes%22]'.format(
            skuId)
        headers = {'Accept': '*/*',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Accept-Language': 'zh-CN,zh;q=0.8',
                   'Connection': 'keep-alive',
                   'Host': 'api.zcloudcat.com',
                   'If-None-Match': "0e04dc6d5c66890e35a6cf2fce5edbd2a",
                   'Origin': 'https://www.6pm.com',
                   'Referer': response.url,
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}

        yield Request(url=link, headers=headers, meta={'defaulturl': response.url}, callback=self.parse_detail)

    def parse_detail(self, response):
        defaulturl = response.meta['defaulturl']
        data = json.loads(response.body_as_unicode())
        if data.get('statusCode') != '200':
            return
        item = dict()
        product = data['product'][0]
        item['brandName'] = product['brandName']
        item['productId'] = product['productId']
        item['productName'] = product['productName']
        item['description'] = product['description']
        sizing = product['sizing']
        dimensionsSet = sizing['dimensionsSet']
        valuesSet = sizing['valuesSet']
        dimensionIdToName = sizing['dimensionIdToName']
        unitIdToName = sizing['unitIdToName']
        valueIdToName = sizing['valueIdToName']
        dimensionIdToUnitId = sizing['dimensionIdToUnitId']

        specName = dict()
        for dimension in dimensionsSet:
            unitId = dimensionIdToUnitId[dimension]
            uname = unitIdToName[unitId]
            dname = dimensionIdToName[dimension].lower().strip()
            specName[dname] = uname

        item['skus'] = list()
        styles = product['styles']
        for style in styles:
            originalPrice = style['originalPrice']
            price = style['price']
            productUrl = style['productUrl']
            color = style['color']
            images = ['https://m.media-amazon.com/images/I/{}._SX480_.jpg'.format(img.get('imageId')) for img in
                      style.get('images')]
            # 初始化库存
            if not dimensionsSet:
                sku = dict()
                sku['originalPrice'] = originalPrice
                sku['price'] = price
                sku['productUrl'] = re.sub('/product/.+', productUrl, defaulturl)
                sku['color'] = color
                sku['images'] = images
                sku['stock'] = 'out of stock'
                item['skus'].append(sku)
            elif len(dimensionsSet) == 1:
                dimensionId = dimensionsSet[0]
                unitId = dimensionIdToUnitId[dimensionId]
                unitName = unitIdToName[unitId]
                if valuesSet[dimensionId][unitId]:
                    for value in valuesSet[dimensionId][unitId]:
                        sku = dict()
                        sku[unitName] = valueIdToName[value]['value']
                        sku['stock'] = 'out of stock'
                        sku['originalPrice'] = originalPrice
                        sku['price'] = price
                        sku['productUrl'] = re.sub('/product/.+', productUrl, defaulturl)
                        sku['color'] = color
                        sku['images'] = images
                        item['skus'].append(sku)
                else:
                    sku = dict()
                    sku['originalPrice'] = originalPrice
                    sku['price'] = price
                    sku['productUrl'] = re.sub('/product/.+', productUrl, defaulturl)
                    sku['color'] = color
                    sku['images'] = images
                    item['skus'].append(sku)
            elif len(dimensionsSet) == 2:
                dimensionId1 = dimensionsSet[0]
                unitId1 = dimensionIdToUnitId[dimensionId1]
                unitName1 = unitIdToName[unitId1]
                dimensionId2 = dimensionsSet[1]
                unitId2 = dimensionIdToUnitId[dimensionId2]
                unitName2 = unitIdToName[unitId2]
                if valuesSet[dimensionId1][unitId1] and valuesSet[dimensionId2][unitId2]:
                    for value1 in valuesSet[dimensionId1][unitId1]:
                        for value2 in valuesSet[dimensionId2][unitId2]:
                            sku = dict()
                            sku[unitName1] = valueIdToName[value1]['value']
                            sku[unitName2] = valueIdToName[value2]['value']
                            sku['stock'] = 'out of stock'
                            sku['originalPrice'] = originalPrice
                            sku['price'] = price
                            sku['productUrl'] = re.sub('/product/.+', productUrl, defaulturl)
                            sku['color'] = color
                            sku['images'] = images
                            item['skus'].append(sku)
                else:
                    sku = dict()
                    sku['originalPrice'] = originalPrice
                    sku['price'] = price
                    sku['productUrl'] = re.sub('/product/.+', productUrl, defaulturl)
                    sku['color'] = color
                    sku['images'] = images
                    item['skus'].append(sku)
            # 更新库存
            for stock in style['stocks']:
                width = stock['width']
                size = stock['size']
                for i, value in enumerate(item['skus']):
                    sizeName = specName.get('size')
                    widthName = specName.get('width') or specName.get('inseam')
                    if sizeName and widthName:
                        if value[sizeName] == size and value[widthName] == width and value['color'] == color:
                            value['stock'] = stock['onHand']
                            item['skus'][i].update({'stock': stock['onHand']})
                    elif sizeName:
                        if value[sizeName] == size and value['color'] == color:
                            value['stock'] = stock['onHand']
                            item['skus'][i].update({'stock': stock['onHand']})
                    elif widthName:
                        if value[widthName] == width and value['color'] == color:
                            value['stock'] = stock['onHand']
                            item['skus'][i].update({'stock': stock['onHand']})
                    else:
                        item['skus'][0]['stock'] = stock['onHand']
        yield item
