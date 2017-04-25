    def process_url_goods(self, params, dlist=None, parse_page=False):
        """产品数据至合作库存"""
        if not params:
            return 0, 0
        _params = params.copy()

        _total_num = 0
        put_xs_list = []

        url = 'http://www.ctelec.cn/goods_search'
        try:
            response = requests.post(url, data=_params, headers=self.headers)
            bs = BeautifulSoup(response.text.encode('utf-8'), 'lxml')
        except:
            _logger.exception("GET %s Failed !!!" % urllib.unquote(_params['keyword']))
            return 0, 0
        if not bs.find('input', id='totalpage'):
            if parse_page:
                return 0, 0
            return 0, 0
        else:
            page_div = bs.find('input', id='totalpage')
            page_num = page_div['value']
            # print page_num
        _page_num = 1
        if parse_page:
            _page_num = page_num
        goods_list = []
        # goods_list
        goods_list = bs.find_all('dl', 'left_lie_d_c')
        if goods_list:
            for goods in goods_list:
                data = {}
                # url
                try:
                    url_div = goods.find('li', class_='ct_n_h')
                    detail_url = url_div.a['href'] if url_div else ''
                    data['url'] = util.urljoin(url, detail_url)
                except:
                    data['url'] = ''
                if data['url']:
                    pattern_gid = re.compile(r'gid=([^&]+)')
                    gid = pattern_gid.search(data['url'])
                    if gid:
                        gid = gid.group(1)
                        _sn = ('%s-%s' % (gid, PN2)).encode('utf-8')
                        data['goods_sn'] = hashlib.md5(_sn).hexdigest()
                    else:
                        continue
                # cat_name
                data['cat_name'] = urllib.unquote(_params['keyword'])
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
                tiered_div = bs.find('dd', class_='san_bgJIa_d san_bgJIa_b ')
                if tiered_div:
                    tiered_list = tiered_div.find_all('li')
                    for li in tiered_list[:-1]:
                        # qty = lis[0].i.get_text(strip=True)
                        # price = lis[1].i.get_text(strip=True)
                        qty = li.find('span', class_='Ia_qus').get_text(strip=True)
                        price = li.find('i', class_='Ia_jia').get_text(strip=True)
                        data['tiered'].append([util.number_format(qty, 0, 0), 0.0, util.floatval(price), 0.0])
                else:
                    data['tiered'] = [[0, 0.0, 0.0, 0.0]]

                # stock
                stock_div = goods.find('dd', class_='san_bgJIa_djia')
                data['hk_stock'] = 0
                data['cn_stock'] = 0
                if stock_div:
                    pattern_stock = re.compile(r'\s*(\d+)K')
                    stock = pattern_stock.search(stock_div.get_text(strip=True))
                    stock = stock.group(1) if stock else 0
                    data['cn_stock'] = int(stock)
                else:
                    data['cn_stock'] = 0
                if data.get('goods_sn', ''):
                    try:
                        _total_num += self.import_goods(data, put_xs_list=put_xs_list)
                    except Exception as e:
                        _logger.exception('导入数据至合作库存失败')
                    self.put_queue_list(put_xs_list, queue_name=config.PUT_XS_QUEUE)
            if parse_page:
                return _total_num, _page_num
            if dlist is not None:
                dlist.append(_total_num)
            return _total_num