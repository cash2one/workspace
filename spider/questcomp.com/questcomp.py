# coding=utf-8
import re
import json
import requests
import bs4
import urlparse
from bs4 import BeautifulSoup

url = 'http://www.questcomp.com/ProductTypes.aspx'

headers = {
    'Host': 'www.questcomp.com',
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/57.0.2987.98 Safari/537.36',
    'Referer': 'http://www.questcomp.com/',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
}


# 获取目录链接
# category = requests.get(url=url, headers=headers)
# with open('category_page.html', 'w') as fp:
#     fp.write(category.content)
# re.compile(r'(DetailSearch.aspx\?catid=\d+)')

# with open('category_page.html', 'r') as fp:
#     html = fp.read()
#     pattern_cat_urls = re.compile(r'(/DetailSearch.aspx\?catid=\d+)')
#     cat_urls = pattern_cat_urls.findall(html)
#     filter_cat_urls = list(set(cat_urls))
# print len(cat_urls), len(filter_cat_urls)
# with open('category_urls.html', 'w') as fp:
#     for a in filter_cat_urls:
#         link = urlparse.urljoin(url, a)
#         fp.write(link + '\n')

# 获取产品页链接
# product_list_url = 'http://www.questcomp.com/DetailSearch.aspx?catid=210'
# product_list = requests.get(url=product_list_url, headers=headers)
# with open('product_list.html', 'w') as fp:
#     fp.write(product_list.content)
# with open('product_list.html', 'r') as fp:
#     html = fp.read()
#     pattern_product_urls = re.compile(r'(/questdetails.aspx\?pn=[^&]+&mpid=[^&]+&pt=\d+)')
#     product_urls = pattern_product_urls.findall(html)
#     filter_product_urls = list(set(product_urls))
# print len(product_urls), len(filter_product_urls)
# with open('product_urls.html', 'w') as fp:
#     for a in filter_product_urls:
#         link = urlparse.urljoin(url, a)
#         fp.write(link + '\n')

# 获取产品详情
# detail_url = 'http://www.questcomp.com/questdetails.aspx?pn=2N2222A'
# detail_page = requests.get(url=detail_url, headers=headers)
# with open('detail2.html', 'w') as fp:
#     fp.write(detail_page.content)


# 解析产品详情
def get_part_stock(items_x_div=None):
    """items_x_div is bs4.element.Tag's object"""
    if not items_x_div.__class__ == bs4.element.Tag:
        return None
    in_stock = items_x_div.find('div', id='rpt-available-qty').get_text(strip=True)
    in_stock = int(in_stock.replace(',', ''))
    return in_stock


def get_part_manufacturer(items_x_div=None):
    """items_x_div is bs4.element.Tag's object"""
    if not items_x_div.__class__ == bs4.element.Tag:
        return None
    manufacturer = items_x_div.find('div', id='rpt-mfg').get_text(strip=True)
    return manufacturer


def get_part_tiered(items_x_div=None):
    """items_x_div is bs4.element.Tag's object"""
    if not items_x_div.__class__ == bs4.element.Tag:
        return None
    tiered = list()
    qty = items_x_div.find('div', id='rpt-range-qty').stripped_strings
    prices = items_x_div.find('div', id='rpt-range-price').stripped_strings
    for qty, price in zip(qty, prices):
        tiered.append([qty, price])
    return tiered


detail_url = 'http://www.questcomp.com/questdetails.aspx?pn=2N2222A'
with open('detail2.html', 'r') as fp:
    html = fp.read()
soup = BeautifulSoup(html, 'lxml')
item = {
    'goods_sn': '',  # 产品标识
    'goods_name': '',  # 产品销售型号名
    'goods_other_name': '',  # 其他商品名

    'goods_desc': '',  # 描述

    'url': '',  # URL
    'goods_img': '',  # 产品图片
    'goods_thumb': '',  # 缩略图
    'provider_name': '',  # 供应商/品牌
    'provider_url': '',  # 供应商URL
    'tiered': '',  # 价格阶梯
    'stock': '',  # 库存信息，库存和最小购买量
    'increment': '',  # 递增量
    'doc': '',  # 文档
    'attr': '',  # 属性
    'rohs': '',  # rohs
    'catlog': '',  # 分类
}

goods_div = soup.find('div', id='divPartNumber').stripped_strings
# print soup.find('div', id='divPartNumber').get_text(strip=True)
goods_sn = list(goods_div)[0]
goods_name = goods_sn
goods_other_name = goods_sn

goods_desc_div = soup.find('div', id='MasterPageContent_ucProductHeader_detailsPartDescription').next_siblings
# print soup.find('div', id='MasterPageContent_ucProductHeader_detailsPartDescription').get_text(strip=True)
goods_desc = list(goods_desc_div)[1].string.strip()

