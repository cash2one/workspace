import re
import sys
import json
import urllib
import copy
import requests
from tools.box import get_pwd
from bs4 import BeautifulSoup

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
}

# home_page = 'http://www.ti.com/'
# html = requests.get(url=home_page, headers=headers)
# pattern_cat_url = re.compile(r'http://.*overview\.page', re.I)
# cat_urls = pattern_cat_url.findall(html.content)
# print cat_urls
# with open('cat_urls.html', 'w') as fp:
#     fp.write('\n'.join(cat_urls))

# cat_url = 'http://www.ti.com/lsds/ti/amplifiers/op-amps/op-amps-overview.page'
# html = requests.get(url=cat_url, headers=headers)
# with open('html/cat_level2.html', 'w') as fp:
#     fp.write(html.content)

with open('html/cat_level2.html', 'r') as fp:
    html = fp.read()
# html = 'tiProductPathID = "/57/1293/234/2335/2342/2";'
pattern_tiProductPathID = re.compile(r'tiProductPathID = "(.*)";')
tiProductPathID = pattern_tiProductPathID.search(html)
if tiProductPathID:
    txt = tiProductPathID.group(1)
    # print txt
ID = re.findall(r'/(\d+)+', txt)
# req_criteria = 'http://www.ti.com/wsapi/paramdata/family/%s/criteria?lang=en&output=json' % ID[-1]
# req_results = 'http://www.ti.com/wsapi/paramdata/family/%s/results?lang=en&output=json' % ID[-1]
#
# criteria_json = requests.get(url=req_criteria, headers=headers)
# with open('criteria_json.html', 'w') as fp:
#     fp.write(criteria_json.content)
# results_json = requests.get(url=req_results, headers=headers)
# with open('results_json.html', 'w') as fp:
#     fp.write(results_json.content)

with open('html/criteria_json.html', 'r') as fp:
    criteria_json = fp.read()

with open('html/results_json.html', 'r') as fp:
    results_json = fp.read()

# get item
criteria_json = json.loads(criteria_json)
results_json = json.loads(results_json)

criteria = criteria_json.get('ParametricControl', {}).get('controls', [])
products = results_json.get('ParametricResults', [])


# attr

# def get_attr():
#     attr_map = {}
#     for parametric in criteria:
#         cid = parametric.get('cid')
#         if 'p' in cid:
#             if parametric.get('name'):
#                 attr_map[cid] = parametric.get('name')
#             if parametric.get('attribute'):
#                 attr_map[cid] += '(%s)' % parametric.get('attribute')
#             if parametric.get('units'):
#                 attr_map[cid] += '(%s)' % parametric.get('units')
#     # print attr_map
#     attr = []
#     for product in products[0:1]:
#         gpn = product.get('o1')
#         for k, v in attr_map.items():
#             if k == 'p1130':
#                 continue
#             attribute = product.get(k, '')
#             if 'multipair1' in attribute:
#                 attribute = attribute.get('multipair1', {}).get('l', '')
#             attribute_name = v
#             attr.append([attribute_name, attribute])
#         for p in get_detail(gpn):
#             item = p
#             item['doc'] = get_data_sheet(gpn)
#             item['attr'] = attr
#             print json.dumps(item)
def get_attr(gpn):
    url = 'http://www.ti.com/product/opa1678'
    pattern_gpn = re.compile(r'/product/([^/]+)')
    gpn = pattern_gpn.search(url)
    gpn = gpn.group(1) if gpn else ''
    resp = requests.get(url=url, headers=headers)
    # with open('attr.html', 'w') as fp:
    #     fp.write(resp.content)
    soup = BeautifulSoup(resp.content, 'lxml')
    # description
    desc = soup.find('h1', class_='productTitle')
    desc = desc.get_text(strip=True) if desc else ''
    print desc
    attr = []
    params_table = soup.find('table', id='paramsName')
    data_table = soup.find('table', id='parametricdata')
    if params_table and data_table:
        attr_params = params_table.find_all('td')[0:-1]
        print len(attr_params)
        attr_data = data_table.find_all('td', class_='on')[0:-1]
        print len(attr_data)
        for k, v in zip(attr_params, attr_data):
            pattern_blank = re.compile('\s+')
            k = pattern_blank.sub(' ', k.get_text(strip=True))
            v = pattern_blank.sub(' ', v.get_text(strip=True))
            attr.append([k, v])
    return attr


