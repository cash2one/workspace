# coding=utf-8
import hashlib
import re
import urllib
import requests
from bs4 import BeautifulSoup
import Format


headers = {
    'host': 'www.ctelec.cn',
    'cache-control': 'max-age=0',
    'origin': 'http://www.ctelec.cn',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'referer': 'http://www.ctelec.cn/',
    'accept-language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
}


def get_keyword():
    url = 'http://www.ctelec.cn'
    response = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')
    cate = soup.find('ul', class_='cate_box')
    for li in cate.find_all('div', class_='tanchu'):
        div = li.get_text(strip=True)
        pattern_keyword = re.compile(r'([^\(\)]+)\((\d+)\)')
        for keyword in pattern_keyword.findall(div):
            if int(keyword[1]):
                # print keyword[0]
                yield urllib.quote(keyword[0])
    # with open('index.html', 'w') as fp:
    #     fp.write(response.content)


def page_num():
    url = 'http://www.ctelec.cn/goods_search'
    data = {'keyword': '%E8%B4%B4%E7%89%87%E7%94%B5%E9%98%BB', }
    response = requests.post(url=url, data=data, headers=headers)
    soup = BeautifulSoup(response.text.encode('utf-8'), 'lxml')
    page_div = soup.find('input', id='totalpage')
    page_num = page_div['value']
    # print page_num
    # goods_list
    # goods = soup.find_all('li', class_='ct_n_h')
    # goods_list = [good.a['href'] for good in goods] if goods else []
    # for x in goods_list:
    #     print 'http://www.ctelec.cn' + x

    # goods_list
    goods_list = soup.find_all('dl', 'left_lie_d_c')
    if goods_list:
        for goods in goods_list:
            data = {}
            # url
            try:
                url_div = goods.find('li', class_='ct_n_h')
                detail_url = url_div.a['href'] if url_div else ''
                data['url'] = url + detail_url
            except:
                data['url'] = ''
            if data['url']:
                pattern_gid = re.compile(r'gid=([^&]+)')
                gid = pattern_gid.search(data['url'])
                if gid:
                    gid = gid.group(1)
                    _sn = ('%s-%s' % (gid, "Hqchip")).encode('utf-8')
                    data['goods_sn'] = hashlib.md5(_sn).hexdigest()
                    data['gid'] = gid
                else:
                    continue
            # moq = 1
            data['moq'] = 1
            # increment
            data['increment'] = 1
            # goods_img
            img_div = goods.find('dt', class_='photo')
            try:
                data['goods_img'] = img_div.a.img['src'] if img_div else ''
                if 'ct_s.gif' in data['goods_img']:
                    data['goods_img'] = ''
            except:
                data['goods_img'] = ''

            # goods_other_name, brand ,goods_name, desc
            product_div = goods.find('dd', class_="san_bgJIa_d")
            # goods_other_name
            if product_div:
                name = product_div.find('li', class_='ct_n_h')
                if name:
                    data['goods_other_name'] = name.get_text(strip=True)
                    data['desc'] = name.get_text(strip=True)
            brand = goods.find('li', class_='brand')
            # brand
            data['brand'] = brand.get_text(strip=True) if brand else ''
            # goods_name
            pattern_goods_name = re.compile(ur'商品货号：\s*([^\s]+)')
            goods_name = pattern_goods_name.search(product_div.get_text())
            if goods_name:
                data['goods_name'] = goods_name.group(1)
            # tiered [[0, 0.0, 0.0, 0.0]]
            data['tiered'] = []
            tiered_div = soup.find('dd', class_='san_bgJIa_d san_bgJIa_b ')
            if tiered_div:
                tiered_list = tiered_div.find_all('li')
                for li in tiered_list[:-1]:
                    # qty = lis[0].i.get_text(strip=True)
                    # price = lis[1].i.get_text(strip=True)
                    qty = li.find('span', class_='Ia_qus').get_text(strip=True)
                    price = li.find('i', class_='Ia_jia').get_text(strip=True)
                    data['tiered'].append([Format.number_format(
                        qty, 0, 0), 0.0, Format.floatval(price), 0.0])

            # stock
            stock_div = goods.find('dd', class_='san_bgJIa_djia')
            if stock_div:
                pattern_stock = re.compile(r'\s*(\d+)K')
                stock = pattern_stock.search(stock_div.get_text(strip=True))
                stock = stock.group(1) if stock else 0
                data['stock'] = int(stock)
            else:
                data['stock'] = 0
            if data.get('goods_sn', ''):
                print data

