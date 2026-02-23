import type { TreeOption } from 'naive-ui'
import {
	loadIndex,
	loadEventList,
	loadActionNodes,
	loadActionKeysTemplate,
	loadActionKeys,
	loadActionDef,
} from './loader'
import { fnMap, type ParseCtx } from './fn'

/* ────────────────── helpers ────────────────── */

/** "Torappu.Battle.Action.Nodes+CreateBuff, Assembly-CSharp" → "CreateBuff" */
function extractNodeType(raw: string): string {
	const m = raw.match(/\+(\w+),/)
	return m ? m[1] : raw
}

/** camelCase → 空格分词：_targetType → target Type */
function humanize(key: string): string {
	return key
		.replace(/^_/, '')
		.replace(/([a-z])([A-Z])/g, '$1 $2')
}

/** 标量 → 友好文本 */
function fmt(v: unknown): string {
	if (v === null || v === undefined) return 'null'
	if (typeof v === 'boolean') return v ? '是' : '否'
	if (Array.isArray(v) && v.length === 0) return '[]'
	return String(v)
}

/** 判断是否为 action 节点（带 $type） */
function isActionNode(v: unknown): v is Record<string, unknown> {
	return !!v && typeof v === 'object' && '$type' in (v as any)
}

/* ────────────────── parse config 执行 ────────────────── */

/** 判断 parse 配置是否为脚本自动生成的默认值 */
function isGenerated(parse: any): boolean {
	return parse?.generated === true
}

/**
 * 根据优先级规则选择 parse 配置（fn > schema）。
 *
 * 手动配置始终优先于自动生成的配置，无论来源层级：
 *   手动 def > 手动 keys > 手动 tpl > generated def > generated keys > generated tpl
 */
function resolveParse(defParse: any, keysParse: any, tplParse: any): any {
	if (defParse && !isGenerated(defParse)) return defParse
	if (keysParse && !isGenerated(keysParse)) return keysParse
	if (tplParse && !isGenerated(tplParse)) return tplParse
	return defParse ?? keysParse ?? tplParse
}

/** 对 values 匹配条目应用同样的优先级逻辑 */
function resolveMatch(
	defMatch: ReturnType<typeof matchInValues>,
	keysMatch: ReturnType<typeof matchInValues>,
): ReturnType<typeof matchInValues> {
	if (defMatch && keysMatch
		&& isGenerated(defMatch.parse) && !isGenerated(keysMatch.parse))
		return keysMatch
	return defMatch ?? keysMatch
}

async function applyParse(
	value: unknown,
	parse: { type: string; return?: unknown; name?: string; args?: string[] },
	ctx: unknown,
): Promise<string> {
	if (parse.type === 'literal')
		return fmt(parse.return ?? value)

	if (parse.type === 'template' && parse.return) {
		const template = String(parse.return)
		const args = (parse.args ?? []).map((a: any) => {
			if (a === '$input') return String(value)
			if (a === '$ctx') return String(ctx)
			return String(a)
		})
		return template.replace(/\{(\d+)\}/g, (_, idx) => args[Number(idx)] ?? '')
	}

	if (parse.type === 'fn' && parse.name) {
		const fn = fnMap.get(parse.name)
		if (fn) {
			const args = (parse.args ?? []).map(a =>
				a === '$input' ? value : a === '$ctx' ? ctx : a,
			)
			return String(await fn(...args))
		}
	}
	return fmt(value)
}

/**
 * 尝试用 fn parse 处理一个字段。
 * 返回 TreeOption 或 null（调用方应走 fallback）。
 */
async function tryFnParse(
	key: string,
	value: unknown,
	desc: string,
	parse: any,
	showAll: boolean,
	action?: Record<string, unknown>,
): Promise<TreeOption | null> {
	if (!parse || parse.type !== 'fn' || !parse.name)
		return null
	if (value === null || typeof value !== 'object')
		return null

	const fn = fnMap.get(parse.name)
	if (!fn) return null

	const pctx: ParseCtx = {
		showAll,
		baseKey: key,
		action,
		buildAction: (a, k, p) => buildAction(a, k, showAll, p),
		buildNested: (v, k, l) => buildNested(v, k, l, showAll),
	}
	const node = await fn(value, pctx) as TreeOption
	return {
		key,
		label: node.label ? `${desc}: ${node.label}` : desc,
		children: node.children,
		isLeaf: node.isLeaf ?? !node.children,
	}
}

