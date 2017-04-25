#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/4/21

"""

"""
import urlparse


def main():
    test_url1 = 'https://www.microchipdirect.com/ProductSearch.aspx?keywords=PIC16LF1789-E/P'
    test_url2 = 'http://www.microchipdirect.com/ProductDetails.aspx?Catalog=BuyMicrochip&Category=AT40K40&mid=10'
    result1 = urlparse.urlsplit(test_url1)
    result2 = urlparse.urlsplit(test_url2)
    print(result1)
    print(result2)


if __name__ == '__main__':
    main()
