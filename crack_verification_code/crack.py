# -*- coding:utf8 -*-
import os
import time
import math
import random
import string
import hashlib
from PIL import Image


class VectorCompare(object):
    # 计算矢量大小
    def vector_norm(self, concordance):
        total = 0
        for word, count in concordance.iteritems():
            total += count ** 2
        return math.sqrt(total)

    # 计算矢量之间的 cos 值
    def relation(self, concordance1, concordance2):
        relevance = 0
        inner_product = 0
        for word, count in concordance1.iteritems():
            if word in concordance2:
                inner_product += count * concordance2[word]
        return inner_product / (self.vector_norm(concordance1) * self.vector_norm(concordance2))


def img_main_colors(img_path=None):
    img_path = img_path if img_path else ""
    if not img_path:
        return []
    im = Image.open(img_path)
    # (将图片转换为8位像素模式)
    im.convert("P")
    # 颜色直方图的每一位数字都代表了在图片中含有对应位的颜色的像素的数量。
    his = im.histogram()
    value = {}
    for i in range(256):
        value[i] = his[i]
    main_colors = sorted(value.items(), key=lambda x: x[1], reverse=True)[:10]
    return main_colors


def convert_bw(colors=None, img_path=None):
    img_path = img_path if img_path else ""
    colors = colors if colors else [0, 255]
    if not img_path:
        return None
    src_img = Image.open(img_path)
    src_img.convert("P")
    target_img = Image.new("P", src_img.size, 255)

    for x in range(src_img.size[0]):
        for y in range(src_img.size[1]):
            pix = src_img.getpixel((x, y))
            if pix == colors[0] or pix == colors[1]:
                target_img.putpixel((x, y), 0)
    # print target_img.size
    target_path = "bw_" + img_path
    target_img.save(target_path, "GIF")
    return target_path


def vector(im):
    d, count = {}, 0
    for i in im.getdata():
        d[count] = i
        count += 1
    return d


def cut_img(img_path=None):
    img_path = img_path if img_path else ""
    if not img_path:
        yield None
    src_img = Image.open(img_path)
    left_border = False
    right_border = False
    letters = list()
    start, end = 0, 0
    for x in range(src_img.size[0]):
        for y in range(src_img.size[1]):
            pix = src_img.getpixel((x, y))
            if not pix == 1:
                left_border = True
        if left_border is True and right_border is False:
            right_border = True
            start = x

        if right_border is True and left_border is False:
            right_border = False
            end = x
            letters.append((start, end))
        left_border = False
    for letter in letters:
        # m = hashlib.md5()
        # .crop((box))
        # box: (left, upper, right, lower) - tuple
        img_split = src_img.crop((letter[0], 0, letter[1], src_img.size[1]))
        # m.update("%s%s" % (time.time(), random.random()))
        # img_split.save("./%s.gif" % (m.hexdigest()))
        # print vector(img_split)
        yield img_split


if __name__ == "__main__":
    # 测试图片
    img = 'captcha.gif'
    img_main_colors(img)
    target = convert_bw([220, 227], img)
    test_list = cut_img(target)
    # 训练集
    icon_set = list(string.printable)[:36]
    image_set = []
    for digit in icon_set:
        for img in os.listdir('./iconset/%s/' % digit):
            temp = []
            if img != "Thumbs.db" and img != ".DS_Store":
                temp.append(vector(Image.open("./iconset/%s/%s" % (digit, img))))
            image_set.append({digit: temp})

    # 对比向量夹角
    V = VectorCompare()
    for test_img in test_list:
        guess = []
        for im in image_set:
            for digit, temp in im.iteritems():
                if temp:
                    guess.append((V.relation(temp[0], vector(test_img)), digit))
        print sorted(guess, key=lambda x: x[0], reverse=True)[0]