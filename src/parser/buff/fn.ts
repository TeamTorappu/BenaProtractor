import type { TreeOption } from 'naive-ui'
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

export async function parseTemplateKey($input: string, _$ctx: any): Promise<string> {
	return $input
}
fnMap.set('parseTemplateKey', parseTemplateKey)

/* ── 节点解析函数（返回 TreeOption，供 schema+parse 使用） ── */

/** 单个 action 节点（带 $type 的 object） */
export async function parseActionNode($input: any, $ctx: ParseCtx): Promise<TreeOption> {
	if ($input && typeof $input === 'object' && '$type' in $input)
		return await $ctx.buildAction($input, $ctx.baseKey)
	return { key: $ctx.baseKey, label: 'null', isLeaf: true }
}
fnMap.set('parseActionNode', parseActionNode)

/** action 节点数组（每项带 $type） */
export async function parseActionArray($input: any, $ctx: ParseCtx): Promise<TreeOption> {
	if (!Array.isArray($input) || $input.length === 0)
		return { key: $ctx.baseKey, label: '[]', isLeaf: true }
	const children = await Promise.all(
		$input.map((item: any, i: number) => {
			const ck = `${$ctx.baseKey}/${i}`
			if (item && typeof item === 'object' && '$type' in item)
				return $ctx.buildAction(item, ck, `[${i}]`)
			return $ctx.buildNested(item, ck, `[${i}]`)
		}),
	)
	return { key: $ctx.baseKey, label: '', children }
}
fnMap.set('parseActionArray', parseActionArray)

/** 普通 object（无 $type） */
export async function parseObjectDefault($input: any, $ctx: ParseCtx): Promise<TreeOption> {
	if (!$input || typeof $input !== 'object')
		return { key: $ctx.baseKey, label: String($input), isLeaf: true }
	return await $ctx.buildNested($input, $ctx.baseKey, '')
}
fnMap.set('parseObjectDefault', parseObjectDefault)

/** 普通数组 */
export async function parseArrayDefault($input: any, $ctx: ParseCtx): Promise<TreeOption> {
	if (!Array.isArray($input) || $input.length === 0)
		return { key: $ctx.baseKey, label: '[]', isLeaf: true }
	return await $ctx.buildNested($input, $ctx.baseKey, '')
}
fnMap.set('parseArrayDefault', parseArrayDefault)