img = soup.find('div', class_='part-details-img')
goods_img = img.img['src'] if img else ''
goods_img = urlparse.urljoin(detail_url, goods_img)
goods_thumb = goods_img

# part-grid

# 异常处理
# div可能不存在
# rptItems_0_div
# In Stock
rptItems_0_div = soup.find('div', id='MasterPageContent_ucProductHeader_ucPartResults_rptPartResults_rptItems_0')
print '*'*3
print rptItems_0_div
part_grid = soup.find('div', id='part-grid')
print '*'*3
print part_grid
items_0_to_end = part_grid.find_all('div', class_='rpt-items flex-row')
print '*'*3
print items_0_to_end
print '-'*3
rptItems_0_stock = get_part_stock(rptItems_0_div)

available_manufacturers_div = soup.find_all('div', class_='rpt-items flex-row instock')
rptItems_0_manufacturers = []
for mnf in available_manufacturers_div:
    mnf_manufacturer = get_part_manufacturer(mnf)
    mnf_stock = get_part_stock(mnf)
    rptItems_0_manufacturers.append([mnf_manufacturer, mnf_stock])
print rptItems_0_manufacturers
# total_sum = reduce(lambda x, y: x + y, [v[1] for v in manufacturers])
# print total_sum

# tiered
rptItems_0_tiered = get_part_tiered(rptItems_0_div)
# print rptItems_0_tiered

# rptItems_1 to the end
part_grid = soup.find('div', id='part-grid')
# print part_grid
rptItems_0_to_end = part_grid.find_all('div', class_='rpt-items flex-row')
# print rptItems_1_to_end
rptItems_detail = []
for rptItem in rptItems_0_to_end:
    rptItem_stock = get_part_stock(rptItem)
    rptItem_manufacturer = get_part_manufacturer(rptItem)
    rptItem_tiered = get_part_tiered(rptItem)
    rptItems_detail.append([rptItem_manufacturer, rptItem_stock, rptItem_tiered])


# print len(rptItems_detail)
print rptItems_detail


# # 翻页next page
# # with open('product_list.html', 'r') as fp:
# #     html = fp.read()
#
# product_list = 'http://www.questcomp.com/DetailSearch.aspx?catid=210'
# resp = requests.get(url=product_list, headers=headers)
# html = resp.content
# soup = BeautifulSoup(html, 'lxml')
# view_state = soup.find('input', id='__VIEWSTATE')['value']
# part_id = soup.find('input', id='MasterPageContent_hidFirstMasterPartID')['value']
# hid_in_stock = soup.find('input', id='MasterPageContent_hidInStock')['value']
# hid_data_sheet_params = soup.find('input', id='MasterPageContent_hidDatasheetParams')['value']
# # print type(view_state)
# # print type(part_id)
# formdata = {
#     '__EVENTTARGET': '',
#     '__EVENTARGUMENT': '',
#     '__VIEWSTATE': view_state,
#     'MasterBasic$searchBox': 'Type Part Number Here',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl01$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl02$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl03$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl04$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl05$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl06$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl07$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl08$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl09$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$rptPartDescriptions$ctl10$ddlSearchParameter': 'Any',
#     'MasterBasic$MasterPageContent$ucDetailSearch$hidAvailability': '',
#     'MasterBasic$MasterPageContent$btnNextParts': 'Next  >>',
#     'MasterBasic$MasterPageContent$hidFirstMasterPartID': part_id,
#     'MasterBasic$MasterPageContent$hidInStock': hid_in_stock,
#     'MasterBasic$MasterPageContent$hidPartInfo': '',
#     'MasterBasic$MasterPageContent$hidDatasheetParams': hid_data_sheet_params,
#     'txtCUVID': '',
# }
# # print type(json.dumps(formdata))
#
# page2 = requests.post(url=product_list, data=json.dumps(formdata), headers=headers)
# with open('product_list_page2.html', 'w') as fp:
#     fp.write(page2.content)

def choice_data_sheet():
    datasheetID = '299530;1404787364'
    datasheetParams = '0;79b9d9b1-166c-4fab-90da-0ee624db0afc;116.24.153.54'

    request_doc_url = 'http://www.questcomp.com/DetailSearch.aspx/GetDataSheetByID'
    data = {
        'datasheetID': '409897;1844042807',
        'datasheetParams': '0;79b9d9b1-166c-4fab-90da-0ee624db0afc;116.24.153.54'
    }
    head = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    resp = requests.post(url, data=json.dumps(data), headers=head)
    print resp.content


# choice_data_sheet()
