import type { TreeOption } from 'naive-ui'
import {
	loadItemInfo,
	loadItemDataKeys,
	loadBlackboards,
	loadBlackboardsTemplate,
} from './loader'
import { fnMap } from '@/parser/rogue/fn'

/* ────────────────── helpers ────────────────── */

function fmt(v: unknown): string {
	if (v === null || v === undefined) return 'null'
	if (typeof v === 'boolean') return v ? '是' : '否'
	if (Array.isArray(v) && v.length === 0) return '[]'
	return String(v)
}

function isGenerated(parse: any): boolean {
	return parse?.generated === true
}

/* ────────────────── resolveArg / splitArgs ────────────────── */

function splitArgs(s: string): string[] {
	const parts: string[] = []
	let depth = 0
	let start = 0
	for (let i = 0; i < s.length; i++) {
		if (s[i] === '(') depth++
		else if (s[i] === ')') depth--
		else if (s[i] === ',' && depth === 0) {
			parts.push(s.slice(start, i))
			start = i + 1
		}
	}
	parts.push(s.slice(start))
	return parts
}

async function resolveArg(arg: string, value: unknown, ctx: unknown): Promise<unknown> {
	if (arg === '$input') return value
	if (arg === '$ctx') return ctx

	/* ctx 字段引用：args 中直接写 "value" / "valueStr" 等字段名 */
	if (ctx && typeof ctx === 'object' && arg in (ctx as Record<string, unknown>))
		return (ctx as Record<string, unknown>)[arg]

	const m = arg.match(/^(\w+)\((.+)\)$/)
	if (m) {
		const fn = fnMap.get(m[1])
		if (fn) {
			const inner = splitArgs(m[2])
			const resolved = await Promise.all(
				inner.map(a => resolveArg(a.trim(), value, ctx)),
			)
			return await fn(...resolved)
		}
	}
	return arg
}

/* ────────────────── applyParse ────────────────── */

async function applyParse(
	value: unknown,
	parse: { type: string; return?: unknown; name?: string; args?: string[] },
	ctx: unknown,
): Promise<string> {
	if (parse.type === 'literal')
		return fmt(parse.return ?? value)

	if (parse.type === 'template' && parse.return) {
		const template = String(parse.return)
		const resolved = await Promise.all(
			(parse.args ?? []).map(a => resolveArg(String(a), value, ctx)),
		)

		/* 过滤：如果任意占位参数为 null/undefined，跳过对应的括号片段 */
		const result = template.replace(/\{(\d+)\}/g, (_, idx) => {
			const v = resolved[Number(idx)]
			if (v === null || v === undefined) return ''
			return fmt(v)
		})
		/* 清理空括号残留，如 "1(null)" → "1"，"1()" → "1" */
		return result.replace(/\(\s*\)/g, '').trim()
	}

	if (parse.type === 'fn' && parse.name) {
		const fn = fnMap.get(parse.name)

		if (fn) {
			const args = await Promise.all(
				(parse.args ?? []).map(a => resolveArg(String(a), value, ctx)),
			)
			return String(await fn(...args))
		}
	}
	return fmt(value)
}

/* ────────────────── value matching ────────────────── */

/**
 * 在 blackboard values 中查找匹配条目。
 * rogue 的 blackboard entry 同时携带 value 和 valueStr，两者都必须匹配。
 */
function matchInBlackboardValues(
	values: any[] | undefined,
	value: unknown,
	valueStr: unknown,
): { display: boolean; parse: any } | null {
	if (!values) return null
	const nv = String(value ?? 'null')
	const nvs = String(valueStr ?? 'null')
	for (const entry of values) {
		if (String(entry.value ?? 'null') === nv
			&& String(entry.valueStr ?? 'null') === nvs)
			return entry
	}
	return null
}

/* ────────────────── tree node helpers ────────────────── */

function leaf(key: string, label: string, display = true): TreeOption {
	return { key, label, isLeaf: true, display }
}

/* ────────────────── build blackboard entry ────────────────── */

