import type { TreeOption } from 'naive-ui'

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