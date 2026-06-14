import os
import sys
import urllib.request

# Github仓库的根文件夹
#WEB = "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/refs/heads/master/zh_CN/gamedata/"
#WEB = "https://torappu.prts.wiki/gamedata/latest/"
WEB = "https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/refs/heads/master/cn/gamedata/"
# 需要下载的文件
# 以简体中文版数据为准（通常会是最新的）
FILES = {
    "buff_table.json" : "buff_table.json",
    "character_table.json" : "excel/character_table.json",
    "roguelike_topic_table.json" : "excel/roguelike_topic_table.json",
    "buff_template_data.json" : "battle/buff_template_data.json",
    "enemy_database.json" : "levels/enemydata/enemy_database.json"
}

# 下载所需文件
def prepare_files():
    def _progress(block_num,block_size,total_size):
        progress = min(float(block_num * block_size) / float(total_size),1.0) * 100.0
        sys.stdout.write("\r[贝娜]下载进度" + "{:.2f}%".format(progress))
        sys.stdout.flush()
    # 创建文件夹
    if not os.path.exists("./tables"):
        os.mkdir("./tables")
    
    # 遍历所需文件
    for name, url in FILES.items():
        if not os.path.exists("./tables/"+name):
            print("[贝娜]没找到本地的 "+name)
            print("[贝娜]尝试从网络下载...（如果下载较慢，建议尝试启用网络代理（俗称梯子））")
            try:
                urllib.request.urlretrieve(WEB+url,"./tables/"+name,_progress)
                print("")
                print("[贝娜]"+name+" 下载完成！")
            except:
                print("[贝娜]"+name+" 下载失败... 请检查联网状态")
                if os.path.exists("./tables/"+name):
                    os.remove("./tables/"+name)
                raise IOError("[贝娜]缺少文件，无法处理")