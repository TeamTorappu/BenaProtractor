import type { TreeOption } from "naive-ui";
import { loadPublicJSON } from "@/composables/usePublic";

/* ── 增强上下文：schema parse 函数可通过它递归构建子树 ── */

export interface ParseCtx {
    /** 是否展示全部 */
    showAll: boolean;
    /** 当前字段的 key 路径 */
    baseKey: string;
    /** 所属 action 对象 */
    action?: Record<string, unknown>;
    /** 顶层 buff 对象 */
    buff?: Record<string, unknown>;
    /** 递归构建带 $type 的 action 节点 */
    buildAction: (node: Record<string, unknown>, key: string, prefix?: string) => Promise<TreeOption>;
    /** 递归构建普通 object / array */
    buildNested: (value: unknown, key: string, label: string) => Promise<TreeOption>;
}

export const fnMap: Map<string, Function> = new Map();

/** 递归标记整棵子树为 display: false */
function markHidden(node: TreeOption): TreeOption {
    return {
        ...node,
        display: false,
        children: node.children?.map(markHidden),
    };
}

/* ── 标量解析函数（返回 string） ── */

export async function parseNumber($input: number, _$ctx: any): Promise<number> {
    return $input;
}
fnMap.set("parseNumber", parseNumber);

export async function parseBoolean($input: boolean, _$ctx: any): Promise<string> {
    return $input ? "是" : "否";
}
fnMap.set("parseBoolean", parseBoolean);

export async function parseTemplateKey($input: string, _$ctx: any): Promise<string> {
    return $input;
}
fnMap.set("parseTemplateKey", parseTemplateKey);

/* ── 节点解析函数（返回 TreeOption，供 schema+parse 使用） ── */

/** 单个 action 节点（带 $type 的 object） */
export async function parseActionNode($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    if ($input && typeof $input === "object" && "$type" in $input) return await $ctx.buildAction($input, $ctx.baseKey);
    return { key: $ctx.baseKey, label: "null", isLeaf: true };
}
fnMap.set("parseActionNode", parseActionNode);

/** action 节点数组（每项带 $type） */
export async function parseActionArray($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    if (!Array.isArray($input) || $input.length === 0) return { key: $ctx.baseKey, label: "[]", isLeaf: true };
    const children = await Promise.all(
        $input.map((item: any, i: number) => {
            const ck = `${$ctx.baseKey}/${i}`;
            if (item && typeof item === "object" && "$type" in item) return $ctx.buildAction(item, ck, `[${i}]`);
            return $ctx.buildNested(item, ck, `[${i}]`);
        }),
    );
    return { key: $ctx.baseKey, label: "", children };
}
fnMap.set("parseActionArray", parseActionArray);

/** 普通 object（无 $type） */
export async function parseObjectDefault($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    if (!$input || typeof $input !== "object") return { key: $ctx.baseKey, label: String($input), isLeaf: true };
    return await $ctx.buildNested($input, $ctx.baseKey, "");
}
fnMap.set("parseObjectDefault", parseObjectDefault);

/** 普通数组 */
export async function parseArrayDefault($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    if (!Array.isArray($input) || $input.length === 0) return { key: $ctx.baseKey, label: "[]", isLeaf: true };
    return await $ctx.buildNested($input, $ctx.baseKey, "");
}
fnMap.set("parseArrayDefault", parseArrayDefault);

