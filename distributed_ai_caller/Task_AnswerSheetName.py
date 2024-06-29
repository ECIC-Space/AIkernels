import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks


def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return img, gray, binary


def extract_number_area(binary):
    h, w = binary.shape
    right_half = binary[:, w // 2:]
    contours, _ = cv2.findContours(right_half, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    number_area_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(number_area_contour)
    x += binary.shape[1] // 2
    number_area = binary[y:y + h, x:x + w]
    return number_area, (x, y, w, h)


def detect_vertical_lines(number_area):
    edges = cv2.Canny(number_area, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=number_area.shape[0] * 0.9,
                            maxLineGap=10)

    if lines is None:
        return find_vertical_lines_alternative(number_area)

    vertical_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(x2 - x1) < 10:  # 假设垂直线的倾斜度很小
            vertical_lines.append((x1 + x2) // 2)

    vertical_lines = sorted(set(vertical_lines))

    if len(vertical_lines) < 7:
        return find_vertical_lines_alternative(number_area)

    return vertical_lines[:7]  # 返回前7条线（6个数字列 + 右边界）


def find_vertical_lines_alternative(number_area):
    # 计算垂直投影
    vertical_projection = np.sum(number_area, axis=0)

    # 使用峰值检测找到可能的垂直线位置
    peaks, _ = find_peaks(-vertical_projection, distance=number_area.shape[1] // 7)

    # 如果检测到的峰值少于7个，我们平均分割图像
    if len(peaks) < 7:
        peaks = np.linspace(0, number_area.shape[1], 8)[:-1].astype(int)

    return peaks[:7]


def split_into_columns(number_area, vertical_lines):
    columns = []
    for i in range(len(vertical_lines) - 1):
        column = number_area[:, vertical_lines[i]:vertical_lines[i + 1]]
        columns.append(column)
    return columns


def find_digit_positions(column):
    row_means = np.mean(column, axis=1)
    peaks, _ = find_peaks(-row_means, distance=column.shape[0] // 11)

    if len(peaks) < 10:
        peaks = np.linspace(0, column.shape[0], 11)[:-1].astype(int)

    return peaks[:10]


def recognize_number(columns):
    result = ""
    for column in columns:
        positions = find_digit_positions(column)
        max_filled = 0
        max_index = 0
        for i, pos in enumerate(positions):
            if i < len(positions) - 1:
                cell = column[pos:positions[i + 1], :]
            else:
                cell = column[pos:, :]
            filled_ratio = cv2.countNonZero(cell) / cell.size
            if filled_ratio > max_filled:
                max_filled = filled_ratio
                max_index = i
        result += str(max_index)
    return result


def visualize_steps(original, gray, binary, number_area, columns, exam_number, vertical_lines):
    plt.figure(figsize=(20, 15))

    plt.subplot(231), plt.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
    plt.title('Original Image'), plt.axis('off')

    plt.subplot(232), plt.imshow(gray, cmap='gray')
    plt.title('Grayscale Image'), plt.axis('off')

    plt.subplot(233), plt.imshow(binary, cmap='gray')
    plt.title('Binary Image'), plt.axis('off')

    plt.subplot(234), plt.imshow(number_area, cmap='gray')
    plt.title('Extracted Number Area'), plt.axis('off')

    grid_img = number_area.copy()
    for x in vertical_lines:
        cv2.line(grid_img, (x, 0), (x, grid_img.shape[0]), (255, 0, 0), 2)
    plt.subplot(235), plt.imshow(grid_img, cmap='gray')
    plt.title('Detected Vertical Lines'), plt.axis('off')

    plt.subplot(236), plt.text(0.5, 0.5, f'Recognized Number: {exam_number}',
                               horizontalalignment='center', verticalalignment='center', fontsize=20)
    plt.axis('off')

    plt.tight_layout()
    plt.savefig('recognition_steps.png')
    plt.close()


def main(image_path):
    original, gray, binary = preprocess_image(image_path)
    number_area, (x, y, w, h) = extract_number_area(binary)
    vertical_lines = detect_vertical_lines(number_area)
    columns = split_into_columns(number_area, vertical_lines)
    exam_number = recognize_number(columns)

    visualize_steps(original, gray, binary, number_area, columns, exam_number, vertical_lines)

    print(f"识别出的考号是: {exam_number}")
    print("处理步骤的可视化结果已保存为 'recognition_steps.png'")


# 使用示例
# main('path_to_your_image.jpg')
if __name__ == '__main__':
    main("./output/1.jpg/corrected_column_1.jpg")