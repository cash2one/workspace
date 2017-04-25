# coding=utf-8
import re
import json
import requests
import urlparse
from bs4 import BeautifulSoup

url = 'http://www.sekorm.com/ecSupply/pageList'

headers = {
    'Host': 'www.sekorm.com',
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/57.0.2987.98 Safari/537.36',
    'Referer': 'http://www.sekorm.com/supply/',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
}

params = {
    # 'pn': '',
    # 'exact': '',
    # 'selType': '',
    # 'sEcho': '1',
    # 'iColumns': '5',
    # 'sColumns': '%2C%2C%2C%2C',
    'iDisplayStart': '0',
    # 'iDisplayLength': '20',
    # 'mDataProp_0': 'pnCode',
    # 'mDataProp_1': 'brand',
    # 'mDataProp_2': 'pcs',
    # 'mDataProp_3': 'day',
    # 'mDataProp_4': 'sampleFlag',
    # '_': '1489650896046',
}

product_json = requests.get(url=url, headers=headers, params=params)
product_dict = json.loads(product_json.content)
# print type(product_dict)
total = int(product_dict.get('totalShow', 0))
product_list = product_dict.get('aaData')
search_url = 'http://www.sekorm.com/Web/Search/keyword/'
detail_list = []
for p in product_list:
    detail_list.append(urlparse.urljoin(search_url, p.get('pnCode', '')))
# print detail_list
test_url = 'http://www.sekorm.com/Web/Search/keyword/AS4C64M16D2-25BIN'
html = requests.get(url=test_url, headers=headers)
soup = BeautifulSoup(html.content, 'lxml')
table = soup.find('table')
# print table
detail_tr = table.find_all('tr')[1:]
# print detail_tr
data = {}
for detail in detail_tr:
    data['pncode'] = detail.find('span', class_='supply_pncode').string
    data['brand'] = detail.find('span', class_='supply_brand').string
    data['increment'] = detail.find('span', class_='supply_packing_min').string
    qty = detail.find('span', class_='supply_booking_min').string
    stock = detail.find_all('td')
    print stock[5].string
    data['stock'] = [stock[5].string, qty]
print data
# for detail in detail_tr:
#     print detail
# print type(detail_tr[0])