export async function parsebuff($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    if (!$input || typeof $input !== "object") return parseObjectDefault($input, $ctx);

    let mappings: Record<string, any> | null = null;
    try {
        mappings = await loadPublicJSON("game_global/mappings.json");
    } catch {
        mappings = null;
    }

    const readDictionary = (cat: string, key: string) => {
        try {
            return mappings?.[cat]?.[key] ?? key;
        } catch {
            return key;
        }
    };

    const fmtPercent = (v: number, keepSign = true) => {
        if (typeof v !== "number" || isNaN(v)) return String(v);
        const pct = Math.round(v * 10000) / 100;
        const s = `${pct}%`;
        if (keepSign && v > 0) return "+" + s;
        return s;
    };

    const buff = $input as Record<string, any>;

    const buffKey = buff.buffKey ?? "";

    if (buff.loadFromDB) {
        return { key: $ctx.baseKey, label: `${buffKey}(读取自数据库)`, isLeaf: true };
    }

    const results: string[] = [];
    const blackboard: Record<string, any> = {};
    let has_resistable_flag = false;

    // template
    if (buff.templateKey && buff.templateKey !== "empty") results.push(`使用${buff.templateKey}模板`);

    // blackboard
    if (Array.isArray(buff.blackboard) && buff.blackboard.length > 0) {
        for (const bb of buff.blackboard) {
            const bb_key = bb.key;
            if (bb.value !== undefined && bb.value !== null) blackboard[bb_key] = bb.value;
            else if (bb.valueStr) blackboard[bb_key] = bb.valueStr;
        }
    }

    // attributes / features
    const attrs = buff.attributes ?? {};
    const features: string[] = [];

    const abnormalFlags = Array.isArray(attrs.abnormalFlags) ? attrs.abnormalFlags : [];
    for (const flag of abnormalFlags) {
        const name = readDictionary("abnormal", flag);
        features.push(name);
        if (["STUNNED", "COLD", "FROZEN"].includes(flag)) has_resistable_flag = true;
    }

    const abnormalImmunes = Array.isArray(attrs.abnormalImmunes) ? attrs.abnormalImmunes : [];
    for (const flag of abnormalImmunes) {
        const name = readDictionary("abnormal", flag);
        features.push(name + "免疫");
    }

    const abnormalAntis = Array.isArray(attrs.abnormalAntis) ? attrs.abnormalAntis : [];
    for (const flag of abnormalAntis) {
        const name = readDictionary("abnormal", flag);
        features.push(name + "反制");
    }

    const abnormalCombos = Array.isArray(attrs.abnormalCombos) ? attrs.abnormalCombos : [];
    for (const combo of abnormalCombos) {
        const name = readDictionary("abnormal", combo);
        features.push(name);
    }

    const abnormalComboImmunes = Array.isArray(attrs.abnormalComboImmunes) ? attrs.abnormalComboImmunes : [];
    for (const combo of abnormalComboImmunes) {
        const name = readDictionary("abnormal", combo);
        features.push(name + "免疫");
    }

    const attributeModifiers = Array.isArray(attrs.attributeModifiers) ? attrs.attributeModifiers : [];
    for (const modify of attributeModifiers) {
        const attr_name = readDictionary("attribute", modify.attributeType);
        const formula = modify.formulaItem;
        let value = modify.value;
        let value_str = String(value);

        if (modify.loadFromBlackboard || modify.fetchBaseValueFromSourceEntity) {
            if (modify.fetchBaseValueFromSourceEntity) value_str = "(来源同值)";
            else value_str = "X";

            if (formula === "ADDITION") value_str = "+" + value_str;
            else if (formula === "MULTIPLIER") value_str = "+" + value_str + "%";
            else if (formula === "FINAL_ADDITION") value_str = "+" + value_str + "(终加)";
            else if (formula === "FINAL_SCALER") value_str = "×" + value_str + "%(终乘)";
        } else {
            if (formula === "FINAL_SCALER") value_str = fmtPercent(value, false) + "(终乘)";
            else if (formula === "MULTIPLIER") value_str = fmtPercent(value, true);
            else if (formula === "ADDITION" || formula === "FINAL_ADDITION") {
                value_str = Number(value) < 0 ? String(value) : `+${value}`;
                if (formula === "FINAL_ADDITION") value_str += "(终加)";
            } else {
                value_str = String(value);
            }
        }

        features.push(attr_name + value_str);
    }

    if (features.length > 0) results.push("提供" + features.join(","));

    if (buff.isDurableBuff) results.push("不可清除");
    if (buff.isDamageMissable) results.push("受命中率影响");

    const stopby: string[] = [];
    if (buff.isSilenceable) stopby.push("沉默");
    if (buff.isStunnable) stopby.push("晕眩");
    if (buff.isFreezable) stopby.push("冻结");
    if (buff.isLevitatable) stopby.push("浮空");
    if (stopby.length > 0) results.push(stopby.join("/") + "期间失效");

    if (buff.statusResistable === "YES" || (buff.statusResistable === "AUTOMATIC" && has_resistable_flag)) results.push("可抵抗");

    if (buff.overrideKey && buff.overrideKey !== "empty") results.push(`处理覆盖时视为${buff.overrideKey}`);
    if (buff.overrideOnEventPriority) results.push(`事件优先级覆写为${buff.onEventPriority}`);

    if (buff.lifeTimeType === "INFINITY") results.push("永久");
    else if (buff.lifeTimeType === "LIMITED") {
        if (buff.durationKey && buff.durationKey !== "none") results.push(`持续(${buff.durationKey})秒`);
        else if (buff.lifeTime === 0 || buff.lifeTime === 0.0) results.push("持续一瞬间");
        else results.push(`持续${String(buff.lifeTime)}秒`);
    }

    // trigger config (简化实现)
    try {
        if (buff.triggerLifeType === "IMMEDIATELY") {
            if (buff.waitFirstTriggerInterval && Number(buff.firstTriggerInterval) >= 0) {
                const ticks = Math.ceil(Number(buff.firstTriggerInterval) * 30);
                results.push(`${ticks}帧后触发`);
            } else if (Number(buff.triggerInterval) >= 0) {
                const ticks = Math.ceil(Number(buff.triggerInterval) * 30);
                results.push(`${ticks}帧后触发`);
            }
        } else if (buff.triggerLifeType === "INFINITY") {
            if (buff.waitFirstTriggerInterval && Number(buff.firstTriggerInterval) >= 0) {
                const start_ticks = Number(buff.firstTriggerInterval);
                if (Number(buff.triggerInterval) >= 0) {
                    const ticks = Math.ceil(Number(buff.triggerInterval) * 30);
                    results.push(`${start_ticks}帧后及后续每${ticks}帧触发一次`);
                } else results.push(`${start_ticks}帧后触发`);
            } else if (Number(buff.triggerInterval) >= 0) {
                const ticks = Math.ceil(Number(buff.triggerInterval) * 30);
                results.push(`每${ticks}帧触发一次`);
            }
        } else if (buff.triggerLifeType === "LIMITED") {
            if (Number(buff.triggerCnt) > 1) {
                const trigget_cnt = Number(buff.triggerCnt);
                if (buff.waitFirstTriggerInterval && Number(buff.firstTriggerInterval) >= 0) {
                    const start_ticks = Number(buff.firstTriggerInterval);
                    if (Number(buff.triggerInterval) >= 0) {
                        const ticks = Math.ceil(Number(buff.triggerInterval) * 30);
                        results.push(`${start_ticks}帧后及后续每${ticks}帧触发一次，上限${trigget_cnt}次`);
                    } else results.push(`${start_ticks}帧后触发`);
                } else if (Number(buff.triggerInterval) >= 0) {
                    const ticks = Math.ceil(Number(buff.triggerInterval) * 30);
                    results.push(`${ticks}帧后触发`);
                }
            } else if (Number(buff.triggerCnt) === 1) {
                if (buff.waitFirstTriggerInterval && Number(buff.firstTriggerInterval) >= 0) {
                    const ticks = Math.ceil(Number(buff.firstTriggerInterval) * 30);
                    results.push(`${ticks}帧后触发`);
                } else if (Number(buff.triggerInterval) >= 0) {
                    const ticks = Math.ceil(Number(buff.triggerInterval) * 30);
                    results.push(`${ticks}帧后触发`);
                }
            }
        }
    } catch {
        // ignore
    }

    // overrideType
    if (buff.overrideType && buff.overrideType !== "DEFAULT") {
        if (buff.overrideType === "STACK") {
            const max_stack = buff.maxStackCnt;
            if (buff.refreshRemainingTimeWhenStackMax) {
                if (buff.clearAllStackCntWhenTimeUp) results.push(`可叠加${max_stack}，叠满后仅刷新时间，到时间时Buff直接结束`);
                else results.push(`可叠加${max_stack}，叠满后仅刷新时间，到时间降低一层并刷新时间`);
            } else {
                if (buff.clearAllStackCntWhenTimeUp) results.push(`可叠加${max_stack}，叠满后无法再施加，到时间时Buff直接结束`);
                else results.push(`可叠加${max_stack}，叠满后无法再施加，到时间降低一层并刷新时间`);
            }
        } else if (buff.overrideType === "EXTEND") {
            if (buff.takeSnapshotWhenExtend) results.push("重复施加时仅延长原有Buff并更新数据");
            else results.push("重复施加时仅延长原有Buff");
        } else {
            results.push(`叠加类型${buff.overrideType}`);
        }
    }

    if (Object.keys(blackboard).length > 0) results.push(JSON.stringify(blackboard));

    const description = results.join(";");

    /* 摘要节点（始终可见） */
    const descChild: TreeOption = { key: `${$ctx.baseKey}/desc`, label: description, isLeaf: true };

    const children: TreeOption[] = [descChild];
    if ($ctx.showAll) {
        const rawTree = await $ctx.buildNested($input, `${$ctx.baseKey}/raw`, "原始属性");
        children.push(...(rawTree.children ?? [rawTree]).map(markHidden));
    }

    return { key: $ctx.baseKey, label: buffKey || "buff", children };
}

