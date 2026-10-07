#----------------------------------------
# GlobalBuff相关Node
#----------------------------------------
from dictionary import anne_dictionary

# 将某个Globalbuff的黑板值誊写到自己黑板上
def AssignGlobalBuffBlackboardToBB(node,blackboard):
    return {
        "main" : f"寻找名为 <global_buff|{node['_globalBuffKey']}> 的GlobalBuff，将其黑板上的 [{node['_globalBuffBlackboardKey']}] 誊写至本Buff黑板的 [{node['_blackboardKey']}]"
    }