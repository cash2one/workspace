# coding=utf-8
import os.path
import Queue
from PIL import Image
from tools import box


def top10_colors(img=None):
    try:
        pixes = img.load()
    except:
        return []
    x, y = img.size


def main_colors(img=None):
    """
    返回8位色图中最多的前十个值
    :param img: Image对象
    :return: 返回列表[(color, times),]
    """
    try:
        img.load()
    except:
        return []
    # (将图片转换为8位像素模式)
    img.convert("P")
    # 颜色直方图的每一位数字都代表了在图片中含有对应位的颜色的像素的数量。
    his = img.histogram()
    value = {}
    # step = 256
    # r_g_b_a = [his[idx: idx+step] for idx in range(0, len(his), step)]
    for i in range(256):
        value[i] = his[i]
    colors = sorted(value.items(), key=lambda x: x[1], reverse=True)[:10]
    return colors


# 通过指定颜色转为二值图
def convert_bw_by_colors(colors=None, img_path=None, cmp_func=None, **kwargs):
    """
    将图片像素颜色和指定颜色列表比较，与颜色列表中颜色相近的颜色的区域填充为黑色，其他区域填充为白色
    :param cmp_func: 比较的颜色的方法
    :param colors: [(R, G, B, Alpha)] 
    :param img_path: 源图片路径
    :return: 转换后的图片路径
    """
    img_path = img_path if img_path else ""
    colors = colors if colors else [(255, 255, 255, 255), ]
    if not img_path:
        return None
    src_img = Image.open(img_path)
    fm = src_img.format
    src_img.convert("P")
    target_img = Image.new("P", src_img.size, 255)

    for x in range(src_img.size[0]):
        for y in range(src_img.size[1]):
            pix = src_img.getpixel((x, y))
            if cmp_func(pix, colors):
                target_img.putpixel((x, y), 0)
    # print target_img.size
    target_path = box.no_space_in_filename("bw_by_colors_", img_path)
    target_img.save(target_path, fm)
    # target_img.show()
    return target_path


# 直接转化为二值图
def convert_bw(img_path=None):
    """
    直接使用pillow的图片模式转换，转换为黑白二值图，效果通常不好
    :param img_path: 源图片的路径
    :return: 返回转换的图片路径
    """
    img_path = img_path if img_path else ''
    if not img_path:
        return None
    img = Image.open(img_path)
    fm = img.format
    img_bw = img.convert('1')
    target_path = box.no_space_in_filename("bw_", img_path)
    img_bw.save(target_path, fm)
    return target_path


def cmp_rpg(color=None, color_list=None, threshold=None):
    """
    比较两种颜色的差距是否在设定的阈值之内
    :param color: (R, G, B, Alpha)
    :param color_list: [(R, G, B, Alpha),]
    :param threshold: 颜色差阈值，默认为80
    :return: bool
    """
    threshold = threshold if threshold else 80
    if not color and not color_list:
        return False
    flag = False
    for clr in color_list:
        flag = True
        for x, y in zip(color, clr):
            if abs(x - y) > threshold:
                flag = False
        if flag:
            return flag
    return flag


# Flood Fill 算法实现抓取验证码文字
def flood_fill(img, x0, y0, blank_color, color_to_fill, cmp_func):
    """
    使用广度优先搜索，从起始点(x0，y0)点开始搜索，将符合blank_color的所有像素点加入集合
    :param img: <class 'PIL.PngImagePlugin.PngImageFile'>
    :param x0: 起始点的x坐标
    :param y0: 起始点的y坐标
    :param blank_color: 参考颜色列表[(R, G, B, Alpha),]
    :param color_to_fill: 填充颜色
    :param cmp_func: 比较颜色的方法
    :return: 像素点的集合set([])
    """
    pix = img.load()
    visited = set()
    q = Queue.Queue()
    q.put((x0, y0))
    visited.add((x0, y0))
    offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    while not q.empty():
        x, y = q.get()
        pix[x, y] = color_to_fill
        for x_offset, y_offset in offsets:
            x1, y1 = x + x_offset, y + y_offset
            if (x1, y1) in visited:
                continue  # 已经访问过了
            visited.add((x1, y1))
            try:
                if cmp_func(pix[x1, y1], blank_color):
                    q.put((x1, y1))
            except IndexError:
                pass
    # img.show()
    return visited


if __name__ == "__main__":
    test_path = r"../test_file/shot.png"
    test_img = Image.open(test_path)
    # print main_colors(test_img)
    convert_bw_by_colors([(49, 255, 255, 255)], test_path, cmp_rpg)
    # chr_rome = flood_fill(test_img, 119, 35, (49, 255, 255, 255), (0, 0, 0, 255), cmp_rpg)
    # chr_rome = flood_fill(test_img, 80, 32, [(49, 255, 255, 255)], (0, 0, 0, 255), cmp_rpg)
    # # print chr_rome
    # max_x = 0
    # min_x = 159
    # max_y = 0
    # min_y = 63
    # for px in chr_rome:
    #     if max_x < px[0]:
    #         max_x = px[0]
    #     elif min_x > px[0]:
    #         min_x = px[0]
    #     elif max_y < px[1]:
    #         max_y = px[1]
    #     elif min_y > px[1]:
    #         min_y = px[1]
    # # print (min_x, min_y)
    # # print (max_x, max_y)
    # img_split = test_img.crop((min_x, min_y, max_x, max_y))
    # img_split.show()