fnMap.set("parsebuff", parsebuff);

export async function parsebuffArray($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    if (!Array.isArray($input) || $input.length === 0) return { key: $ctx.baseKey, label: "[]", isLeaf: true };
    const children = await Promise.all(
        $input.map((item: any, i: number) => {
            const ck = `${$ctx.baseKey}/${i}`;
            return parsebuff(item, { ...$ctx, baseKey: ck });
        }),
    );
    return { key: $ctx.baseKey, label: "", children };
}
fnMap.set("parsebuffArray", parsebuffArray);


let _mappingsCache: Record<string, any> | null = null;
async function getMappings(): Promise<Record<string, any>> {
    if (_mappingsCache) return _mappingsCache;
    try {
        _mappingsCache = await loadPublicJSON("game_global/mappings.json");
    } catch {
        _mappingsCache = {};
    }
    return _mappingsCache!;
}

function readDict(mappings: Record<string, any>, cat: string, key: string): string {
    return mappings?.[cat]?.[key] ?? key;
}

const toPercent = (v: number) => `${Math.floor(v * 100)}%`;

function analyzeDamage(node: Record<string, any>, mappings: Record<string, any>, prefix = "", suffix = ""): string {
    const features: string[] = [];
    const damageTypeName = readDict(mappings, "damage_type", node._damageType);
    const attackTypeName = readDict(mappings, "attack_type", node._attackType ?? "NONE");

    if (node._noSource) prefix += "无来源的";
    else if (node._onlyUseSourceOnCalculateDamage) features.push("仅在计算伤害时使用来源处理");

    if (node._ignoreForSp) features.push("不触发受击回复");
    if (node._forceUseProjectileCachedAtk) features.push("强制使用弹道的缓存攻击力");
    else if (node._getCachedAtkFromBlackboard && node._cachedAtkKey)
        features.push(`使用黑板中(${node._cachedAtkKey})作为缓存攻击力`);

    if (node._skipModifierEvent) features.push("类生命流失(无计算/事件)");
    if (node._isEnvDamage) features.push("环境伤害");
    if (node._isUndeadable) features.push("不会致命");
    if (node._instantKillLikeDamage) features.push("类斩杀伤害");
    if (node._isNotChangeableValue) features.push("无法被其他方式增/减/免伤");

    if (node._setSharedFlag && node._sharedFlagIndex) {
        const name = readDict(mappings, "sharedflag", node._sharedFlagIndex);
        if (!features.includes(name)) features.push(name);
    }
    if (node._ignoreMissFlag && node._ignoreMissFlag !== "NONE")
        features.push("无视" + readDict(mappings, "damage_type", node._ignoreMissFlag) + "闪避");
    if (node._multiplierByKey && node._multiplierKey)
        features.push("乘以黑板值" + node._multiplierKey);
    if (node._ignoreCancelReasonMask && node._ignoreCancelReasonMask !== "NONE")
        features.push("无视" + readDict(mappings, "cancel_reason", node._ignoreCancelReasonMask));

    if (features.length > 0) suffix += "（" + features.join(";") + "）";
    return prefix + damageTypeName + attackTypeName + "伤害" + suffix;
}