export async function parsebuff($input: any, $ctx: ParseCtx): Promise<TreeOption> {
	if (!$input || typeof $input !== 'object')
		return parseObjectDefault($input, $ctx)

	let mappings: Record<string, any> | null = null
	try {
		mappings = await loadPublicJSON('game_global/mappings.json')
	} catch {
		mappings = null
	}

	const readDictionary = (cat: string, key: string) => {
		try {
			return mappings?.[cat]?.[key] ?? key
		} catch {
			return key
		}
	}

	const fmtPercent = (v: number, keepSign = true) => {
		if (typeof v !== 'number' || isNaN(v)) return String(v)
		const pct = Math.round(v * 10000) / 100
		const s = `${pct}%`
		if (keepSign && v > 0) return '+' + s
		return s
	}

	const buff = $input as Record<string, any>

	const buffKey = buff.buffKey ?? ''

	if (buff.loadFromDB) {
		return { key: $ctx.baseKey, label: `${buffKey}(读取自数据库)`, isLeaf: true }
	}

	const results: string[] = []
	const blackboard: Record<string, any> = {}
	let has_resistable_flag = false

	// template
	if (buff.templateKey && buff.templateKey !== 'empty')
		results.push(`使用${buff.templateKey}模板`)

	// blackboard
	if (Array.isArray(buff.blackboard) && buff.blackboard.length > 0) {
		for (const bb of buff.blackboard) {
			const bb_key = bb.key
			if (bb.value !== undefined && bb.value !== null) blackboard[bb_key] = bb.value
			else if (bb.valueStr) blackboard[bb_key] = bb.valueStr
		}
	}

	// attributes / features
	const attrs = buff.attributes ?? {}
	const features: string[] = []

	const abnormalFlags = Array.isArray(attrs.abnormalFlags) ? attrs.abnormalFlags : []
	for (const flag of abnormalFlags) {
		const name = readDictionary('abnormal', flag)
		features.push(name)
		if (['STUNNED', 'COLD', 'FROZEN'].includes(flag)) has_resistable_flag = true
	}

	const abnormalImmunes = Array.isArray(attrs.abnormalImmunes) ? attrs.abnormalImmunes : []
	for (const flag of abnormalImmunes) {
		const name = readDictionary('abnormal', flag)
		features.push(name + '免疫')
	}

	const abnormalAntis = Array.isArray(attrs.abnormalAntis) ? attrs.abnormalAntis : []
	for (const flag of abnormalAntis) {
		const name = readDictionary('abnormal', flag)
		features.push(name + '反制')
	}

	const abnormalCombos = Array.isArray(attrs.abnormalCombos) ? attrs.abnormalCombos : []
	for (const combo of abnormalCombos) {
		const name = readDictionary('abnormal', combo)
		features.push(name)
	}

	const abnormalComboImmunes = Array.isArray(attrs.abnormalComboImmunes) ? attrs.abnormalComboImmunes : []
	for (const combo of abnormalComboImmunes) {
		const name = readDictionary('abnormal', combo)
		features.push(name + '免疫')
	}

	const attributeModifiers = Array.isArray(attrs.attributeModifiers) ? attrs.attributeModifiers : []
	for (const modify of attributeModifiers) {
		const attr_name = readDictionary('attribute', modify.attributeType)
		const formula = modify.formulaItem
		let value = modify.value
		let value_str = String(value)

		if (modify.loadFromBlackboard || modify.fetchBaseValueFromSourceEntity) {
			if (modify.fetchBaseValueFromSourceEntity) value_str = '(来源同值)'
			else value_str = 'X'

			if (formula === 'ADDITION') value_str = '+' + value_str
			else if (formula === 'MULTIPLIER') value_str = '+' + value_str + '%'
			else if (formula === 'FINAL_ADDITION') value_str = '+' + value_str + '(终加)'
			else if (formula === 'FINAL_SCALER') value_str = '×' + value_str + '%(终乘)'
		} else {
			if (formula === 'FINAL_SCALER') value_str = fmtPercent(value, false) + '(终乘)'
			else if (formula === 'MULTIPLIER') value_str = fmtPercent(value, true)
			else if (formula === 'ADDITION' || formula === 'FINAL_ADDITION') {
				value_str = (Number(value) < 0 ? String(value) : `+${value}`)
				if (formula === 'FINAL_ADDITION') value_str += '(终加)'
			} else {
				value_str = String(value)
			}
		}

		features.push(attr_name + value_str)
	}

	if (features.length > 0) results.push('提供' + features.join(','))

	if (buff.isDurableBuff) results.push('不可清除')
	if (buff.isDamageMissable) results.push('受命中率影响')

	const stopby: string[] = []
	if (buff.isSilenceable) stopby.push('沉默')
	if (buff.isStunnable) stopby.push('晕眩')
	if (buff.isFreezable) stopby.push('冻结')
	if (buff.isLevitatable) stopby.push('浮空')
	if (stopby.length > 0) results.push(stopby.join('/') + '期间失效')

	if (buff.statusResistable === 'YES' || (buff.statusResistable === 'AUTOMATIC' && has_resistable_flag))
		results.push('可抵抗')

	if (buff.overrideKey && buff.overrideKey !== 'empty') results.push(`处理覆盖时视为${buff.overrideKey}`)
	if (buff.overrideOnEventPriority) results.push(`事件优先级覆写为${buff.onEventPriority}`)

	if (buff.lifeTimeType === 'INFINITY') results.push('永久')
	else if (buff.lifeTimeType === 'LIMITED') {
		if (buff.durationKey && buff.durationKey !== 'none') results.push(`持续(${buff.durationKey})秒`)
		else if (buff.lifeTime === 0 || buff.lifeTime === 0.0) results.push('持续一瞬间')
		else results.push(`持续${String(buff.lifeTime)}秒`)
	}

	// trigger config (简化实现)
	try {
		if (buff.triggerLifeType === 'IMMEDIATELY') {
			if (buff.waitFirstTriggerInterval && Number(buff.firstTriggerInterval) >= 0) {
				const ticks = Math.ceil(Number(buff.firstTriggerInterval) * 30)
				results.push(`${ticks}帧后触发`)
			} else if (Number(buff.triggerInterval) >= 0) {
				const ticks = Math.ceil(Number(buff.triggerInterval) * 30)
				results.push(`${ticks}帧后触发`)
			}
		} else if (buff.triggerLifeType === 'INFINITY') {
			if (buff.waitFirstTriggerInterval && Number(buff.firstTriggerInterval) >= 0) {
				const start_ticks = Number(buff.firstTriggerInterval)
				if (Number(buff.triggerInterval) >= 0) {
					const ticks = Math.ceil(Number(buff.triggerInterval) * 30)
					results.push(`${start_ticks}帧后及后续每${ticks}帧触发一次`)
				} else results.push(`${start_ticks}帧后触发`)
			} else if (Number(buff.triggerInterval) >= 0) {
				const ticks = Math.ceil(Number(buff.triggerInterval) * 30)
				results.push(`每${ticks}帧触发一次`)
			}
		} else if (buff.triggerLifeType === 'LIMITED') {
			if (Number(buff.triggerCnt) > 1) {
				const trigget_cnt = Number(buff.triggerCnt)
				if (buff.waitFirstTriggerInterval && Number(buff.firstTriggerInterval) >= 0) {
					const start_ticks = Number(buff.firstTriggerInterval)
					if (Number(buff.triggerInterval) >= 0) {
						const ticks = Math.ceil(Number(buff.triggerInterval) * 30)
						results.push(`${start_ticks}帧后及后续每${ticks}帧触发一次，上限${trigget_cnt}次`)
					} else results.push(`${start_ticks}帧后触发`)
				} else if (Number(buff.triggerInterval) >= 0) {
					const ticks = Math.ceil(Number(buff.triggerInterval) * 30)
					results.push(`${ticks}帧后触发`)
				}
			} else if (Number(buff.triggerCnt) === 1) {
				if (buff.waitFirstTriggerInterval && Number(buff.firstTriggerInterval) >= 0) {
					const ticks = Math.ceil(Number(buff.firstTriggerInterval) * 30)
					results.push(`${ticks}帧后触发`)
				} else if (Number(buff.triggerInterval) >= 0) {
					const ticks = Math.ceil(Number(buff.triggerInterval) * 30)
					results.push(`${ticks}帧后触发`)
				}
			}
		}
	} catch {
		// ignore
	}

	// overrideType
	if (buff.overrideType && buff.overrideType !== 'DEFAULT') {
		if (buff.overrideType === 'STACK') {
			const max_stack = buff.maxStackCnt
			if (buff.refreshRemainingTimeWhenStackMax) {
				if (buff.clearAllStackCntWhenTimeUp) results.push(`可叠加${max_stack}，叠满后仅刷新时间，到时间时Buff直接结束`)
				else results.push(`可叠加${max_stack}，叠满后仅刷新时间，到时间降低一层并刷新时间`)
			} else {
				if (buff.clearAllStackCntWhenTimeUp) results.push(`可叠加${max_stack}，叠满后无法再施加，到时间时Buff直接结束`)
				else results.push(`可叠加${max_stack}，叠满后无法再施加，到时间降低一层并刷新时间`)
			}
		} else if (buff.overrideType === 'EXTEND') {
			if (buff.takeSnapshotWhenExtend) results.push('重复施加时仅延长原有Buff并更新数据')
			else results.push('重复施加时仅延长原有Buff')
		} else {
			results.push(`叠加类型${buff.overrideType}`)
		}
	}

	if (Object.keys(blackboard).length > 0) results.push(JSON.stringify(blackboard))

	const description = results.join(';')

	/* 摘要节点（始终可见） */
	const descChild: TreeOption = { key: `${$ctx.baseKey}/desc`, label: description, isLeaf: true }

	/* 递归展开原始属性，全部标记为 display: false */
	const rawTree = await $ctx.buildNested($input, `${$ctx.baseKey}/raw`, '原始属性')
	const rawChildren = (rawTree.children ?? [rawTree]).map(markHidden)

	return { key: $ctx.baseKey, label: buffKey || 'buff', children: [descChild, ...rawChildren] }
}

fnMap.set('parsebuff', parsebuff)

export async function parsebuffArray($input: any, $ctx: ParseCtx): Promise<TreeOption> {
	if (!Array.isArray($input) || $input.length === 0)
		return { key: $ctx.baseKey, label: '[]', isLeaf: true }
	const children = await Promise.all(
		$input.map((item: any, i: number) => {
			const ck = `${$ctx.baseKey}/${i}`
			return parsebuff(item, { ...$ctx, baseKey: ck })
		}),
	)
	return { key: $ctx.baseKey, label: '', children }
}
fnMap.set('parsebuffArray', parsebuffArray)