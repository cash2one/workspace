#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/6/19

import copy
import config
import requests
import urlparse
import lxml.html
from tools import box as util

proxies = {
    'http': 'http://127.0.0.1:1080',
    'https': 'http://127.0.0.1:1080'
}

_headers = copy.copy(config.DEFAULT_HEADERS)
_headers.update({
    'Host': 'estore.heilind.com',
})


def main():
    target = 'https://estore.heilind.com/search.asp?p=aa&mfg=&md=1&n=25'
    rs = requests.get(url=target, headers=_headers, proxies=proxies)
    html = rs.text.encode('utf-8')
    with open(r'html/search_page.html', 'w') as fp:
        fp.write(html)
    print rs.cookies


def get_page():
    with open('html/search_page.html', 'r') as fp:
        html = fp.read()
    root = lxml.html.fromstring(html.encode('utf-8'))
    # detail url
    url = 'https://estore.heilind.com/search.asp?p=aa&mfg=&md=1&n=25'
    product_list = root.xpath('//table[@class="searchresults"]//td/b/a/@href')
    product_list = [urlparse.urljoin(url, x) for x in product_list]
    print len(product_list)
    print product_list


def get_detail():
    target = 'https://estore.heilind.com/2BA-AL-36/POM2BA-AL-36.html'
    # rs = requests.get(url=target, headers=_headers, proxies=proxies)
    # html = rs.text.encode('utf-8')
    # with open(r'html/detail3.html', 'w') as fp:
    #     fp.write(html)
    with open('html/detail3.html', 'r') as fp:
        html = fp.read()
    root = lxml.html.fromstring(html)
    item = {
        'goods_img': '',
        'goods_thumb': '',
        'provider_url': '',
        'attr': [],
        'catlog': [],
        'rohs': -1,
    }
    _table = root.xpath('//table[@class="partdetail"]')
    select_parse_mode = len(_table)
    if select_parse_mode == 1:
        detail_table = _table[0]
        info_table = detail_table.xpath('//table[@id="partinfo"]')
        goods_sn = info_table[0].xpath('.//td[@class="txtleft"]/h4/text()') if info_table else None
        if not goods_sn:
            return
        item['goods_sn'] = goods_sn[0].strip()
        item['goods_name'] = item['goods_sn']

        # goods_other_name
        goods_other_name = info_table[0].xpath('.//tr[2]/td[2]/text()')
        item['goods_other_name'] = goods_other_name[0].strip() if goods_other_name else ''

        # provider_name
        provider_name = info_table[0].xpath('.//tr[3]/td[2]/text()')
        item['provider_name'] = provider_name[0].strip() if provider_name else ''

        # goods_desc
        goods_desc = info_table[0].xpath('.//tr[4]/td[2]/text()')
        item['goods_desc'] = goods_desc[0].strip() if goods_desc else ''

        # doc
        doc = info_table[0].xpath('.//tr[5]//h4/a/@href')
        item['doc'] = urlparse.urljoin(target, doc[0]) if doc else ''

        # url
        item['url'] = ''

        # increment
        item['increment'] = 1

        # tiered
        price_table = detail_table.xpath('.//table[@class="price-break"]')
        if not price_table:
            item['tiered'] = [[0, 0.00]]
        else:
            tiered = []
            price_tr = price_table[0].findall('tr')
            for tr in price_tr:
                tds = tr.findall('td')
                qty = util.intval(tds[0].text)
                price = util.floatval(tds[1].text, places=5)
                if price == 0 or qty == 0:
                    break
                tiered.append([qty, price])
            item['tiered'] = tiered if tiered else [[0, 0.00]]

        # stock
        item['stock'] = [0, 1]
        available = detail_table.xpath('./tr[2]/td[2]/text()')
        stock = util.intval(available[0].strip()) if available else 0
        # qty
        quantity = detail_table.xpath('./tr[2]/td[4]')
        input_box = quantity[0].findall('input') if quantity else None
        if input_box:
            quantity = quantity[0].xpath('//input[@class="textbox"]/@value')
        else:
            quantity = util.intval(quantity[0].text) if quantity else 1
        item['stock'] = [stock, quantity]
    elif select_parse_mode == 2:
        stock_table = _table[0].xpath('./tr[2]/td')
        info_table = _table[1]
        goods_sn = stock_table[0].text_content()
        item['goods_sn'] = goods_sn.strip()
        if not goods_sn:
            return
        item['goods_sn'] = goods_sn.strip()
        item['goods_name'] = item['goods_sn']

        # url
        item['url'] = ''

        # tiered
        price_table = stock_table[5].xpath('.//table[@class="price-break"]')
        if not price_table:
            item['tiered'] = [[0, 0.00]]
        else:
            tiered = []
            price_tr = price_table[0].findall('tr')
            for tr in price_tr:
                tds = tr.findall('td')
                qty = util.intval(tds[0].text)
                price = util.floatval(tds[1].text, places=5)
                if price == 0 or qty == 0:
                    break
                tiered.append([qty, price])
            item['tiered'] = tiered if tiered else [[0, 0.00]]

        # stock
        item['stock'] = [0, 1]
        available = stock_table[1].text_content()
        stock = util.intval(available) if available.strip() else 0
        # qty
        quantity = stock_table[6]
        input_box = quantity.findall('input') if quantity is not None else None
        if input_box:
            input_value = quantity.xpath('//input[@class="textbox"]/@value')
            quantity = util.intval(input_value[0]) if len(input_value) else 1
        else:
            quantity = item['tiered'][0][0] if item['tiered'][0][0] != 0 else 1
        item['stock'] = [stock, quantity]

        # increment
        increment = stock_table[4].text_content()
        item['increment'] = util.intval(increment, index=999)

        # goods_other_name
        goods_other_name = info_table.xpath('./tr[3]/td[2]/text()')
        item['goods_other_name'] = goods_other_name[0].strip() if len(goods_other_name) else ''

        # provider_name
        provider_name = info_table.xpath('./tr[4]/td[2]/text()')
        item['provider_name'] = provider_name[0].strip() if provider_name else ''

        # goods_desc
        goods_desc = info_table.xpath('./tr[5]/td[2]/text()')
        item['goods_desc'] = goods_desc[0].strip() if goods_desc else ''

        # doc
        doc = info_table.xpath('./tr[7]//a/@href')
        item['doc'] = urlparse.urljoin(target, doc[0]) if doc else ''

        # rohs
        rohs = info_table.xpath('./tr[8]//img')
        item['rohs'] = 1 if len(rohs) else -1

    return item


if __name__ == '__main__':
    # main()
    print get_detail()