def get_detail(gpn=None):
    data = {}
    if not gpn:
        return data
    url = "http://www.ti.com/product/%s/samplebuy" % gpn
    html = requests.get(url=url, headers=headers)
    # with open('simplebuy2.html', 'w') as fp:
    #     fp.write(html.content)
    # with open('simplebuy3.html', 'r') as fp:
    #     html = fp.read()
    soup = BeautifulSoup(html.content, "lxml")
    # soup = BeautifulSoup(html, "lxml")
    breadcrumb_div = soup.find('div', class_='breadcrumb')
    cat_log = []
    for a in breadcrumb_div.find_all('a'):
        if 'TI Home' in a.get_text(strip=True):
            continue
        cat_log.append([a.get_text(strip=True), a['href']])
    # print cat_log
    # goods_img, goods_thumb
    img_div = soup.find('div', class_='image')
    img = img_div.img['src'] if img_div else ''
    data['goods_img'] = img
    data['goods_thumb'] = img
    # data sheet
    data['doc'] = get_data_sheet(gpn)
    # pretty table
    table = soup.find('table', id='tblBuy')
    if not table:
        data['goods_sn'] = gpn
        data['tiered'] = [[0, 0.00]]
        data['stock'] = [0, 1]
        return [data]
    body_div = table.tbody if table else None
    ths = table.find_all('th')
    th_td = dict()
    for th in ths:
        if 'Part' in th.get_text(strip=True):
            th_td['PartNum'] = ths.index(th)
        if 'Price' in th.get_text(strip=True):
            th_td['Price'] = ths.index(th)
        if 'Inventory' in th.get_text(strip=True):
            th_td['Inventory'] = ths.index(th)
    tds = body_div.find_all('td')
    step = len(ths)
    tr = [tds[x:x + step] for x in range(0, len(tds), step)]
    product_list = list()
    for td in tr:
        # tiered
        price = th_td.get('Price')
        pattern_price = re.compile(r'\s*(\d+.\d+)\s*\|\s*(\d+)ku\s*')
        if td[price].script:
            td[price].script.extract()
        tiered = pattern_price.search(td[price].get_text())
        if tiered:
            price = tiered.group(1)
            qty = int(tiered.group(2)) * 1000
            data['tiered'] = [[qty, price]]
        # goods_sn
        part_num = th_td.get('PartNum')
        for x in td[part_num].contents:
            if x.name == 'script':
                continue
            elif x.name == 'a':
                data['goods_sn'] = str(x.string).strip()
                data['tiered'] = get_tiered(x['href'])
                stock = get_stock(data['goods_sn'], x['href'])
                data['stock'] = [stock, 1]
            elif x.string and str(x.string).strip():
                data['goods_sn'] = str(x.string).strip()
                data['stock'] = [0, 1]
        # print td[part_num]
        # # stock
        # inventory = th_td.get('Inventory')
        # if td[inventory].script:
        #     td[inventory].script.extract()
        # stock = td[inventory].get_text(strip=True)
        # if 'No Stock' in stock:
        #     data['stock'] = [0, 1]
        # else:
        #     match_stock = re.findall(r'(\d+)k', stock, re.I)
        #     if match_stock:
        #         stock = int(match_stock[0]) * 1000
        product_list.append(copy.copy(data))
    return json.dumps(product_list)
    # return product_list


def get_data_sheet(gpn):
    url = 'http://www.ti.com/lit/gpn/%s' % gpn
    html = requests.get(url=url, headers=headers, allow_redirects=False)
    pattern_redirect_url = re.compile(r'<a href="(.*)">')
    redirect_url = pattern_redirect_url.search(html.content)
    redirect_url = redirect_url.group(1) if redirect_url else ''
    if redirect_url:
        redirect_url = redirect_url.replace(r'&amp;', '&')
        pdf_page = requests.get(url=redirect_url, headers=headers, allow_redirects=False)
        with open('3.html', 'w') as fp:
            fp.write(pdf_page.content)
        pattern_doc_url = re.compile(r"window.location\s*=\s*'(http://.*\.pdf)'")
        doc_url = pattern_doc_url.search(pdf_page.content)
        doc_url = doc_url.group(1) if doc_url else ''
    else:
        doc_url = ''
    return doc_url


def get_tiered(url):
    url = 'https://store.ti.com/OPA4191ID.aspx'
    html = requests.get(url=url, headers=headers)
    # with open('tiered.html', 'w') as fp:
    #     fp.write(html.content)
    # with open('tiered.html', 'r') as fp:
    #     html = fp.read()
    # print type(html.status_code)
    soup = BeautifulSoup(html.content, 'lxml')
    table = soup.find('table', id='ctl00_ctl00_NestedMaster_PageContent_ctl00_BuyProductDialog1_PricingTierList')
    tiered = []
    if table:
        for tr in table.find_all('tr')[1:]:
            tds = tr.find_all('td')
            qty = tds[0].get_text(strip=True)
            price = tds[1].get_text(strip=True)
            tiered.append([qty, price])
    return tiered