export async function parseNodeCreateBuff($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._buffOwner);
    const buffName = node._isDerivedBuff ? "本Buff的子Buff" : "Buff";
    const label = `为${target}创建一个${buffName}`;

    const children: TreeOption[] = [];
    if (node._buff) {
        const buffTree = await parsebuff(node._buff, { ...$ctx, baseKey: `${$ctx.baseKey}/_buff` });
        children.push(buffTree);
    }
    return { key: $ctx.baseKey, label, children: children.length ? children : undefined, isLeaf: !children.length };
}
fnMap.set("parseNodeCreateBuff", parseNodeCreateBuff);


export async function parseNodeCreateBuffUseHostAsSource($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    let target = readDict(mappings, "target", node._targetType);
    const source = readDict(mappings, "target", node._sourceType);
    const buffName = node._isDerivedBuff ? "本Buff的子Buff" : "Buff";
    if (node._createOnTargetHost) target += "(召唤物)的持有者";
    const label = `让${source}为${target}创建一个${buffName}`;

    const children: TreeOption[] = [];
    if (node._buffData) {
        const buffTree = await parsebuff(node._buffData, { ...$ctx, baseKey: `${$ctx.baseKey}/_buffData` });
        children.push(buffTree);
    }
    return { key: $ctx.baseKey, label, children: children.length ? children : undefined, isLeaf: !children.length };
}
fnMap.set("parseNodeCreateBuffUseHostAsSource", parseNodeCreateBuffUseHostAsSource);


