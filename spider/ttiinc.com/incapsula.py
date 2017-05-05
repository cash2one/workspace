# coding=utf-8
import re
import urlparse as util
import random
import requests
import json
proxy = {
    'http': 'http://115.28.88.238:8080',
    'https': 'https://115.28.88.238:8083',
}

default_headers = {
    'Host': 'www.ttiinc.com',
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json;charset=UTF-8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.ttiinc.com/content/ttiinc/en/apps/part-search.html?manufacturers=&searchTerms=&systemsCatalog=254428',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
}


def broken(proxy=None, **kwargs):
    _headers = default_headers
    url = 'https://www.ttiinc.com/content/ttiinc/en/apps/part-detail.html?mfrShortname=PUL&partsNumber=H5120NL&customerPartNumber=&minQty=5&customerId='
    session = requests.Session()
    proxies = kwargs.get('proxies')
    if proxies is None and proxy:
        i = random.randint(0, proxy[0] - 1)
        proxies = {
            'http': 'http://' + proxy[1][i],
            'https': 'http://' + proxy[1][i],
        }

    tti = session.get(url, headers=_headers, timeout=30, proxies=proxies)
    js_cookies = {}
    for vo in tti.cookies:
        js_cookies[vo.name] = vo.value
    tti = session.get(url, headers=_headers, cookies=js_cookies, timeout=30, proxies=proxies)
    js_cookies = _parse_incapsula_page(tti.text, cookies=js_cookies, headers=_headers, session=session, proxies=proxies)
    # 解析链接
    data = {"mfrShortname": "PUL", "partNumber": "H5120NL", "thirdParty": True}
    process_data = re.search(r'mfrShortname=(.*)&partsNumber=(.*)&customerPartNumber=(.*)&minQty=(.*)&customerId=(.*)',
                             url)
    data['mfrShortname'] = process_data.group(1)
    data['partNumber'] = process_data.group(2)
    process_url = 'https://www.ttiinc.com/bin/services/processData?jsonPayloadAvailable=true&osgiService=partdetailpost'
    resp = session.post(url=process_url, data=json.dumps(data), headers=_headers, timeout=30, proxies=proxies,
                         cookies=js_cookies)
    return resp.content


def _parse_incapsula_page(text, **kwargs):
    """解析incapsula cdn验证跳转页面"""
    match = re.search('var\s+b\s*=\s*"([^"]+)', text)
    if not match:
        return None
    # print('解析incapsula cdn验证跳转页面中......')
    content = match.group(1).decode('hex')
    match = re.search('\s*"(/_Incapsula[^"]+)', content)
    if not match:
        return None
    js_cookies = kwargs.get('cookies', {})
    url = util.urljoin('https://www.ttiinc.com/', match.group(1))
    if 'url' in kwargs:
        del kwargs['url']
    proxies = kwargs.get('proxies')
    if 'session' in kwargs:
        session = kwargs['session']
        print type(session)
        # rs = fetcher(url, return_response=1, **kwargs)
        rs = session.get(url=url, headers=default_headers, proxies=proxies)
        with open('rs.html', 'w') as fp:
            fp.write(rs.content)
    else:
        rs = fetcher(url, return_response=1, **kwargs)
    if not rs:
        return None
    for vo in rs.cookies:
        js_cookies[vo.name] = vo.value
    return js_cookies




def fetcher(url, data=None, **kwargs):
    '''获取URL数据'''
    global _headers
    if kwargs.get('headers'):
        _headers = kwargs['headers']
    cookies = kwargs.get('cookies')
    proxies = kwargs.get('proxies')
    timeout = kwargs.get('timeout', 30)
    _page = ''
    if 'page' in kwargs:
        _page = '; Page : %s' % kwargs['page']
    try:
        if 'method' in kwargs:
            method = kwargs['method']
        else:
            method = 'GET' if data is None else 'POST'
        rs = requests.request(method, url, data=data, headers=_headers, cookies=cookies,
                              proxies=proxies, timeout=timeout)
    except Exception as e:
        print('请求异常 ; %s' % e)
        return None

    if rs.status_code != 200:
        print('数据请求异常，网页响应码: %s ; URL: %s' % (rs.status_code, url))
        return None

    if 'return_response' in kwargs:
        return rs
    return rs.text


