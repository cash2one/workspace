#!/usr/bin/env python
# -*- encoding: utf-8 -*-

__author__ = 'qaulau'

import os
import re
import sys
import copy
import logging
import random

import requests
import lxml.html

try:
    import Util as util
except ImportError:
    _path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.insert(0, _path)
    import Util as util

'''
microchipdirect 封装函数

@description
    以下为收集特殊情况页面




'''

logger = logging.getLogger('hqchip_spider')
default_headers = {
    'host': 'www.microchipdirect.com',
}
default_cookies = {
    'CurrentLanguage': 'cn',  # 语言中文
    'BuyMicrochipCatalog': 'BuyMicrochip',  # 位置美国，显示为美元
    'MSCSProfile': '983BB0CC620F5E6D8FDE26829663AF162FE6ACA7EE7267F7A5639D19B69483AC48806A68A2401ED927F160FE974DB78B6FDADC70FE871E98365938EB101BF5184545EC9E357CBD6CFED57460649ADFE2D0CAF79726107A4106332CBBE41C1D5979295327266C6774DF6A50B3281273B12FDC0C80309A9D7430EA533D993AA9611380A35BC8880BD295E26C30E7F03362E9B7B4624B60F1D91C345C7F9B4AB288E8FD9DCE2B22E386C959C4E64BE07471'
}


def fetch_data(url, proxy=None, headers=None, **kwargs):
    '''
    获取页面数据

    @param url      产品详细页地址
    @param proxy    代理ip，[代理数量,代理列表]
    @param headers  头部信息，如user_agent
    @param kwargs   扩展参数

    @return
        获取数据异常时返回信息为负值，成功为字典类型数据


    '''
    _headers = copy.copy(default_headers)
    _cookies = copy.copy(default_cookies)
    # 暂时性替换https
    url = url.replace('https:', 'http:')
    if isinstance(headers, dict):
        _headers.update(headers)
    proxies = None
    try:
        if proxy:
            i = random.randint(0, proxy[0] - 1)
            proxies = {'http': 'http://' + proxy[1][i]}
        resp = requests.get(url, headers=_headers, cookies=_cookies,
                            timeout=30, proxies=proxies)
    except Exception as e:
        logger.debug('STATUS:-400 ; INFO:%s ; URL:%s' % (e, url))
        return -400
    if resp.status_code != 200:
        logger.debug('STATUS:-405 ; INFO:请求错误，网页响应码 %s ; PROXY：%s ; URL:%s' % (resp.status_code,
                                                                               proxies['http'] if proxies else '', url))
        return -405

    fetch_update = kwargs['fetch_update'] if 'fetch_update' in kwargs else False

    root = lxml.html.fromstring(resp.text)
    if not root.xpath('//div[@id="mainContent"]'):
        logger.debug('STATUS:-404, INFO:数据异常，URL：%s' % url)
        return -404

    rlist = root.xpath('//div[contains(@class, "result")]')
    if not rlist:
        logger.debug('STATUS:404 ; INFO:无产品数据 ; URL: %s' % url)
        return 404
    # print resp.text.encode('utf-8')
    res = {}
    res['list'] = []
    for row in rlist:
        item = {}
        # 制造商和制造商型号名
        try:
            text = row.xpath(".//span[contains(@id, 'productIDLabelvalue')]/text()")[0].replace(u'\xa0', '')
            item['goods_name'] = util.cleartext(text)
        except:
            item['goods_name'] = util.cleartext(row.xpath("./input[contains(@id, 'PID_')]/@value")[0])
        item['goods_sn'] = item['goods_name']
        try:
            item['desc'] = util.cleartext(row.xpath(".//p[@class='description']")[0].text_content())
        except:
            item['desc'] = ''

        item['url'] = 'https://www.microchipdirect.com/ProductSearch.aspx?keywords=%s' % item['goods_name']
        item['provider_name'] = 'Microchip Technology Inc.'
        item['provider_url'] = 'http://www.microchip.com'
        item['provider_img'] = 'http://www.microchip.com/_images/logo.png'
        # 产品图片
        item['goods_img'] = ''
        imgs = row.xpath(".//img[contains(@class, 'img-responsive')]/@src")
        if imgs:
            item['goods_img'] = util.urljoin(resp.url, imgs[0])
        item['goods_thumb'] = item['goods_original'] = item['goods_img']
        # 产品库存
        # Availaible为搜索列表页库存数，Availability为类型列表页库存数，Available为非开发工具库存数
        stocks = row.xpath("//span[contains(@id, 'Available')] | //span[contains(@id, 'Availaible')] | \
            //span[contains(@id, 'Availibility')]")
        if stocks:
            stock = util.intval(stocks[0].text_content())
        else:
            stock = 0
        item['tiered'] = []
        prices = row.xpath(".//div[contains(@id, 'StdPricing')]/table/tr[2]/td/table/tr")
        if not prices:
            prices = row.xpath(".//div[contains(@id, 'stdListing')]")
        for vo in prices:
            try:
                tlist = vo.xpath('./td')
                if not tlist:
                    tlist = vo.xpath('./div')
                    price = util.floatval(tlist[1].text_content())
                else:
                    price = util.floatval(tlist[2].text_content())
                qty = util.intval(tlist[0].text_content())
                if not qty or (item['tiered'] and qty < item['tiered'][-1][0]):
                    continue
                # 由于采购时超过100的还会按100的价格计算，因此去除100之后的价格（2014/09/24）
                # if qty > 100:
                #    break
                item['tiered'].append([qty, price])
            except:
                pass
        if not item['tiered']:
            item['tiered'].append([0, 0.0])

        mqty = row.xpath(".//div[contains(@id, 'lblAvailabilityIn')]")
        if mqty:
            mqty = util.intval(mqty[0].text_content(), 0)
            if mqty <= 0:
                mqty = 1
        else:
            mqty = 1
        item['stock'] = [stock, mqty]
        item['increment'] = mqty  # 产品递增量
        # 属性
        item['attr'] = []
        attrs = row.xpath(".//div[@class='specifications']/div[1]/div")
        for vo in attrs:
            try:
                text = vo.xpath('./p')[0].text_content().replace(u'\xa0', '')
                tlist = util.cleartext(text, ' ').split(':')
                name = tlist[0]
                value = tlist[1]
                if not name:
                    continue
                item['attr'].append([name, value])
            except:
                pass
                # 文档
        item['doc'] = 'http://www.microchip.com/search/searchapp/searchparts.aspx?q=%s' % item['goods_name']
        datasheet = row.xpath(".//a[contains(@id, 'DataSheetLink')]/@href")
        if datasheet:
            item['doc'] = util.urljoin(resp.url, datasheet[0])
        # 描述信息
        if not item['desc']:
            if not fetch_update:
                desc = row.xpath(".//span[contains(@id, 'ProductDescription')]")
            else:
                desc = row.xpath(".//span[contains(@id, 'lblDevToolValue')]")
            if desc:
                item['desc'] = util.cleartext(desc[0].text_content(), item['goods_name'], '\xa0-\xa0')
            print('型号：%s 数据获取成功' % util.binary_type(item['goods_name']))
        res['list'].append(item)
    return res


