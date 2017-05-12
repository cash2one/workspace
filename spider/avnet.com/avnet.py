#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/11

import re
import logging
import urlparse
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("avnet")

_headers = {
    'Host': 'www.avnet.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/57.0.2987.98 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.avnet.com/wps/portal/apac/',
    'Accept-Encoding': 'gzip, deflate, sdch, br',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    'X-Requested-With': 'XMLHttpRequest',
}

url = 'https://www.avnet.com/shop/us/p/capacitor/capacitor-niobium/avx/noja226m002rwj-3074457345625507635/'


def _parse_detail_data(resp, headers=None, **kwargs):
    """
    解析详情数据，独立出来

    @param  data    页面数据
    @param  url     解析的页面url（方便记录异常）
    @param  kwargs  扩展参数
    """
    item = {}
    try:
        soup = BeautifulSoup(resp.text, 'lxml')
        if soup is None:
            logger.debug('初始化商品详情页面失败 URL: %s', resp.url)
            return -404
    except Exception as e:
        # logger.debug('初始化商品详情页面失败 URL: %s ERROR: %s', (resp.url, util.traceback_info(e)))
        return -404
    # goods_sn
    url_path_list = resp.url.split('/')
    goods_sn_pattern = re.compile(r'.*-\d{19}')
    for path in url_path_list[::-1]:
        if goods_sn_pattern.findall(path):
            item['goods_sn'] = path
            break
    if not item.get('goods_sn', False):
        logger.debug("无法从链接中解析goods_sn URL: {url} ".format(url=resp.url))
        return -400
    # goods_name
    goods_info_div = soup.find('div', class_='section-left')
    item['goods_name'] = goods_info_div.find('h1').get_text(strip=True) if goods_info_div else item['goods_sn']
    # url
    item['url'] = resp.url
    # goods_img
    img_div = soup.find('div', id="outer-div1")
    img = img_div.find('img') if img_div else None
    item['goods_img'] = img.get('src') if img else ''
    # goods_thumb
    item['goods_thumb'] = item['goods_img']
    # desc
    desc_p = soup.find('p', class_='RB-pdp_short_Desc')
    item['desc'] = desc_p.get_text(strip=True) if desc_p else ''
    # provider_name
    item['provider_name'] = "AVNET"
    # provider_url
    item['provider_url'] = ''
    # attr: [[None, None]]
    attr_body = soup.find('div', id="techAttr")
    attr_div = attr_body.find_all('div', class_='pdpDescriptionsBodyContent')
    attr = []
    if attr_div is not None:
        for content in attr_div:
            att_name = content.find('div', class_='pdpDescriptionColumn')
            attr_value = content.find('div', class_='pdpValueColumn')
            if att_name and attr_value:
                attr.append([att_name.get_text(strip=True), attr_value.get_text(strip=True)])
            else:
                continue
        item['attr'] = attr
    else:
        item['attr'] = attr
    # tiered: [[0, 0.00]]
    tiered_span = soup.find_all('span', class_='usdpart1')
    tiered = []
    if tiered_span is not None:
        for span in tiered_span:
            qty_span = span.find('span', class_='pdpTierMinQty')
            qty = qty_span.get_text(strip=True) if qty_span else 0
            price_p = span.find('p')
            price = price_p.get_text(strip=True) if price_p else 0.00
            if qty and price:
                tiered.append([qty, price])
            else:
                tiered = [[0, 0.00]]
                break
        item['tiered'] = tiered
    else:
        item['tiered'] = [[0, 0.00]]
    # 需要类型转换
    # stock: [0, 1]  >> [stock, qty]
    stock_input = soup.find('input', id='inStock')
    stock = stock_input.get('value') if stock_input else 0
    # qty
    min_qty_input = soup.find('input', attrs={'name': 'min'})
    min_qty = min_qty_input.get('value') if min_qty_input else 1
    item['stock'] = [stock, min_qty] if stock else ['0', '1']
    # increment: 1
    multi_input = soup.find('input', attrs={'name': 'mult'})
    item['increment'] = multi_input.get('value') if multi_input else 1
    # doc
    doc_div = soup.find('div', class_='pdfcontent')
    if doc_div is not None:
        doc_url = doc_div.find('a', class_='datasheet_align')
        item['doc'] = doc_url.get('href') if doc_url else ''
    else:
        item['doc'] = ''
    # rohs: -1
    rohs_div = soup.find('div', class_='leafcontent')
    item['rohs'] = 1 if rohs_div else -1
    # catlog: [[name, url]]
    nav = soup.find('nav', class_='breadcrumb')
    nav_ul = nav.find('ul', class_='nav')
    catlog = []
    if nav is not None:
        lis = nav.find_all('a')
        for a in lis:
            cat_name = a.get_text(strip=True)
            cat_url = urlparse.urljoin(resp.url, a.get('href'))
            if cat_name and cat_url:
                catlog.append([cat_name, cat_url])
            else:
                continue
        item['catlog'] = catlog
    else:
        item['catlog'] = catlog
    # goods_other_name
    item['goods_other_name'] = ''
    # product_id
    # family_sn
    return item


if __name__ == '__main__':
    # resp = requests.get(url=url, headers=_headers)
    # with open(r'product_detail.html', 'w') as fp:
    #     fp.write(resp.text.encode('utf-8'))
    class a(object):
        def __init__(self, text):
            self.url = 'https://www.avnet.com/shop/us/p/capacitor/capacitor-niobium/avx/noja226m002rwj-3074457345625507635/'
            self.text = text


    with open('product_detail.html', 'r') as fp:
        text = fp.read()
        resp = a(text)
    print _parse_detail_data(resp)
