产品筛选参数
Get http://www.ti.com/wsapi/paramdata/family/3170/criteria?lang=en&output=json
http://www.ti.com/wsapi/paramdata/family/3523/criteria?lang=en&output=json
列表信息中对应的title在筛选参数中

产品列表信息
Get http://www.ti.com/wsapi/paramdata/family/3170/results?lang=en&output=json
http://www.ti.com/wsapi/paramdata/family/3523/results?lang=en&output=json

搜索
http://www.ti.com/sitesearch/docs/productsnapshot.tsp?partNumber=lm358
http://www.ti.com/sitesearch/docs/universalsearch.tsp?searchTerm=INA
全部搜索结果
http://www.ti.com/sitesearch/docs/universalsearch.tsp?searchTerm=lm358#linkId=2
http://www.ti.com/sitesearch/docs/universalsearch.tsp?searchTerm=INA#linkId=2
搜索结果获取及翻页
http://www.ti.com/sitesearch/docs/partnumsearch.tsp?linkId=2&filter=p&searchTerm=INA&startNum=50&sortBy=pstatus&sort=asc
产品查询
http://www.ti.com/sitesearch/docs/partnumsearch.tsp?linkId=2&filter=p&searchTerm=OPA&startNum=0&sortBy=pstatus&sort=asc



header={
	'Accept': "*/*",
	"Accept-Encoding": "gzip, deflate, sdch",
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36",
}


结构
http://www.ti.com/
产品目录url
http://www.ti.com/lsds/ti/amplifiers/amplifiers-overview.page
/lsds/ti/.*overview\.page
获取目录命和ID
tiContentGroup = "/microcontrollers (mcu)/"
tiProductPathID = "/4/"
<script language="JavaScript">
        	    	var tiContentGroup;
            		tiContentGroup = "/microcontrollers (mcu)/";
        </script>
<script language="JavaScript">
        	    	var tiProductPathID;
        	    	tiProductPathID = "/4/";
        </script>
构造请求产品数据请求url
http://www.ti.com/wsapi/paramdata/family/4/criteria?lang=en&output=json
http://www.ti.com/wsapi/paramdata/family/4/results?lang=en&output=json

库存查询
https://store.ti.com/Search.aspx?k=CC430F5123&pt=-1

!!!!产品库存列表!!!!
http://www.ti.com/product/lm71-q1/samplebuy

价格和购买量
https://store.ti.com/TMP75CQDGKRQ1.aspx