async function buildBlackboardEntry(
	entry: Record<string, unknown>,
	baseKey: string,
	bb: any,
	tpl: any,
	showAll: boolean,
): Promise<TreeOption | null> {
	const field = entry.key as string
	const value = entry.value
	const valueStr = entry.valueStr

	const fBb = bb?.[field]
	const fTpl = tpl?.[field]
	let desc: string
	if (fBb?.description && fBb.description !== field) {
		desc = fBb.description
	} else if (fTpl?.description) {
		desc = fTpl.description
	} else {
		desc = field
	}

	/* 值匹配 */
	const match = matchInBlackboardValues(fBb?.values, value, valueStr)

	/* display：match > default > true */
	let visible: boolean
	if (match)
		visible = match.display !== false
	else
		visible = (fBb?.default?.display ?? fTpl?.default?.display) !== false

	/* 构建上下文供 template args 中的 "value" / "valueStr" 字段引用 */
	const ctx = { value, valueStr, field }

	/* parse 优先级：如果模板默认是 fn，优先使用它（即便 match 是生成的） */
	let displayText: string
	if (fTpl?.default?.parse?.type === 'fn') {
		displayText = await applyParse(value, fTpl.default.parse, ctx)
	} else if (match?.parse && !isGenerated(match.parse)) {
		displayText = await applyParse(value, match.parse, ctx)
	} else if (fBb?.default?.parse && !isGenerated(fBb.default.parse)) {
		displayText = await applyParse(value, fBb.default.parse, ctx)
	} else if (fTpl?.default?.parse && !isGenerated(fTpl.default.parse)) {
		displayText = await applyParse(value, fTpl.default.parse, ctx)
	} else if (match?.parse) {
		displayText = await applyParse(value, match.parse, ctx)
	} else if (fBb?.default?.parse) {
		displayText = await applyParse(value, fBb.default.parse, ctx)
	} else if (fTpl?.default?.parse) {
		displayText = await applyParse(value, fTpl.default.parse, ctx)
	} else {
		const vs = valueStr != null ? ` (${fmt(valueStr)})` : ''
		displayText = `${fmt(value)}${vs}`
	}

	if (!displayText && visible)
		visible = false

	if (!visible && !showAll)
		return null

	return leaf(baseKey, `${desc}: ${displayText}`, visible)
}

/* ────────────────── build single buff ────────────────── */

async function buildBuff(
	buff: Record<string, unknown>,
	baseKey: string,
	keys: any,
	bb: any,
	tpl: any,
	showAll: boolean,
	index: number,
): Promise<TreeOption> {
	const buffKey = (buff.key as string) || `buff_${index}`
	const keySchema = keys?.[buffKey]
	const desc = keySchema?.description ?? buffKey
	const keyVisible = keySchema?.display !== false

	if (!keyVisible && !showAll)
		return leaf(baseKey, `[${index}] ${desc}`, false)

	const blackboard = buff.blackboard as any[] | undefined
	if (!Array.isArray(blackboard) || blackboard.length === 0)
		return leaf(baseKey, `[${index}] ${desc}: (空)`)

	const children: TreeOption[] = []
	for (let j = 0; j < blackboard.length; j++) {
		const entry = blackboard[j]
		if (!entry || typeof entry !== 'object') continue
		const node = await buildBlackboardEntry(
			entry, `${baseKey}/${j}`, bb, tpl, showAll,
		)
		if (node) children.push(node)
	}

	const label = `[${index}] ${desc}`
	return children.length
		? { key: baseKey, label, children }
		: leaf(baseKey, label)
}

/* ────────────────── build itemInfo ────────────────── */

async function buildItemInfo(
	info: Record<string, unknown>,
	showAll: boolean,
): Promise<TreeOption> {
	const schema = await loadItemInfo()
	const children: TreeOption[] = []

	for (const [key, value] of Object.entries(info)) {
		const ck = `itemInfo/${key}`
		const field = schema?.[key]
		const desc = field?.description ?? key
		const visible = field?.display !== false

		if (!visible && !showAll) continue

		let displayText: string
		if (field?.default?.parse) {
			displayText = await applyParse(value, field.default.parse, info)
		} else {
			displayText = fmt(value)
		}

		children.push(leaf(ck, `${desc}: ${displayText}`, visible))
	}

	return children.length
		? { key: 'itemInfo', label: '基础数据', children }
		: leaf('itemInfo', '基础数据: (空)')
}

/* ────────────────── public API ────────────────── */

/**
 * 将一条 rogue data 解析为 naive-ui TreeOption[] 树结构。
 * 接收完整的 rogueItem.data（含 itemInfo + itemData）。
 *
 * 解析优先级：
 *   itemData_blackboards.yml (match) > itemData_blackboards_template.yml (default)
 *   手动配置 > 自动生成配置
 */
export async function parseRogueToTree(
	data: { itemInfo?: Record<string, unknown>; itemData?: Record<string, unknown> } | undefined,
	showAll = false,
): Promise<TreeOption[]> {
	if (!data) return []

	const result: TreeOption[] = []

	/* itemInfo */
	if (data.itemInfo && typeof data.itemInfo === 'object')
		result.push(await buildItemInfo(data.itemInfo, showAll))

	/* buffs */
	const buffs = (data.itemData as any)?.buffs as any[] | undefined
	if (!Array.isArray(buffs) || buffs.length === 0) {
		result.push(leaf('buffs', 'buffs: []'))
		return result
	}

	const [keys, bb, tpl] = await Promise.all([
		loadItemDataKeys(),
		loadBlackboards(),
		loadBlackboardsTemplate(),
	])

	const children: TreeOption[] = []
	for (let i = 0; i < buffs.length; i++) {
		const b = buffs[i]
		if (!b || typeof b !== 'object') continue
		children.push(
			await buildBuff(b, `buff/${i}`, keys, bb, tpl, showAll, i),
		)
	}

	result.push({
		key: 'buffs',
		label: `buffs (${buffs.length})`,
		children,
	})

	return result
}
