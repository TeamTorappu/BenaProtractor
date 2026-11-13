import os
import json

# 检查字符串前面的缩进量
def count_indent(line: str):
    return line.count("\t")

# 将AB的一行读取为类型+变量+数据
def load_line(line: str):
    striped = line.strip()
    if striped.startswith("unsigned "):
        striped = striped[9:]
    if " = " in striped:
        left_part,right_part = striped.split(" = ",1)
        _type,_name = left_part.split(" ",1)
        if _type == "string": # 字符串
            return _type, _name, right_part[1:-1]
        elif _type == "float": # 浮点
            return _type, _name, float(right_part)
        elif _type == "bool": # 布尔
            return _type, _name, (True if right_part == "True" else False)
        elif _type in ["int","UInt8","UInt16","SInt64"]: # 整数、短整数、长整数
            return _type, _name, int(right_part)
        #其他，原路返回
        print("发现未知的类型 "+_type)
        return _type, _name, right_part
    elif " " in striped:
        _type, _name = striped.split(" ",1)
        return _type, _name, None
    else:
        print("无效的数据行："+striped)
        return "", striped, None

# 将AB的数据读取为结构体
def load_as_dict(data,depth: int = 0):
    lines = data if isinstance(data,list) else data.splitlines()
    my_dict = {}
    index = 0
    last_type = ""
    last_key = ""
    inner_mode = False
    inner_start = -1
    if len(lines) == 0:
        return {}
    if lines[0].strip().endswith(" Base"): # 跳过首行
        depth += 1
        index = 0
        del lines[0]
    for line in lines:
        indent = count_indent(line)
        # 检查内嵌套
        if not inner_mode and indent > depth: 
            inner_mode = True
            inner_start = index
        elif inner_mode and indent == depth:
            if last_key == "":
                last_key = "_"
            if lines[inner_start].strip() == "Array Array":
                my_dict[last_key] = load_as_array(lines[inner_start+2:index],depth+2)
            else:
                my_dict[last_key] = load_as_dict(lines[inner_start:index],depth+1)
            last_key = ""
            inner_mode = False
        if indent == depth: # 正常逻辑，每一行都应该是 类型 变量 = 值 或者 类型 变量 的格式
            _type, _key, _var = load_line(line)
            if _var != None:
                my_dict[_key] = _var
            else:
                last_type = _type
                last_key = _key
                
        elif indent < depth: # 缩进小于自身，该返回了
            break
        index += 1
    # 补充处理
    if inner_mode:
        if last_key == "":
            last_key = "_"
        if lines[inner_start].strip() == "Array Array":
            my_dict[last_key] = load_as_array(lines[inner_start+2:index],depth+2)
        else:
            my_dict[last_key] = load_as_dict(lines[inner_start:index],depth+1)
    return my_dict


# 将AB的数据读取为数组
def load_as_array(data,depth: int = 0):
    lines = data if isinstance(data,list) else data.splitlines()
    my_array = []
    index = 0
    last_place = -1
    for line in lines:
        indent = count_indent(line)
        # 检查各项
        if indent == depth: 
            striped = line.strip()
            if striped.startswith("[") and striped.endswith("]"):
                if last_place != -1:
                    if index == last_place+1: # 就相隔1行，说明直接是数据？
                        _type, _name, _var = load_line(lines[last_place])
                        my_array.append(_var)
                    else:
                        my_array.append(load_as_dict(lines[last_place+1:index],depth+1))
                last_place = index+1
        index += 1
    if last_place != -1:
        if index == last_place+1: # 就相隔1行，说明直接是数据？
            _type, _name, _var = load_line(lines[last_place])
            my_array.append(_var)
        else:
            my_array.append(load_as_dict(lines[last_place+1:index],depth+1))
    return my_array

# 读取AB文件
def load_file(file_path):
    if not os.path.exists(file_path):
        print("路径不存在："+file_path)
        return {}
    else:
        print("读取文件："+file_path)
        with open(file_path,"r") as _f:
            data = _f.read()
        return load_as_dict(data)
# 测试用
if __name__ == "__main__":
    data = ""
    test_path = "./MonoBehaviour/GlobalBuff #5876.txt"
    data_dict = load_file(test_path)
    print(json.dumps(data_dict, indent=4, ensure_ascii=False))
    
        