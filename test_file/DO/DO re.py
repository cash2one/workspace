#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Vin on 2017/4/28
import re

str_for_test = """The DOWNLOADER_MIDDLEWARES setting is merged with the DOWNLOADER_MIDDLEWARES_BASE setting defined in Scrapy (and not meant to be overridden) and then sorted by order to get the final sorted list of enabled middlewares: the first middleware is the one closer to the engine and the last is the one closer to the downloader. In other words, the process_request() method of each middleware will be invoked in increasing middleware order (100, 200, 300, ...) and the process_response() method of each middleware will be invoked in decreasing order.

To decide which order to assign to your middleware see the DOWNLOADER_MIDDLEWARES_BASE setting and pick a value according to where you want to insert the middleware. The order does matter because each middleware performs a different action and your middleware could depend on some previous (or subsequent) middleware being applied.

If you want to disable a built-in middleware (the ones defined in DOWNLOADER_MIDDLEWARES_BASE and enabled by default) you must define it in your project’s DOWNLOADER_MIDDLEWARES setting and assign None as its value. For example, if you want to disable the user-agent middleware:"""


def main():
    # test ^ and $
    pattern_with_dollar_mark = r'^setting$'
    pattern_no_dollar_mark = r'setting'
    rs_search = re.search(pattern_with_dollar_mark, str_for_test)
    rs_match = re.match(pattern_with_dollar_mark, str_for_test)
    print rs_search.group() if rs_search else None
    print rs_match.group() if rs_match else None
    print '=' * 20
    rs_search = re.search(pattern_no_dollar_mark, str_for_test)
    rs_match = re.match(pattern_no_dollar_mark, str_for_test)
    print rs_search.group() if rs_search else None
    print rs_match.group() if rs_match else None


if __name__ == '__main__':
    main()
