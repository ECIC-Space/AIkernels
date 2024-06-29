import os
import shutil

# 创建reviews文件夹
os.makedirs("./reviews", exist_ok=True)

# 用于跟踪处理的文件数量
processed_files = 0

# 遍历output文件夹
for folder_name in os.listdir("../distributed_ai_caller/output"):
    folder_path = os.path.join("../distributed_ai_caller/output", folder_name)

    # 检查是否为目录且不以"err-"开头
    if os.path.isdir(folder_path) and not folder_name.startswith("err-"):
        detected_columns_path = os.path.join(folder_path, "detected_columns.jpg")

        # 检查detected_columns.jpg是否存在
        if os.path.exists(detected_columns_path):
            # 从文件夹名称中提取序号（去掉.jpg后缀）
            original_number = folder_name.rstrip('.jpg')

            # 构造新的文件名，保持原始序号
            new_filename = f"{original_number}-detected_columns.jpg"

            # 复制文件到reviews文件夹
            shutil.copy(detected_columns_path, os.path.join("./reviews", new_filename))

            print(f"Copied {detected_columns_path} to ./reviews/{new_filename}")

            processed_files += 1

print(f"Processed {processed_files} normal files. Review images are saved in ./reviews folder.")