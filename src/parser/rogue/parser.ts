import type { TreeOption } from 'naive-ui'
import { fnMap } from '@/parser/buff/fn'

function humanize(key: string): string {
	return key
		.replace(/^_/, '')
		.replace(/([a-z])([A-Z])/g, '$1 $2')
}

function fmt(v: unknown): string {
	if (v === null || v === undefined) return 'null'
	if (typeof v === 'boolean') return v ? '是' : '否'
	if (Array.isArray(v) && v.length === 0) return '[]'
	return String(v)
}

async function parseBlackboardValue(
	value: number | string | null
): Promise<string> {
	if (value === null) return 'null'
	
	// 如果存在parseNumber函数则使用
	const parseNumber = fnMap.get('parseNumber')
	if (typeof value === 'number' && parseNumber) {
		try {
			const result = await parseNumber(value, {})
			return String(result)
		} catch {
			return String(value)
		}
	}
	
	return fmt(value)
}

export async function parseRogueToTree(
	itemData: any,
	_showAll: boolean = false
): Promise<TreeOption[]> {
	if (!itemData || typeof itemData !== 'object') {
		return [{ key: 'root', label: 'null', isLeaf: true }]
	}

	const buffs = itemData.buffs
	if (!Array.isArray(buffs) || buffs.length === 0) {
		return [{ key: 'buffs', label: 'buffs: []', isLeaf: true }]
	}

	const buffNodes: TreeOption[] = []
	
	for (let i = 0; i < buffs.length; i++) {
		const buff = buffs[i]
		if (!buff || typeof buff !== 'object') continue

		const buffKey = buff.key || `buff_${i}`
		const blackboard = buff.blackboard || []

		const bbChildren: TreeOption[] = []
		
		if (Array.isArray(blackboard)) {
			for (const entry of blackboard) {
				if (!entry || typeof entry !== 'object') continue
				
				const field = entry.key
				const value = entry.value
				const valueStr = entry.valueStr
				
				const fieldLabel = humanize(field)
				const displayValue = await parseBlackboardValue(value)
				
				const entryLabel = valueStr !== null && valueStr !== undefined && valueStr !== ""
					? `${fieldLabel}: ${displayValue} (${valueStr})`
					: `${fieldLabel}: ${displayValue}`
				
				bbChildren.push({
					key: `${i}/${field}`,
					label: entryLabel,
					isLeaf: true
				})
			}
		}

		buffNodes.push({
			key: `buff_${i}`,
			label: `[${i}] ${buffKey}`,
			children: bbChildren.length > 0 ? bbChildren : undefined
		})
	}

	return [
		{
			key: 'buffs',
			label: `buffs (${buffs.length})`,
			children: buffNodes
		}
	]
}
