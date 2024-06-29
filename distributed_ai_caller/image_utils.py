import base64
import cv2
import numpy as np


def preprocess_image(image):
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result=gray
    # # 应用中值滤波来减少噪声，同时保留边缘
    # median = cv2.medianBlur(gray, 5)
    #
    # 使用自适应阈值处理，参数调整以更好地处理不均匀照明
    # thresh = cv2.adaptiveThreshold(median, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV, 21, 10)
    # closing=thresh
    #
    # # 应用开运算来去除小噪点
    # kernel = np.ones((2, 2), np.uint8)
    # opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    #
    # # 应用闭运算来填充字符中的小空洞
    # kernel = np.ones((3, 3), np.uint8)
    # closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=1)
    #
    # # 反转图像颜色
    # result = cv2.bitwise_not(closing)

    return result


def image_to_base64(file_path):
    # 读取图像
    image = cv2.imread(file_path)
    if image is None:
        print(f"错误：无法读取图像文件 '{file_path}'")
        return None

    # 预处理图像
    # enhanced = preprocess_image(image)
    enhanced=image
    # 显示原图和处理后的图像
    # cv2.imshow('Original Image', image)
    # cv2.imshow('Enhanced Image', enhanced)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # 将处理后的图像编码为 base64
    _, buffer = cv2.imencode('.jpg', enhanced)
    return base64.b64encode(buffer).decode('utf-8')


if __name__ == '__main__':
    file_path = r".\output\1.jpg\corrected_column_2.jpg"  # 请替换为实际的图像路径
    base64_string = image_to_base64(file_path)
    if base64_string:
        print("Base64 encoded string of the enhanced image:")
        print(base64_string[:100] + "...")  # 只打印前100个字符