def get_stock(goods_sn, url):
    session = requests.Session()
    session.headers = headers
    stock = 0
    add_to_cart(url, session)
    goods = look_at_basket(session)
    if goods_sn in goods:
        stock = goods[goods_sn]
    session.close()
    return stock


def add_to_cart(url, only_session):
    form_data = {
        "ctl00$ctl00$ScriptManager1": "ctl00$ctl00$NestedMaster$PageContent$ctl00$BuyProductDialog1$BuyProductPanel|ctl00$ctl00$NestedMaster$PageContent$ctl00$BuyProductDialog1$btnBuyPaid",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": "",
        "__VIEWSTATEGENERATOR": "",
        "__VIEWSTATEENCRYPTED": "",
        "ctl00$ctl00$NestedMaster$PageHeader$StoreHeader_H$SearchPhrase": "",
        "ctl00$ctl00$NestedMaster$PageHeader$StoreHeader_H$hiLastHeaderAction": "none",
        "ctl00$ctl00$NestedMaster$PageHeader$StoreHeader_H$hiSearchFilterValue": "none",
        "__ASYNCPOST": "true",
        "ctl00$ctl00$NestedMaster$PageContent$ctl00$BuyProductDialog1$btnBuyPaid": "Buy",
    }
    stock_page = only_session.get(url=url)
    soup = BeautifulSoup(stock_page.content, 'lxml')
    view_state = soup.find('input', id="__VIEWSTATE")
    form_data['__VIEWSTATE'] = view_state.value if view_state else ''
    view_state_generator = soup.find('input', id="__VIEWSTATEGENERATOR")
    form_data['__VIEWSTATEGENERATOR'] = view_state_generator.value if view_state_generator else ''
    # post
    resp = only_session.post(url=url, data=form_data)
    print resp.content


def look_at_basket(only_session):
    basket_url = 'https://store.ti.com/Basket.aspx'
    try:
        basket_page = only_session.get(basket_url)
    except:
        return 0
    soup = BeautifulSoup(basket_page.content, 'lxml')
    table = soup.find('table', id='ctl00_ctl00_NestedMaster_PageContent_ctl00_ProductList')
    rows = table.find_all('td', class_='cartRow')
    goods_data = {}
    for goods in rows:
        goods_sn = goods.find('span', class_='productSku').get_text(strip=True)
        print goods_sn
        goods_stock = goods.find('div', class_='prodStock').get_text(strip=True)
        print goods_stock
        goods_data[goods_sn] = goods_stock
    return goods_data


# def clean_cart(only_session):

def tool_detail(resp):
    # item = GoodsItem()
    item = {}
    pattern_gpn = re.compile(r'/tool/([^/\?\.]+)')
    # gpn
    gpn = pattern_gpn.search(resp.url)
    try:
        soup = BeautifulSoup(resp.text.encode('utf-8'),'lxml')
    except:
        # logger.exception('Parse Error Product URL: %s' % resp.url)
        return
    # category
    breadcrumb_div = soup.find('div', class_='breadcrumbs')
    cat_log = []
    for a in breadcrumb_div.find_all('a'):
        if 'TI Home' in a.get_text(strip=True):
            continue
        cat_log.append([a.get_text(strip=True), a['href']])
    item['catlog'] = cat_log if cat_log else []
    print cat_log
    # pretty table
    table = soup.find('table', attrs={'class': 'tblstandard'})
    if not table:
        # logger.exception('No Product in URL: %s' % resp.url)
        return
    trs = table.find_all('tr')[1:-1]
    for tr in trs:
        # goods_sn:description
        part = tr.find('h2').get_text(strip=True).split(':')
        name = part[0]
        desc = part[1]
        print part
        # price
        price = re.search(r'\$(\d+.?\d+)\(USD\)', tr.get_text(strip=True))
        print price.group(1)
    return item

if __name__ == "__main__":
    pass
    # test_pgn = 'OPA1678'
    # get_tiered(url)
    # print get_detail(test_pgn)
    # print get_attr(0)
    # get_data_sheet(t)
    # test_session = requests.Session()
    # test_session.headers = headers
    # test_goods_sn = 'OPA4377AQPWRQ1'
    # test_url = 'https://store.ti.com/OPA4377AQPWRQ1.aspx'
    # add_to_cart(test_url, test_session)
    # look_at_basket(test_session)
    # test_url = 'http://www.ti.com/tool/TMDSADP'
    # response = requests.get(url=test_url, headers=headers)
    # tool_detail(response)
    print get_pwd()