export async function parseNodeAdvancedApplyDamage($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const source = readDict(mappings, "target", node._sourceType);
    const target = readDict(mappings, "target", node._targetType);
    const damageName = analyzeDamage(node, mappings);
    const atkScale = toPercent(node._defaultAtkScale ?? 1);
    const label = `让${source}对${target}造成${atkScale}${damageName}`;
    const desc = `会读取黑板中的${node._atkScaleVar}作为攻击力倍率使用`;

    return {
        key: $ctx.baseKey,
        label,
        children: [{ key: `${$ctx.baseKey}/desc`, label: desc, isLeaf: true }],
    };
}
fnMap.set("parseNodeAdvancedApplyDamage", parseNodeAdvancedApplyDamage);


export async function parseNodeNoSourceDamage($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const damageName = analyzeDamage(node, mappings, "无来源的");
    return { key: $ctx.baseKey, label: `对持有者造成X点${damageName}`, isLeaf: true };
}
fnMap.set("parseNodeNoSourceDamage", parseNodeNoSourceDamage);


export async function parseNodeFinishBuff($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const label = node._decCntIfStack
        ? "此Buff叠层减少一层；若减少至0层则此Buff结束"
        : "此Buff结束";
    return { key: $ctx.baseKey, label, isLeaf: true };
}
fnMap.set("parseNodeFinishBuff", parseNodeFinishBuff);


export async function parseNodeFinishDerivedBuff(_$input: any, $ctx: ParseCtx): Promise<TreeOption> {
    return { key: $ctx.baseKey, label: "结束此Buff的所有子Buff", isLeaf: true };
}
fnMap.set("parseNodeFinishDerivedBuff", parseNodeFinishDerivedBuff);


export async function parseNodeFinishDerivedBuffById($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const label = node._decCntIfStack
        ? `结束${node._buffKey}的所有无叠层的子Buff；可叠层的子Buff减少一层叠层，若减少至0层则其结束`
        : `结束${node._buffKey}的所有子Buff`;
    return { key: $ctx.baseKey, label, isLeaf: true };
}
fnMap.set("parseNodeFinishDerivedBuffById", parseNodeFinishDerivedBuffById);


export async function parseNodeFinishBuffsById($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._targetType);
    let buffName = node._loadFromBlackboard ? "特定Buff（取决于黑板）" : (node._buffKey ?? "Buff");

    if (node._checkBuffSource) {
        const source = readDict(mappings, "target", node._sourceType);
        buffName = node._alsoClearNullSource
            ? `来源于${source}或无来源的${buffName}`
            : `来源于${source}的${buffName}`;
    }

    let action = "结束";
    if (node._decCntIfStack) {
        action = node._decCntKey
            ? `减少黑板${node._decCntKey}值层叠层（变为0层时该Buff结束）`
            : `减少${node._decCnt ?? 1}层叠层（变为0层时该Buff结束）`;
    }

    return { key: $ctx.baseKey, label: `令${target}身上的${buffName}${action}`, isLeaf: true };
}
fnMap.set("parseNodeFinishBuffsById", parseNodeFinishBuffsById);



