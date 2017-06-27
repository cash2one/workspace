# coding=utf-8


def get_lists():
    ls_test = []
    ll = [1, 2, 3, 4]
    ls_test.append(ll)
    dd = {3: 33, 2: 22, 34: 3344, 5: 55}
    ls_test.append(dd)
    total = []
    for x in range(3):
        ls_test.append(range(x))
        print "*", ls_test
        print "*", id(ls_test)
        # total.append(ls_test)
        yield ls_test
        # print id(total)
        # return total


def look_at_list():
    # l = get_lists()
    for l in get_lists():
        print l
        print id(l)


look_at_list()

"""
结论
列表内部对其他数据对象是直接引用的，如果在循环中append，会导致最后列表都是一样的（引用了同一个）
可以使用yield
"""