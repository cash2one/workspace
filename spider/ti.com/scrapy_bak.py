# def parse_resp(self, resp):
#     pattern_ti_id = re.compile(r'tiProductPathID = "(.*)";')
#     ti_id = pattern_ti_id.search(resp.text.encode('utf-8'))
#     txt = ti_id.group(1) if ti_id else ''
#     cat_id = re.findall(r'/(\d+)+', txt)
#     for x in cat_id:
#         criteria_url = 'http://www.ti.com/wsapi/paramdata/family/%s/criteria?lang=en&output=json' % x
#         results_url = 'http://www.ti.com/wsapi/paramdata/family/%s/results?lang=en&output=json' % x
#         yield Request(url=criteria_url, headers=self.headers, meta={'results_url': results_url}, callback=self.parse_detail)

# def parse_detail(self, resp):
#     results_url = resp.meta.get('results_url')
#     results_json = {}
#     criteria_json = {}
#     try:
#         results_json = requests.get(url=results_url, headers=self.headers)
#         criteria_json = resp.text.encode('utf-8')
#     except:
#         logger.exception('Parse error, request results_json is wrong, results_url: %s' % results_url)
#     if results_json and criteria_json:
#         criteria_json = json.loads(resp.text.encode('utf-8'))
#         results_json = json.loads(results_json.text.encode('utf-8'))
#     criteria = criteria_json.get('ParametricControl', {}).get('controls', [])
#     products = results_json.get('ParametricResults', [])
#     # pretty json data
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
#     # init item
#     item = GoodsItem()
#     item['goods_sn'] = ''
#     item['goods_name'] = ''
#     item['goods_other_name'] = ''
#     item['provider_name'] = ''
#     item['goods_desc'] = ''
#     item['url'] = ''
#     item['doc'] = ''
#     item['goods_img'] = ''
#     item['goods_thumb'] = ''
#     item['provider_url'] = ''
#     item['attr'] = []
#     item['catlog'] = []
#     item['stock'] = [0, 1]
#     item['tiered'] = [[0, 0.0]]
#     item['increment'] = 1
#     item['rohs'] = -1
#
#     # attr
#     attr = []
#     for product in products:
#         gpn = product.get('o1', '')
#         if not gpn:
#             continue
#         for k, v in attr_map.items():
#             if k == 'p1130':
#                 continue
#             attribute = product.get(k, '')
#             if 'multipair1' in attribute:
#                 attribute = attribute.get('multipair1', {}).get('l', '')
#             attribute_name = v
#             if not attribute:
#                 continue
#             attr.append([attribute_name, attribute])
#         for p in self.get_detail(gpn):
#             item['goods_sn'] = p.get('goods_sn', '')
#             item['goods_name'] = p.get('goods_sn', '')
#             item['goods_other_name'] = p.get('goods_sn', '')
#             item['goods_desc'] = product.get('o3', '')
#             item['url'] = 'http://www.ti.com/product/%s' % gpn
#             item['doc'] = self.get_data_sheet(gpn)
#             item['goods_img'] = p.get('goods_img', '')
#             item['goods_thumb'] = p.get('goods_img', '')
#             item['attr'] = attr
#             item['catlog'] = p.get('catlog', [])
#             item['stock'] = p.get('stock', [0, 1])
#             item['tiered'] = p.get('tiered', [[0, 0.0]])
#             yield item
