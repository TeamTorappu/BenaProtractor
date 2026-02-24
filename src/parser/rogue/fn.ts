import type { TreeOption } from 'naive-ui'
import { typeNameMap } from '@/composables/useRogue'
import { loadPublicJSON } from '@/composables/usePublic'
/* ── 增强上下文：schema parse 函数可通过它递归构建子树 ── */

export interface ParseCtx {
    /** 是否展示全部 */
    showAll: boolean
    /** 当前字段的 key 路径 */
    baseKey: string
    /** 所属 action 对象 */
    action?: Record<string, unknown>
    /** 顶层 buff 对象 */
    buff?: Record<string, unknown>
    /** 递归构建带 $type 的 action 节点 */
    buildAction: (node: Record<string, unknown>, key: string, prefix?: string) => Promise<TreeOption>
    /** 递归构建普通 object / array */
    buildNested: (value: unknown, key: string, label: string) => Promise<TreeOption>
}

export const fnMap: Map<string, Function> = new Map()

/** 递归标记整棵子树为 display: false */
function markHidden(node: TreeOption): TreeOption {
    return {
        ...node,
        display: false,
        children: node.children?.map(markHidden),
    }
}

/* ── 标量解析函数（返回 string） ── */

export async function parseNumber($input: number, _$ctx: any): Promise<number> {
    return $input
}
fnMap.set('parseNumber', parseNumber)

export async function parseBoolean($input: boolean, _$ctx: any): Promise<string> {
    return $input ? '是' : '否'
}
fnMap.set('parseBoolean', parseBoolean)

export async function parseRogueType($input: string, _$ctx: any): Promise<string> {
    return $input + " | " + (typeNameMap[$input] || "鸽物");
}
fnMap.set('parseRogueType', parseRogueType)

export async function parseRarity(_value: any, valueStr: string): Promise<string> {
    if (typeof valueStr !== 'string') return String(valueStr);
    if (['NORMAL', 'RARE', 'SUPER_RARE'].includes(valueStr)) {
        return valueStr;
    }
    const tierMap: Record<string, string> = { '1': '一星', '2': '二星', '3': '三星', '4': '四星', '5': '五星', '6': '六星' };
    const matches = valueStr.match(/tier_([456])/gi) || [];
    return matches.map((t) => tierMap[t.slice(-1)]).join(',');
}
fnMap.set('parseRarity', parseRarity)

export async function parseProfession(valueStr: string): Promise<string> {
    let mappings: Record<string, any> | null = null;
    try {
        mappings = await loadPublicJSON("game_global/mappings.json");
        mappings = mappings.profession;
    } catch {
        mappings = null;
    }
    return valueStr.split(/[,|;]/g).map((p) => mappings?.[p.toUpperCase()] || p).join(',')
}
fnMap.set('parseProfession', parseProfession)

export async function parseToPercent(value: number): Promise<string> {
    return (value * 100).toFixed(2) + '%';
}
fnMap.set('parseToPercent', parseToPercent)

export async function parseBlackboardKey(valueStr: string): Promise<string> {
    switch (valueStr) {
        case "enemy_def_down":
            return "敌人防御力下降";
        case "enemy_def_up[down_when_take_dmg]":
            return "敌人防御力上升[受伤时下降]";
        default:
            return valueStr;
    }
}
fnMap.set('parseBlackboardKey', parseBlackboardKey)