export async function parseNodeBlockDamage($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const features: string[] = [];
    let name = "处理概率格挡/计次护盾效果";

    if (node._useDynamicVar) {
        name = "处理屏障效果";
        if (node._allowNegativeDynamicVar) features.push("允许负屏障值");
        if (node._showShieldUI) features.push("在血条上显示屏障值");
    } else if (node._useFixedValue) {
        name = "处理阈值格挡效果";
    }

    if (node._showDamageNumber) features.push("即使成功格挡也显示伤害数值");
    if (node._specifyBlockEffect) features.push("使用格挡特效" + node._specifyBlockEffect);

    if (node._filterApplyWay) {
        const f = node._applyWayFilter;
        if (f === "NONE") features.push("仅格挡施加方式为\u201c无\u201d的伤害");
        else if (f === "MELEE") features.push("仅格挡施加方式为\u201c近战\u201d或\u201c无\u201d的伤害");
        else if (f === "RANGED") features.push("仅格挡施加方式为\u201c远程\u201d或\u201c无\u201d的伤害");
    }

    const label = features.length > 0 ? `${name}（${features.join(",")})` : name;
    return { key: $ctx.baseKey, label, isLeaf: true };
}
fnMap.set("parseNodeBlockDamage", parseNodeBlockDamage);


export async function parseNodeDamageScale($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();

    let scale = node._isOneMinus ? "(1-X)" : "(1+X)";
    const action = node._isOneMinus ? "降低" : "提升";
    if (node._isStackable) scale = `(${scale}×Buff层数)`;

    let text = `令本次伤害${action}至${scale}倍`;
    const conditions: string[] = [];

    if (node._filterDamageType)
        conditions.push("伤害类型为" + readDict(mappings, "damage_type", node._damageMask));
    if (node._filterApplyWay) {
        const f = node._applyWayFilter;
        if (f === "NONE") conditions.push("施加方式为无类型施加");
        else if (f === "MELEE") conditions.push("施加方式为近战");
        else if (f === "RANGED") conditions.push("施加方式为远程");
    }
    if (conditions.length > 0) text = `若${conditions.join("且")}，${text}`;
    if (node._cachedDeltaValueToBBKey) text += "，并将减少/增加的部分记在黑板上";

    return { key: $ctx.baseKey, label: text, isLeaf: true };
}
fnMap.set("parseNodeDamageScale", parseNodeDamageScale);


export async function parseNodeAtkScaleUp($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    let label = `攻击力倍率乘以${node._defaultValue ?? "X"}倍`;
    const desc = `会读取黑板中的${node._atkScaleKey}作为乘数`;
    const conditions: string[] = [];

    if (node._filterApplyWay) {
        const f = node._applyWay;
        if (f === "NONE" && node._filterNoneApplyWay) conditions.push("目标攻击方式为\"不攻击\"或未标注攻击方式");
        else if (f === "NONE") conditions.push("目标攻击方式为\"不攻击\"");
        else if (f === "MELEE") conditions.push("目标攻击方式为\"近战\"");
        else if (f === "RANGED") conditions.push("目标攻击方式为\"远程\"");
    }
    if (node._filterProjectileKey) conditions.push(`伤害来自${node._filterProjectileKey}弹道`);
    if (conditions.length > 0) label = `若${conditions.join("且")}，${label}`;

    let descText = desc;
    if (node._cancelIfAtkScaleZero)
        descText += "；若乘算后本次伤害的攻击力倍率为0，则取消此次伤害";

    return {
        key: $ctx.baseKey,
        label,
        children: [{ key: `${$ctx.baseKey}/desc`, label: descText, isLeaf: true }],
    };
}
fnMap.set("parseNodeAtkScaleUp", parseNodeAtkScaleUp);


export async function parseNodeTriggerAbility($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._targetType);
    const ability = node._abilityName ?? "";

    if (node._ownerType === node._targetType)
        return { key: $ctx.baseKey, label: `让${target}触发${ability}能力`, isLeaf: true };

    const owner = readDict(mappings, "target", node._ownerType);
    return { key: $ctx.baseKey, label: `让${owner}向${target}触发${ability}能力`, isLeaf: true };
}
fnMap.set("parseNodeTriggerAbility", parseNodeTriggerAbility);


