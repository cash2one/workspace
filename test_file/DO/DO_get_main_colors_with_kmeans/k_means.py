# coding=utf-8
# 导入必要的库
from sklearn.cluster import KMeans  # 这里用scikit-learn库中的K-Means算法
import matplotlib.pyplot as plt  # 使用matplotlib显示图片
import argparse  # 用argparse解析命令行参数
import utils
import cv2  # 导入OpenCV库

# 解析命令行参数  -i指定图片  -c表示要产生几个主要颜色
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="Path to the image")
ap.add_argument("-c", "--clusters", required=True, type=int,
                help="# of clusters")
args = vars(ap.parse_args())

# 加载图片并从BGR转为RGB，matplotlib需要RGB格式
image = cv2.imread(args["image"])
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# 显示原始图片
plt.figure()
plt.axis("off")
plt.imshow(image)

# 把mxn的矩阵像素转为一维像素
image = image.reshape((image.shape[0] * image.shape[1], 3))
# <type 'numpy.ndarray'>
# print type(image)

# 使用KMeans算法找到图片的主要颜色
clt = KMeans(n_clusters=args["clusters"])
clt.fit(image)

# 在utils.py中定义，绘制主要颜色条
hist = utils.centroid_histogram(clt)
bar = utils.plot_colors(hist, clt.cluster_centers_)

# 显示
plt.figure()
plt.axis("off")
plt.imshow(bar)
plt.show()