import pic_4pCorrect
import cv2
import numpy as np
import os

# 逐个遍历文件夹中的图片
for root, dirs, files in os.walk("./target"):
    for file in files:
        if file.endswith(".jpg"):
            image_path = os.path.join(root, file)
            image = cv2.imread(image_path)
            print("Processing:", image_path)
            # 调用函数
            result = pic_4pCorrect.multi_column_correction(image, min_area=5000, max_contours=6, visualize=True)
            print("Saving results for:", image_path)


            if len(result) == 2:
                corrected_columns, vis_image = result
                # cv2.imwrite(f"detected_columns_{file}", vis_image)
                # 在output文件夹中创建对应的文件夹
                os.makedirs(f"output/{file}", exist_ok=True)
                # 将文件写入到output中的{file}子文件夹中
                cv2.imwrite(f"output/{file}/detected_columns.jpg", vis_image)
            else:
                corrected_columns = result

            # 保存每个矫正后的列
            for i, column in enumerate(corrected_columns):
                # cv2.imwrite(f"corrected_column_{file}_{i + 1}.jpg", column)
                cv2.imwrite(f"output/{file}/corrected_column_{i + 1}.jpg", column)

            # 输出保存了多少文件
            print("Saved", len(corrected_columns) + 1, "files")

            # 如果保存文件不是7个，则标记为异常
            if len(corrected_columns) + 1 != 7:
                print("Anomaly detected in", image_path)
                # 重命名文件夹为err-原名
                os.rename(f"output/{file}", f"output/err-{file}")
            print("=" * 50)