/* ────────────────── value 匹配 ────────────────── */

function matchInValues(
	values: any[] | undefined,
	value: unknown,
): { display: boolean; parse: any } | null {
	if (!values) return null
	const needle = typeof value === 'object'
		? JSON.stringify(value)
		: String(value)
	for (const entry of values) {
		const hay = typeof entry.value === 'object'
			? JSON.stringify(entry.value)
			: String(entry.value)
		if (hay === needle) return entry
	}
	return null
}

/* ────────────────── 树节点构造 ────────────────── */

/** 叶节点，display 标记决定是否在精简模式显示 */
function leaf(key: string, label: string, display = true): TreeOption {
	return { key, label, isLeaf: true, display }
}

/** 递归展开普通 object / array（不含 $type 的嵌套数据） */
async function buildNested(
	value: unknown,
	baseKey: string,
	label: string,
	showAll: boolean,
): Promise<TreeOption> {
	const children: TreeOption[] = []

	if (Array.isArray(value)) {
		if (value.length === 0)
			return leaf(baseKey, `${label}: []`)

		for (let i = 0; i < value.length; i++) {
			const item = value[i]
			const ck = `${baseKey}/${i}`
			if (isActionNode(item))
				children.push(await buildAction(item, ck, showAll, `[${i}]`))
			else if (item && typeof item === 'object')
				children.push(await buildNested(item, ck, `[${i}]`, showAll))
			else
				children.push(leaf(ck, `[${i}]: ${fmt(item)}`))
		}
	} else if (value && typeof value === 'object') {
		/* 子节点同样遵循主 parser 的引用规则（fn > schema） */
		const [keys, tpl] = await Promise.all([
			loadActionKeys(),
			loadActionKeysTemplate(),
		])

		for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
			const ck = `${baseKey}/${k}`
			const fKeys = keys?.[k]
			const fTpl = tpl?.[k]
			const d = fKeys?.description ?? fTpl?.description ?? humanize(k)

			const parse = resolveParse(undefined, fKeys?.parse, fTpl?.parse)
			const fnNode = await tryFnParse(ck, v, d, parse, showAll)
			if (fnNode) {
				children.push(fnNode)
				continue
			}

			if (isActionNode(v))
				children.push(await buildAction(v, ck, showAll, d))
			else if (v && typeof v === 'object')
				children.push(await buildNested(v, ck, d, showAll))
			else
				children.push(leaf(ck, `${d}: ${fmt(v)}`))
		}
	}

	return children.length
		? { key: baseKey, label, children }
		: leaf(baseKey, label)
}