def fetch_search_data(keyword=None, id=None, data_dict=None, headers=None, proxy=None, **kwargs):
    '''
    抓取搜索数据
    '''
    print '正在获取 microchipdirect 中关键词：%s 的相关数据' % keyword
    url = 'https://www.microchipdirect.com/ProductSearch.aspx?keywords=%s' % keyword
    res = fetch_data(url=url, proxy=proxy, headers=headers, **kwargs)
    if isinstance(res, dict):
        for data in res['list']:
            data['id'] = id
            data['status'] = 200
            data_dict['detail'].append(data)
        return 200
    else:
        data_dict['url'].append({'status': res, 'url': url, 'id': id, 'count': kwargs.get('count', 1)})
        return res


def fetch_search_list(url, id=None, headers=None, proxy=None):
    '''
    抓取搜索列表数据
    '''
    pass


def fetch_update_data(url=None, id=None, **kwargs):
    '''
    获取更新数据

    @description
        更新数据仅需要
        id          此处为GoodsId
        tiered      价格阶梯
        stock       库存
        attr        属性
        desc        描述
        increment   递增量
    '''
    headers = kwargs.get('headers')
    proxy = kwargs.get('proxy')
    data = fetch_data(url, headers=headers, proxy=proxy, fetch_update=True)
    res = {}
    res['id'] = id
    if isinstance(data, dict):
        res['status'] = 200
        res['stock'] = data['list'][0]['stock']
        res['tiered'] = data['list'][0]['tiered']
        res['attr'] = data['list'][0]['attr']
        res['increment'] = data['list'][0]['increment']
        res['desc'] = data['list'][0]['desc']
    else:
        res['status'] = data
        res['url'] = url
        res['count'] = kwargs.get('count', 1)
    return res


# def tests():
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
#     }
#     url = 'http://www.microchipdirect.com/ProductSearch.aspx?keywords=PIC32MX110F016C-I%2fTL'
#     #print fetch_data(url, headers=headers)
#     url = 'https://www.microchipdirect.com/ProductSearch.aspx?keywords=SW500189'
#     print fetch_data(url, headers=headers)
#     url = 'http://www.microchipdirect.com/ProductDetails.aspx?Catalog=BuyMicrochip&Category=AT89C2051&mid=10'
#     #print fetch_data(url, headers=headers)

if __name__ == '__main__':
    # tests()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    }
    url = 'http://www.microchipdirect.com/ProductSearch.aspx?keywords=AT89C51CC02'
    print fetch_data(url, headers=headers)
