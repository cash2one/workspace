json 接口
https://www.avnet.com/search/resources/store/715839038/productview/bySearchTerm/select?searchType=102&profileName=Avn_findProductsBySearchTermCatNav_Ajax&searchSource=Q&landingPage=true&storeId=715839038&catalogId=10001&langId=-1&currency=USD&orgEntityId=-2000&responseFormat=json&pageSize=20&pageNumber=1&_wcf.search.internal.boostquery=price_USD:{0.00001+TO+*}^499999.0+inStock:%22true%22^9000.0+topSellerFlag:%22Yes%22^0.085+newProductFlag:%22Yes%22^0.080+packageTypeCode:%22BKN%22^0.075&_wcf.search.internal.filterquery=-newProductFlag%3ANPI&q=LM358ADT&intentSearchTerm=LM358ADT&searchTerm=LM358ADT&wt=json

headers={
	'Host': 'www.avnet.com',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
	'Referer': 'https://www.avnet.com/wps/portal/apac/',
	'Accept-Encoding': 'gzip, deflate, sdch, br',
	'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
}

对比
https://www.avnet.com/search/resources/store/715839038/productview/bySearchTerm/select?searchType=102&profileName=Avn_findProductsBySearchTermCatNav_Ajax&searchSource=Q&landingPage=true&storeId=715839038&catalogId=10001&langId=-1&currency=USD&orgEntityId=-2000&responseFormat=json&pageSize=20&pageNumber=1&_wcf.search.internal.boostquery=price_USD:{{0.00001+TO+*}}^499999.0+inStock:%22true%22^9000.0+topSellerFlag:%22Yes%22^0.085+newProductFlag:%22Yes%22^0.080+packageTypeCode:%22BKN%22^0.075&_wcf.search.internal.filterquery=-newProductFlag%3ANPI&q={keyword}&intentSearchTerm={keyword}&searchTerm={keyword}&wt=json

https://www.avnet.com/search/resources/store/715839038/productview/bySearchTerm/select?searchType=102&profileName=Avn_findProductsBySearchTermCatNav_More_Ajax&searchSource=Q&landingPage=true&storeId=715839038&catalogId=10001&langId=-1&currency=USD&orgEntityId=-2000&responseFormat=json&pageSize=20&pageNumber=2&_wcf.search.internal.boostquery=price_USD:{0.00001+TO+*}^499999.0+inStock:%22true%22^9000.0+topSellerFlag:%22Yes%22^0.085+newProductFlag:%22Yes%22^0.080+packageTypeCode:%22BKN%22^0.075&_wcf.search.internal.filterquery=-newProductFlag:NPI&q=LM358&intentSearchTerm=LM358&searchTerm=LM358&showMore=true&wt=json