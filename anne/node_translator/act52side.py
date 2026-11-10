#----------------------------------------
# 昨日海相关Node
#----------------------------------------
from dictionary import anne_dictionary
from analyzer import to_percent

# 修改颜色
def Act52(node,blackboard):
    target_name = anne_dictionary("target",node["_targetType"])