if __name__ == "__main__":
    t = """
    <html>
<head>
<META NAME="robots" CONTENT="noindex,nofollow">
<script>
(function(){function getSessionCookies(){var cookieArray=new Array();var cName=/^\s?incap_ses_/;var c=document.cookie.split(";");for(var i=0;i<c.length;i++){var key=c[i].substr(0,c[i].indexOf("="));var value=c[i].substr(c[i].indexOf("=")+1,c[i].length);if(cName.test(key)){cookieArray[cookieArray.length]=value}}return cookieArray}function setIncapCookie(vArray){var res;try{var cookies=getSessionCookies();var digests=new Array(cookies.length);for(var i=0;i<cookies.length;i++){digests[i]=simpleDigest((vArray)+cookies[i])}res=vArray+",digest="+(digests.join())}catch(e){res=vArray+",digest="+(encodeURIComponent(e.toString()))}createCookie("___utmvc",res,20)}function simpleDigest(mystr){var res=0;for(var i=0;i<mystr.length;i++){res+=mystr.charCodeAt(i)}return res}function createCookie(name,value,seconds){var expires="";if(seconds){var date=new Date();date.setTime(date.getTime()+(seconds*1000));var expires="; expires="+date.toGMTString()}document.cookie=name+"="+value+expires+"; path=/"}function test(o){var res="";var vArray=new Array();for(var j=0;j<o.length;j++){var test=o[j][0];switch(o[j][1]){case"exists":try{if(typeof(eval(test))!="undefined"){vArray[vArray.length]=encodeURIComponent(test+"=true")}else{vArray[vArray.length]=encodeURIComponent(test+"=false")}}catch(e){vArray[vArray.length]=encodeURIComponent(test+"=false")}break;case"value":try{try{res=eval(test);if(typeof(res)==="undefined"){vArray[vArray.length]=encodeURIComponent(test+"=undefined")}else if(res===null){vArray[vArray.length]=encodeURIComponent(test+"=null")}else{vArray[vArray.length]=encodeURIComponent(test+"="+res.toString())}}catch(e){vArray[vArray.length]=encodeURIComponent(test+"=cannot evaluate");break}break}catch(e){vArray[vArray.length]=encodeURIComponent(test+"="+e)}case"plugin_extentions":try{var extentions=[];try{i=extentions.indexOf("i")}catch(e){vArray[vArray.length]=encodeURIComponent("plugin_ext=indexOf is not a function");break}try{var num=navigator.plugins.length;if(num==0||num==null){vArray[vArray.length]=encodeURIComponent("plugin_ext=no plugins");break}}catch(e){vArray[vArray.length]=encodeURIComponent("plugin_ext=cannot evaluate");break}for(var i=0;i<navigator.plugins.length;i++){if(typeof(navigator.plugins[i])=="undefined"){vArray[vArray.length]=encodeURIComponent("plugin_ext=plugins[i] is undefined");break}var filename=navigator.plugins[i].filename;var ext="no extention";if(typeof(filename)=="undefined"){ext="filename is undefined"}else if(filename.split(".").length>1){ext=filename.split('.').pop()}if(extentions.indexOf(ext)<0){extentions.push(ext)}}for(i=0;i<extentions.length;i++){vArray[vArray.length]=encodeURIComponent("plugin_ext="+extentions[i])}}catch(e){vArray[vArray.length]=encodeURIComponent("plugin_ext="+e)}break}}vArray=vArray.join();return vArray}var o=[["navigator","exists"],["navigator.vendor","value"],["navigator.appName","value"],["navigator.plugins.length==0","value"],["navigator.platform","value"],["navigator.webdriver","value"],["platform","plugin_extentions"],["ActiveXObject","exists"],["webkitURL","exists"],["_phantom","exists"],["callPhantom","exists"],["chrome","exists"],["yandex","exists"],["opera","exists"],["opr","exists"],["safari","exists"],["awesomium","exists"],["puffinDevice","exists"],["__nightmare","exists"],["_Selenium_IDE_Recorder","exists"],["document.__webdriver_script_fn","exists"],["document.$cdc_asdjflasutopfhvcZLmcfl_","exists"],["process.version","exists"],["navigator.cpuClass","exists"],["navigator.oscpu","exists"],["navigator.connection","exists"],["window.outerWidth==0","value"],["window.outerHeight==0","value"],["window.WebGLRenderingContext","exists"],["document.documentMode","value"],["eval.toString().length","value"]];try{setIncapCookie(test(o));document.createElement("img").src="/_Incapsula_Resource?SWKMTFSR=1&e="+Math.random()}catch(e){img=document.createElement("img");img.src="/_Incapsula_Resource?SWKMTFSR=1&e="+e}})();
</script>
<script>
(function() { 
var z="";var b="7472797B766172207868723B76617220743D6E6577204461746528292E67657454696D6528293B766172207374617475733D227374617274223B7661722074696D696E673D6E65772041727261792833293B77696E646F772E6F6E756E6C6F61643D66756E6374696F6E28297B74696D696E675B325D3D22723A222B286E6577204461746528292E67657454696D6528292D74293B646F63756D656E742E637265617465456C656D656E742822696D6722292E7372633D222F5F496E63617073756C615F5265736F757263653F4553324C555243543D363726743D373826643D222B656E636F6465555249436F6D706F6E656E74287374617475732B222028222B74696D696E672E6A6F696E28292B222922297D3B69662877696E646F772E584D4C4874747052657175657374297B7868723D6E657720584D4C48747470526571756573747D656C73657B7868723D6E657720416374697665584F626A65637428224D6963726F736F66742E584D4C4854545022297D7868722E6F6E726561647973746174656368616E67653D66756E6374696F6E28297B737769746368287868722E72656164795374617465297B6361736520303A7374617475733D6E6577204461746528292E67657454696D6528292D742B223A2072657175657374206E6F7420696E697469616C697A656420223B627265616B3B6361736520313A7374617475733D6E6577204461746528292E67657454696D6528292D742B223A2073657276657220636F6E6E656374696F6E2065737461626C6973686564223B627265616B3B6361736520323A7374617475733D6E6577204461746528292E67657454696D6528292D742B223A2072657175657374207265636569766564223B627265616B3B6361736520333A7374617475733D6E6577204461746528292E67657454696D6528292D742B223A2070726F63657373696E672072657175657374223B627265616B3B6361736520343A7374617475733D22636F6D706C657465223B74696D696E675B315D3D22633A222B286E6577204461746528292E67657454696D6528292D74293B6966287868722E7374617475733D3D323030297B706172656E742E6C6F636174696F6E2E72656C6F616428297D627265616B7D7D3B74696D696E675B305D3D22733A222B286E6577204461746528292E67657454696D6528292D74293B7868722E6F70656E2822474554222C222F5F496E63617073756C615F5265736F757263653F535748414E45444C3D363836393338363033313036313935323832352C313736323032353133303135343532303831392C313938303933393230383437333033383939342C363638353835222C66616C7365293B7868722E73656E64286E756C6C297D63617463682863297B7374617475732B3D6E6577204461746528292E67657454696D6528292D742B2220696E6361705F6578633A20222B633B646F63756D656E742E637265617465456C656D656E742822696D6722292E7372633D222F5F496E63617073756C615F5265736F757263653F4553324C555243543D363726743D373826643D222B656E636F6465555249436F6D706F6E656E74287374617475732B222028222B74696D696E672E6A6F696E28292B222922297D3B";for (var i=0;i<b.length;i+=2){z=z+parseInt(b.substring(i, i+2), 16)+",";}z = z.substring(0,z.length-1); eval(eval('String.fromCharCode('+z+')'));})();
</script></head>
<body>
<iframe style="display:none;visibility:hidden;" src="//content.incapsula.com/jsTest.html" id="gaIframe"></iframe>
</body></html>
    """
    # print translate(t)
    # session = requests.Session()
    # tti = session.get(url='https://www.ttiinc.com/content/ttiinc/en.html', headers=default_headers)
    # print tti.text
    # js_cookies = {}
    # for vo in tti.cookies:
    #     js_cookies[vo.name] = vo.value
    # print js_cookies
    session = requests.Session()
    tti = session.get(url='https://www.ttiinc.com/content/ttiinc/en.html', headers=default_headers, timeout=30)
    print tti.text
    js_cookies = {}
    for vo in tti.cookies:
        js_cookies[vo.name] = vo.value
    tti = session.get(url='https://www.ttiinc.com/content/ttiinc/en.html', headers=default_headers, cookies=js_cookies, timeout=30)
    print tti.text
    js_cookies = _parse_incapsula_page(tti.text, cookies=js_cookies, headers=default_headers, session=session)
