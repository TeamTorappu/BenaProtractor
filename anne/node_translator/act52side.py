#----------------------------------------
# 昨日海相关Node
#----------------------------------------
from dictionary import enum_dictionary
from analyzer import to_percent

# 修改颜色
def Act52(node,blackboard):
    target_name = enum_dictionary("target",node["_targetType"])
