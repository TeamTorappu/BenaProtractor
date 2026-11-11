#----------------------------------------
# 拆分活动表（因为实在是太大了，不适合一直存在内存里）
#----------------------------------------

# 读取activity_table.json，将获取到的名称制作成若干单独的json以供使用。
import json

from app_paths import app_path

REASONABLE_ACTIVITIES = {
    #"AUTOCHESS" : "activity_table_autochess.json", # 卫戍协议另起炉灶
    #"ARCADE" : "activity_table_arcade.json",
    #"ARK_HUB" : "activity_table_ark_hub.json",
    #"BOSS_RUSH" : "activity_table_boss_rush.json",
    "VEC_BREAK_V2" : "activity_table_vec_break_v2.json",
    #"ACT_FOOTBALL" : "activity_table_act_football.json",
    "ENEMY_DUEL" : "activity_table_enemy_duel.json",
    #"HALFIDLE_VERIFY1" : "activity_table_halfidle_verify1.json",
}

def split_activity_table():
    print(f"[贝娜]开始读取activity_table.json")
    # 获取文件数据
    activity_data = None
    autochess_data = None
    with open(app_path("tables","activity_table.json"),'r',encoding="UTF-8") as _f:
        json_data = json.load(_f)
        print(f"[贝娜]尝试将活动数据拆分记录至activity_table_xxxxxx.json")
        activity_data = json_data["activity"]
        autochess_data = json_data["autoChessData"]
    # 拆分写入子文件便于未来使用
    if "AUTOCHESS" in activity_data:
        with open(app_path("table_dummies","activity_table_autochess.json") ,'w',encoding="UTF-8") as _f:
            json_data = {
                "activity" : activity_data["AUTOCHESS"],
                "autoChessData" : autochess_data
            }
            _f.write(json.dumps(json_data,indent=4,ensure_ascii=False))
    # 卫戍协议以外的其他
    for act, path in REASONABLE_ACTIVITIES.items():
        if act in activity_data:
            with open(app_path("table_dummies",path) ,'w',encoding="UTF-8") as _f:
                _f.write(json.dumps(activity_data[act],indent=4,ensure_ascii=False))
    print(f"[贝娜]activity_table.json拆分完毕！")