/** 构建 action 节点（带 $type 的对象） */
async function buildAction(
	action: Record<string, unknown>,
	baseKey: string,
	showAll: boolean,
	prefix?: string,
): Promise<TreeOption> {
	/* null / 非法值 → dummy 占位节点 */
	if (!action || typeof action !== 'object' || !('$type' in action)) {
		const dummyLabel = prefix ? `${prefix} (空节点)` : '(空节点)'
		return leaf(baseKey, dummyLabel, true)
	}

	const nodeType = extractNodeType(action.$type as string)
	const nodes = await loadActionNodes()
	const desc = nodes?.[nodeType]?.description ?? humanize(nodeType)
	const label = prefix ? `${prefix} ${desc}` : desc

	/* 一次加载当前 action 需要的所有 schema 文件 */
	const [def, keys, tpl] = await Promise.all([
		loadActionDef(nodeType),
		loadActionKeys(),
		loadActionKeysTemplate(),
	])

	const children: TreeOption[] = []

	for (const [key, value] of Object.entries(action)) {
		if (key === '$type') continue
		const ck = `${baseKey}/${key}`

		const fDef = def?.fields?.[key]
		const fKeys = keys?.[key]
		const fTpl = tpl?.[key]
		const fdesc = fDef?.description ?? fKeys?.description ?? fTpl?.description ?? humanize(key)

		/* ─ fn > schema：优先使用声明式节点函数 ─ */
		const schemaParse = resolveParse(fDef?.parse, fKeys?.parse, fTpl?.parse)
		const fnNode = await tryFnParse(ck, value, fdesc, schemaParse, showAll, action)
		if (fnNode) {
			children.push(fnNode)
			continue
		}

		/* ─ 复杂嵌套（fallback） ─ */
		if (isActionNode(value)) {
			children.push(await buildAction(value, ck, showAll, fdesc))
			continue
		}
		if (Array.isArray(value) && value.length > 0 && value.some(v => isActionNode(v))) {
			const items = await Promise.all(
				value.map((item, i) => {
					const ik = `${ck}/${i}`
					return buildAction(item as Record<string, unknown>, ik, showAll, `[${i}]`)
				}),
			)
			children.push({ key: ck, label: fdesc, children: items })
			continue
		}
		if (value && typeof value === 'object') {
			children.push(await buildNested(value, ck, fdesc, showAll))
			continue
		}

		/* ─ 标量：三级优先匹配值 ─ */
		const defMatch = matchInValues(fDef?.values, value)
		const keysMatch = matchInValues(fKeys?.values, value)
		const match = resolveMatch(defMatch, keysMatch)

		const visible = match
			? match.display !== false
			: (fDef?.default?.display ?? fKeys?.default?.display ?? fTpl?.default?.display) !== false

		let displayText: string
		if (match) {
			displayText = await applyParse(value, match.parse, action)
		} else if (fDef?.default?.parse) {
			displayText = await applyParse(value, fDef.default.parse, action)
		} else if (fKeys?.default?.parse) {
			displayText = await applyParse(value, fKeys.default.parse, action)
		} else if (fTpl?.default?.parse) {
			displayText = await applyParse(value, fTpl.default.parse, action)
		} else {
			displayText = fmt(value)
		}

		if (visible || showAll)
			children.push(leaf(ck, `${fdesc}: ${displayText}`, visible))
	}

	return children.length
		? { key: baseKey, label, children }
		: leaf(baseKey, label)
}

/** 构建 eventToActions 记录 */
async function buildEvents(
	record: Record<string, unknown[]>,
	baseKey: string,
	showAll: boolean,
): Promise<TreeOption> {
	const children: TreeOption[] = []
	const eventList = await loadEventList()

	for (const [event, actions] of Object.entries(record)) {
		const ek = `${baseKey}/${event}`
		const eventMatch = matchInValues(eventList?.values, event)
		let eventLabel = event
		if (eventMatch?.parse)
			eventLabel = await applyParse(event, eventMatch.parse, {})

		const actionNodes = await Promise.all(
			(actions as Record<string, unknown>[]).map((a, i) =>
				buildAction(a, `${ek}/${i}`, showAll, `[${i}]`),
			).filter(Boolean),
		)
		children.push({ key: ek, label: eventLabel, children: actionNodes })
	}

	return { key: baseKey, label: '事件 → 动作', children }
}

/**
 * 将一条 buff JSON 解析为 naive-ui TreeOption[] 树结构。
 *
 * 解析优先级：
 *   actions/{type}.yml > action_keys.yml > action_keys_template.yml
 *
 * 复杂字段（object / array）递归展开为子节点。
 */
export async function parseBuffsToTree(
	buff: Record<string, unknown> | undefined,
	showAll = false,
): Promise<TreeOption[]> {
	if (!buff) return []

	const index = await loadIndex()
	const result: TreeOption[] = []

	for (const [key, value] of Object.entries(buff)) {
		/* eventToActions 是特殊的 record 结构 */
		if (key === 'eventToActions') {
			result.push(
				await buildEvents(value as Record<string, unknown[]>, key, showAll),
			)
			continue
		}

		const schema = index?.[key]
		const desc: string = schema?.description ?? humanize(key)

		/* 字段级 display 检查 */
		const fieldVisible = schema?.display !== false
		if (!fieldVisible && !showAll) continue

		/* 复杂顶层字段 */
		if (value && typeof value === 'object') {
			result.push(await buildNested(value, key, desc, showAll))
			continue
		}

		/* 标量顶层字段：index.yml 匹配 → default parse → 原始值 */
		const match = matchInValues(schema?.values, value)
		const visible = fieldVisible && (match ? match.display !== false : true)

		let displayText: string
		if (match)
			displayText = await applyParse(value, match.parse, buff)
		else if (schema?.default?.parse)
			displayText = await applyParse(value, schema.default.parse, buff)
		else
			displayText = fmt(value)

		if (visible || showAll)
			result.push(leaf(key, `${desc}: ${displayText}`, visible))
	}

	return result
}