PN2 = 'Hqchip'


def get_detail(url=None, keyword=None):
    url = url if url else ''
    if not url:
        return {}
    data = {}
    response = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')

    # url
    data = {'url': url}

    product_div = soup.find('ul', class_='xx_d')
    if product_div:
        data['goods_other_name'] = product_div.find('input', id='uname1')['value']
        data['goods_name'] = product_div.find('input', id='GSn1')['value']
        data['brand'] = product_div.find('input', id='BName1')['value']

    # goods_sn
    pattern_gid = re.compile(r'gid=([^&]+)')
    gid = pattern_gid.search(data['url'])
    if gid:
        gid = gid.group(1)
        _sn = ('%s-%s' % (gid, PN2)).encode('utf-8')
        data['goods_sn'] = hashlib.md5(_sn).hexdigest()
    elif data.get('goods_name', ''):
        _sn = ('%s-%s' % (data['goods_name'], PN2)).encode('utf-8')
        data['goods_sn'] = hashlib.md5(_sn).hexdigest()
    else:
        return {}

    # goods_desc
    description_div = soup.find('li', class_='xx_bzsm')
    data['goods_desc'] = description_div.get_text(strip=True) if description_div else ''
    # print data['goods_desc']

    # increment 和 min_buynum 最小购买量使用默认值
    data['increment'] = 1
    data['min_buynum'] = 0

    # tiered = [[0, 0.0, 0.0, 0.0]] [起订量，香港， 大陆， 海外]
    data['tiered'] = []
    tiered_div = soup.find('ul', class_='ul1')
    if tiered_div:
        tiered_list = tiered_div.find_all('dl')
        for item in tiered_list:
            spans = item.find_all('span')
            qty = spans[0].get_text(strip=True)
            price = spans[1].get_text(strip=True)
            data['tiered'].append([Format.number_format(qty, 0, 0), 0.0, Format.floatval(price), 0.0])
    else:
        data['tiered'] = [[0, 0.0, 0.0, 0.0]]

    # img
    img_div = soup.find('div', id='tsImgS')
    if img_div:
        img = img_div.find('img')
        data['goods_img'] = img['src'] if img else ''
        data['goods_thumb'] = data['goods_img']
    # 如果是空图片
    if 'non.jpg' in data['goods_img']:
        data['goods_img'] = ''
        data['goods_thumb'] = ''

    # category
    data['category'] = []
    crumbs_div = soup.find('div', class_='dizhilian_d')
    if crumbs_div:
        category_name = crumbs_div.find_all('a')[1:]  # 去掉首页
        for cat in category_name:
            data['category'].append(cat.get_text(strip=True))
    else:
        data['category'] = [keyword]

    # stock
    stock_div = soup.find('div', 'ku_cun')
    data['cn_stock'] = Format.intval(stock_div.i.get_text(strip=True)) if stock_div else 0
    data['hk_stock'] = 0

    # attr
    data['attr'] = []
    attr_div = soup.find('ul', class_='ping_a_d')
    if attr_div:
        for li in attr_div.find_all('li'):
            attr_string = li.get_text(strip=True)
            data['attr'].append(Format.str_to_unicode(attr_string).split(u'：'))
    return data


if __name__ == '__main__':
    # get_keyword()
    # page_num()
    test_urls = {
        'url1': 'http://www.ctelec.cn/goods_detail?gid=14330',  # 信息齐备
        'url2': 'http://www.ctelec.cn/goods_detail?gid=235463',  # 没价格
        'url3': 'http://www.ctelec.cn/goods_detail?gid=9731',  # 有图片
     }
    for item in test_urls.items():
        print get_detail(item[1])
