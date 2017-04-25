# coding=utf-8
import re
import json
import requests
from tools import box
from w3lib.html import remove_tags

headers = """
accept:application/json, text/javascript, */*; q=0.01
accept-encoding:gzip, deflate, br
accept-language:en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4
cache-control:no-cache
content-length:0
origin:https://www.maximintegrated.com
pragma:no-cache
user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36
x-requested-with:XMLHttpRequest"""
headers = box.headers_to_dict(headers)


def get_part_name(series_name=None):
    series_name = series_name if series_name else ''
    url = 'https://www.maximintegrated.com/bin/ProductCatalogSearchServlet'
    if series_name:
        params_data = {
            'canSearch': '',
            'product_info_root_part': series_name
        }
        html = requests.get(url=url, params=params_data, headers=headers)
        # with open('parts_list.html', 'w') as fp:
        #     fp.write(html.content)
        data = json.loads(html.content)
        print data.get('Root_Part_Numbers')[0].get(series_name).get('Orderable_Part_Numbers')[0]


def combined(pn, pb, dn, db):
    pnd = []
    attr_key = ""
    attr_value = ""
    for item_pn, item_pb in zip(pn, pb):
        attr_key = ''.join([item_pn[x] + ' ' for x in range(0, 3) if item_pn[x].strip()])
        attr_value = item_pb
        pnd.append([attr_key, attr_value])
    attr = []
    attr_str = ""
    idx = 0
    # print pnd
    for item, value in zip(dn, db):
        dnb = {}
        attr = []
        series_name = item[0] if item[0].strip() else ''
        if not series_name:
            continue
        for k, v in zip(pnd, value):
            attr_str = ''
            attr_name = remove_tags(k[0])
            if isinstance(v, list):
                for vi in v:
                    attr_str += str(k[1][vi]) + ' '
                attr.append([attr_name, attr_str])
            elif not v == 0:
                attr_str = str(k[1][v]) + ' '
                attr.append([attr_name, attr_str])
            else:
                continue
        dnb = {
            'series_name': series_name,
            'series_number': item[1],
            'desc': item[2],
            'attr': attr
        }
        yield dnb


def get_stock(part_number):
    url = 'https://www.maximintegrated.com/bin/mySearchServlet'
    post_data = box.headers_to_dict("""input:single
query:MAX15036ATE+T
userType:anonymous""")
    post_data['query'] = part_number
    # print post_data
    # print headers
    # init
    part_data = {
        'tiered': [[0, 0.00]],
        'stock': [0, 1],
        'increment': 1,
    }
    try:
        response = requests.post(url=url, data=post_data, headers=headers)
        with open('stock.html', 'w') as fp:
            fp.write(response.content)
        data = json.loads(response.content)
    except:
        return part_data
    volume_prices = data.get('volumePrices', [])
    tiered = []
    for vol in volume_prices:
        min_qty = vol.get('minQuantity')
        price = vol.get('value')
        tiered.append([min_qty, price])
    if not tiered:
        tiered = [[0, 0.00]]
    stock = data.get('stock', {}).get('atpInv', 0)
    qty = data.get('min', 1)
    part_data['stock'] = [stock, qty]
    part_data['increment'] = data.get('mult', 1)
    part_data['tiered'] = tiered
    return part_data


if __name__ == "__main__":
    with open("product_list.html", 'r') as fp:
        html = fp.read()
    product_num = re.findall(r'\&nbsp;\((\d+)\)', html)
    # print sum(map(int, product_num))

    # pn
    with open('pn.html', 'r') as fp:
        html = fp.read()
        test_pn = json.loads(html)
    # pb
    with open('pb.html', 'r') as fp:
        html = fp.read()
        test_pb = json.loads(html)
    # dn
    with open('dn.html', 'r') as fp:
        html = fp.read()
        test_dn = json.loads(html)
    # db
    with open('db.html', 'r') as fp:
        html = fp.read()
        test_db = json.loads(html)
    # print type(test_pn), type(test_pb), type(test_dn), type(test_db)
    # print test_pn
    # print test_pb
    # for dd in combined(test_pn, test_pb, test_dn, test_db):
    #     print json.dumps(dd)
    # l = list(combined(test_pn, test_pb, test_dn, test_db))
    # print l[0]
    print get_stock('MAX15036ATE+')
    # get_part_name('MAX856')
    # print headers
