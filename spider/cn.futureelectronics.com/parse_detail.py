#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/5/4
import json
import re
import urlparse
import requests
from bs4 import BeautifulSoup
from tools.Format import text_filter, clear_text

with open(r'detail_1.html', 'r') as fp:
    html_1 = fp.read()
with open('detail_2.html', 'r') as fp:
    html_2 = fp.read()


class Resp(object):
    def __init__(self, url):
        self.url = url


resp = Resp(
    'http://cn.futureelectronics.com/zh/technologies/passives/inductors/wirewound-inductors/Pages/1004195-LQW15AN15NG00D.aspx')
headers = {'Host': 'cn.futureelectronics.com', 'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4', 'Accept-Encoding': 'gzip, deflate, sdch', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36'}
cookies = {
            'SelectedCurrency': 'NY',
            'SelectedLanguage': 'zh-CN',
        }

filter_rules = (
    r'/search\.aspx\?dsNav=',
    r'/Technologies/.*/Product\.aspx\?ProductID=',
    r'/technologies/.*/Pages/.*\.aspx'
)
test_url = 'http://cn.futureelectronics.com/zh/search.aspx?dsNav=Ro%3A0%2CNea%3ATrue%2CN%3A891'
rs = requests.get(url=test_url, headers=headers, cookies=cookies)
with open(r'product_list.html', 'w') as fp:
    fp.write(rs.text.encode('utf-8'))
url_list = re.findall(filter_rules[1], rs.text.encode('utf-8')) or re.findall(filter_rules[2], rs.text.encode('utf-8'))
print url_list


def main():
    item = {}
    soup = BeautifulSoup(html_2, 'lxml')
    # goods_sn
    product_id_pattern_1 = re.compile(r'ProductID=([^&]+)', re.IGNORECASE)
    product_id_pattern_2 = re.compile(r'/Pages/(.*)\.aspx', re.IGNORECASE)
    product_id = product_id_pattern_1.search(resp.url) or product_id_pattern_2.search(resp.url)
    goods_sn = product_id.group(1) if product_id else ''
    item['goods_sn'] = goods_sn
    if not goods_sn:
        # logger.info(u"获取goods_sn失败 URL:{url}".format(url=resp.url))
        return None
    # goods_name
    product_ref = soup.find('p', class_='ref')
    goods_name = ''
    if product_ref:
        goods_name_pattern = re.compile(ur'<b>制造商零件编号:</b>\s*([^\"\'<>/]+)')
        product_ref_list = unicode(product_ref).split('<br/>')
        for x in product_ref_list:
            match = goods_name_pattern.search(x)
            if match:
                goods_name = match.group(1)
                break
    item['goods_name'] = goods_name
    # goods_other_name
    item['goods_other_name'] = ''
    # goods_desc
    goods_desc = soup.find('p', class_='desc')
    item['goods_desc'] = goods_desc.get_text(strip=True) if goods_desc else ''
    # provider_name and provider_url
    provider_name = soup.find('img', id='ctl00_PlaceHolderMain_mfrLogo')
    item['provider_name'] = provider_name.get('title', '')
    if not provider_name:
        desc_div = soup.find('div', id='product-desc')
        provider_name = desc_div.find('h2')
        provider_name = provider_name.get_text(strip=True) if provider_name else ''
        item['provider_name'] = provider_name
    item['provider_url'] = ''
    # url
    item['url'] = resp.url
    # doc
    doc = soup.find('a', id='ctl00_PlaceHolderMain_csDownloadCenter_linkDatasheetUrlJustText')
    item['doc'] = doc.get('href', '')
    # goods_img and goods_thumb
    goods_img = soup.find('img', id='previewedMEDImage')
    item['goods_img'] = goods_img.get('src', '')
    goods_thumb = soup.find('img', id='thumbnail-1')
    item['goods_thumb'] = goods_thumb.get('src', '')
    # catlog
    item['catlog'] = []
    catlog = soup.find('ul', id='breadcrumb-navigation')
    catlog_list = catlog.find_all('a')
    for a in catlog_list:
        breadcrumb_name = a.get_text(strip=True)
        # TODO 修改为util.urljoin
        breadcrumb_url = urlparse.urljoin(resp.url, a.get('href', ''))
        item['catlog'].append([breadcrumb_name, breadcrumb_url])
    # attr
    item['attr'] = []
    product_attr_div = soup.find('div', id='product-details-overview-highlights')
    product_attr_list = product_attr_div.find_all('li') if product_attr_div else []
    for li in product_attr_list:
        attr_name, attr_value = li.get_text(strip=True).split(':')
        item['attr'].append([attr_name, attr_value])
    # tiered
    item['tiered'] = []
    price_table = soup.find('table', class_='product-prices')
    price_tr_list = price_table.find_all('tr', class_='price-break')
    for tr in price_tr_list:
        qty_th = tr.find('th')
        # TODO qty提取第一个数值
        qty = qty_th.get_text(strip=True) if qty_th else 0
        price_span = tr.find('span')
        # TODO price转为浮点型
        price = price_span.get_text(strip=True) if price_span else 0.00
        # print qty, price
        if qty and price:
            item['tiered'].append([qty, price])
        else:
            item['tiered'] = [0, 0.00]
    # stock、increment、 min_qty
    stock_div = soup.find('div', id='product-qty-content')
    stock_tr = stock_div.find('tr', class_='qtyInStock')
    increment_tr = stock_div.find('tr', class_='multipleOf')
    min_qty_tr = stock_div.find('tr', class_='minOrderQty')
    # TODO 类型转换
    stock = stock_tr.find('td', class_='qty').get_text(strip=True) if stock_tr else 0
    increment = increment_tr.find('td', class_='qty').get_text(strip=True) if increment_tr else 1
    min_qty = min_qty_tr.find('td', class_='qty').get_text(strip=True) if min_qty_tr else 1
    item['stock'] = [stock, min_qty]
    item['increment'] = increment
    # rohs
    rohs_div = soup.find('div', id='ctl00_PlaceHolderMain_imgRoHS')
    item['rohs'] = 1 if rohs_div else -1
    print json.dumps(item)


if __name__ == '__main__':
    main()