export async function parseNodeCalcBBValue($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    let placeName = "";
    const inputKey = node._inputKey ?? "";
    const outputKey = node._outputKey ?? "";
    let formula = inputKey;

    if (node._useAbilityBlackboard && node._abilityName)
        placeName = `在能力${node._abilityName}的黑板中，`;

    if (node._multiplyParamKey) formula += ` × ${node._multiplyParamKey}`;
    if (node._dividedParamKey) {
        formula += node._useRemainder ? ` rem ${node._dividedParamKey}` : ` ÷ ${node._dividedParamKey}`;
    }
    if (node._addParamKey) formula += ` + ${node._addParamKey}`;
    if (node._minusParamKey) formula += ` - ${node._minusParamKey}`;

    if (node._minValueKey) {
        formula = node._maxValueKey
            ? `clamp(${formula},${node._minValueKey},${node._maxValueKey})`
            : `max(${formula},${node._minValueKey})`;
    } else if (node._maxValueKey) {
        formula = `min(${formula},${node._maxValueKey})`;
    }

    if (node._finalAbs) formula = `| ${formula} |`;
    if (node._finalCeil) formula += "（向上取整）";
    else if (node._finalFloor) formula += "（向下取整）";
    else if (node._finalRound) formula += "（四舍六入）";

    return { key: $ctx.baseKey, label: `${placeName}计算黑板值。将 ${outputKey} 设置为 ${formula}`, isLeaf: true };
}
fnMap.set("parseNodeCalcBBValue", parseNodeCalcBBValue);


export async function parseNodeSwitchMode($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._targetType);

    let action = "";
    if (node._restoreDefault) action = "切换回默认模式";
    else if (node._loadModeFromBlackboard) action = "切换至第X号模式";
    else action = `切换至第${node._modeIndex}号模式`;

    return { key: $ctx.baseKey, label: `令${target}${action}`, isLeaf: true };
}
fnMap.set("parseNodeSwitchMode", parseNodeSwitchMode);


export async function parseNodeRechargeToken($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const label = node._refreshRemainingCnt
        ? "将Buff持有者的召唤物数量恢复至默认值"
        : `根据黑板上 ${node._cntKey} 的数值，为Buff持有者补充召唤物（不会超过上限）`;
    return { key: $ctx.baseKey, label, isLeaf: true };
}
fnMap.set("parseNodeRechargeToken", parseNodeRechargeToken);


export async function parseNodeAssignTokenCardCntToBB($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._targetType);
    const label = node._assignMaxCount
        ? `在黑板上将${target}的召唤物最大持有数记录为 ${node._countKey}`
        : `在黑板上将${target}的召唤物当前持有数记录为 ${node._countKey}`;
    return { key: $ctx.baseKey, label, isLeaf: true };
}
fnMap.set("parseNodeAssignTokenCardCntToBB", parseNodeAssignTokenCardCntToBB);


export async function parseNodeInterruptTokenSkill($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const host = readDict(mappings, "target", node._hostType);
    return { key: $ctx.baseKey, label: `由${host}终止Buff持有者的技能（通常来说，持有者应该是${host}的召唤物）`, isLeaf: true };
}
fnMap.set("parseNodeInterruptTokenSkill", parseNodeInterruptTokenSkill);


export async function parseNodeDamageSplit($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._targetType);
    const attackType = readDict(mappings, "attack_type", node._attackType);
    return { key: $ctx.baseKey, label: `将本次伤害的X%以同类型${attackType}伤害的形式传递给${target}（原伤害不会变化）`, isLeaf: true };
}
fnMap.set("parseNodeDamageSplit", parseNodeDamageSplit);


export async function parseNodePlayAudio($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._target);
    return { key: $ctx.baseKey, label: `让${target}播放音效 ${node._audioSignal}`, isLeaf: true };
}
fnMap.set("parseNodePlayAudio", parseNodePlayAudio);



export async function parseNodeCheckCharacterGroupTag($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._targetType);
    return { key: $ctx.baseKey, label: `检查${target}阵营标签：${node._groupTag}`, isLeaf: true };
}
fnMap.set("parseNodeCheckCharacterGroupTag", parseNodeCheckCharacterGroupTag);


export async function parseNodeFilterByTargetMassLevel($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._target);
    const compare = readDict(mappings, "compare", node._condType);
    return { key: $ctx.baseKey, label: `检查${target}的重量是否${compare}X`, isLeaf: true };
}
fnMap.set("parseNodeFilterByTargetMassLevel", parseNodeFilterByTargetMassLevel);


