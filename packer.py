import zipfile
import os
import datetime

def add_folder_to_zip(zip_file, folder_name):
    for root, dirs, files in os.walk("./"+folder_name):
        for file in files:
            file_path = os.path.join(root, file)
            zip_file.write(file_path)

#创建压缩包并删除
if __name__ == "__main__":
    if not os.path.exists("output"):
        os.makedirs("output")
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    day = now.day
    with zipfile.ZipFile(f"output/贝娜的量角器 {year}.{month}.{day}.zip", 'w') as _z:
        _z.write("./dist/main.exe","./贝娜的量角器.exe")
        _z.write("./icon/icon.ico","./icon/icon.ico")
        add_folder_to_zip(_z,"data")
        add_folder_to_zip(_z,"tables")
        add_folder_to_zip(_z,"translation")