export async function parseNodeCheckContainsBuff($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const node = $input as Record<string, any>;
    const mappings = await getMappings();
    const target = readDict(mappings, "target", node._targetType);
    const keys = Array.isArray(node._buffKeys) ? node._buffKeys : [];
    const isAnd = node.isAND;

    let condition = `检查${target}是否`;
    if (keys.length > 1) {
        let keyStr = keys.join("、");
        if (node._checkBuffSource) {
            const source = readDict(mappings, "target", node._buffSourceType);
            keyStr = `来自${source}的 ${keyStr}`;
        }
        condition += isAnd ? `同时持有 ${keyStr}` : `持有 ${keyStr} 中的任意一个`;
    } else if (keys.length === 1) {
        let keyStr = keys[0];
        if (node._checkBuffSource) {
            const source = readDict(mappings, "target", node._buffSourceType);
            keyStr = `来自${source}的 ${keyStr}`;
        }
        condition += `持有 ${keyStr}`;
    }

    return { key: $ctx.baseKey, label: condition, isLeaf: true };
}
fnMap.set("parseNodeCheckContainsBuff", parseNodeCheckContainsBuff);


export async function parseTargetOptions($input: any, $ctx: ParseCtx): Promise<TreeOption> {
    const opt = $input as Record<string, any>;
    const mappings = await getMappings();

    const sideMap: Record<string, string> = { ENEMY: "敌方", ALLY: "我方", ALL: "全部" };
    const motionMap: Record<string, string> = { ALL: "全部", WALK_ONLY: "移动中" };

    const side = sideMap[opt.targetSide] ?? opt.targetSide;
    const motion = motionMap[opt.targetMotion] ?? opt.targetMotion;
    const label = `目标：${side}`;

    const children: TreeOption[] = [];
    const ck = (k: string) => `${$ctx.baseKey}/${k}`;

    children.push({ key: ck("targetSide"), label: `目标阵营: ${side}`, isLeaf: true });
    children.push({ key: ck("targetMotion"), label: `运动状态: ${motion}`, isLeaf: true });

    if (opt.targetCategory && opt.targetCategory !== "DEFAULT")
        children.push({ key: ck("targetCategory"), label: `目标类别: ${opt.targetCategory}`, isLeaf: true });

    if (opt.professionMask && opt.professionMask !== "NONE") {
        const profs = opt.professionMask.split(/[,|;]/g).map((p: string) => mappings?.[p.toUpperCase()] || p).join(',');
        children.push({ key: ck("professionMask"), label: `职业筛选: ${profs}`, isLeaf: true });
    }

    if (opt.checkUnitType && opt.unitTypeMask && opt.unitTypeMask !== "NONE")
        children.push({ key: ck("unitTypeMask"), label: `单位类型: ${opt.unitTypeMask}`, isLeaf: true });

    if (opt.purposeMask && opt.purposeMask !== "NONE")
        children.push({ key: ck("purposeMask"), label: `用途: ${opt.purposeMask}`, isLeaf: true });

    if (opt.ignoreTargetFree) children.push({ key: ck("ignoreTargetFree"), label: "无视不可选中", isLeaf: true });
    if (opt.ignoreAllyTargetFree) children.push({ key: ck("ignoreAllyTargetFree"), label: "无视友方不可选中", isLeaf: true });
    if (opt.ignoreHealFree) children.push({ key: ck("ignoreHealFree"), label: "无视禁疗", isLeaf: true });
    if (opt.ignoreTargetSide) children.push({ key: ck("ignoreTargetSide"), label: "无视阵营", isLeaf: true });

    if (opt.excludeSomeAbnormalFlags) {
        const excl = readDict(mappings, "abnormal", opt.excludeAbnormalFlag);
        children.push({ key: ck("excludeAbnormalFlag"), label: `排除${excl}单位`, isLeaf: true });
    }
    if (opt.onlyIgnoreSomeOfTargetFreeCase) {
        const abFlag = readDict(mappings, "abnormal", opt.abnormalFlag);
        children.push({ key: ck("abnormalFlag"), label: `仅忽略${abFlag}导致的不可选中`, isLeaf: true });
    }

    if (opt.abnormalCombo && opt.abnormalCombo !== "NONE") {
        const combo = readDict(mappings, "abnormal", opt.abnormalCombo);
        children.push({ key: ck("abnormalCombo"), label: `异常连锁: ${combo}`, isLeaf: true });
    }

    return { key: $ctx.baseKey, label, children };
}
fnMap.set("parseTargetOptions", parseTargetOptions);
