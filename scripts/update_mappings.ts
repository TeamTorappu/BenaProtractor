/**
 * update_mappings.ts
 *
 * 智能合并 scripts/generated/ → public/ 的 YAML 映射文件。
 *
 * 规则：
 *   - generated: true 的节点 → 用新生成的内容替换
 *   - 没有 generated: true 的节点 → 保留 public 中人工修改的版本
 *   - generated 中新增的字段 / 文件 → 追加到 public
 *   - public 中存在但 generated 中不存在的 → 不删除
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { parse as parseYaml, stringify as stringifyYaml } from "yaml";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

interface Stats {
	updated: number;
	added: number;
	skipped: number;
	errored: number;
}

/* ─── generated 标记检测 ─── */

/**
 * 递归检查节点（含子树）是否包含 generated: true。
 * 用于判断 public 侧的某个节点是否仍是自动生成的。
 */
function hasGenerated(node: unknown): boolean {
	if (!node || typeof node !== "object") return false;

	if (Array.isArray(node))
		return node.some(hasGenerated);

	const obj = node as Record<string, unknown>;
	if (obj.generated === true) return true;

	return Object.values(obj).some(hasGenerated);
}

/* ─── values 数组合并 ─── */

/**
 * 构造 values 数组条目的唯一 key。
 * buff 使用 value，rogue 使用 value + valueStr。
 */
function valueEntryKey(entry: Record<string, unknown>): string {
	const v = String(entry.value ?? "");
	if ("valueStr" in entry)
		return `${v}|${String(entry.valueStr ?? "")}`;
	return v;
}

/**
 * 合并 values 数组：以 value(+valueStr) 为 key 做匹配。
 *   - 匹配到且 pub 条目有 generated → 替换
 *   - 匹配到但 pub 条目没有 generated → 保留 pub
 *   - gen 独有 → 追加
 *   - pub 独有 → 保留
 */
function mergeValuesArray(
	pubArr: Record<string, unknown>[],
	genArr: Record<string, unknown>[],
): Record<string, unknown>[] {
	const pubMap = new Map<string, Record<string, unknown>>();
	for (const entry of pubArr)
		pubMap.set(valueEntryKey(entry), entry);

	const seen = new Set<string>();
	const result: Record<string, unknown>[] = [];

	/* 保留 pub 的顺序 */
	for (const pubEntry of pubArr) {
		const key = valueEntryKey(pubEntry);
		seen.add(key);
		result.push(pubEntry); // 先放 pub 版本
	}

	/* gen 中新增的条目追加 */
	for (const genEntry of genArr) {
		const key = valueEntryKey(genEntry);
		if (seen.has(key)) {
			/* 已存在：看 pub 版本是否 generated */
			const pubEntry = pubMap.get(key)!;
			if (hasGenerated(pubEntry)) {
				const idx = result.indexOf(pubEntry);
				if (idx >= 0) result[idx] = genEntry;
			}
			/* 否则保留 pub */
		} else {
			result.push(genEntry);
		}
	}

	return result;
}

/* ─── 深度合并 ─── */

function deepMerge(pub: unknown, gen: unknown): unknown {
	if (gen === null || gen === undefined) return pub;
	if (pub === null || pub === undefined) return gen;

	/* 两边都是数组 → 不做递归合并（除了 values 数组由上层处理） */
	if (Array.isArray(pub) && Array.isArray(gen))
		return pub;

	/* 两边都是 object */
	if (typeof pub === "object" && typeof gen === "object"
		&& !Array.isArray(pub) && !Array.isArray(gen)) {
		const pubObj = pub as Record<string, unknown>;
		const genObj = gen as Record<string, unknown>;
		const result: Record<string, unknown> = { ...pubObj };

		for (const key of Object.keys(genObj)) {
			if (!(key in pubObj)) {
				/* 新字段：直接添加 */
				result[key] = genObj[key];
				continue;
			}

			/*
			 * values 数组需要特殊处理：按 value 做 keyed 合并
			 */
			if (key === "values"
				&& Array.isArray(pubObj[key])
				&& Array.isArray(genObj[key])) {
				result[key] = mergeValuesArray(
					pubObj[key] as Record<string, unknown>[],
					genObj[key] as Record<string, unknown>[],
				);
				continue;
			}

			/* pub 侧该节点整体仍是 generated → 替换 */
			if (hasGenerated(pubObj[key])) {
				result[key] = genObj[key];
				continue;
			}

			/* pub 侧是人工修改 → 递归合并子节点（仅对 object） */
			if (typeof pubObj[key] === "object" && typeof genObj[key] === "object"
				&& !Array.isArray(pubObj[key]) && !Array.isArray(genObj[key])) {
				result[key] = deepMerge(pubObj[key], genObj[key]);
				continue;
			}

			/* 标量 / 类型不同 → 保留 pub */
		}

		return result;
	}

	/* 标量 → 保留 pub */
	return pub;
}

/* ─── 文件遍历 ─── */

function walkYml(dir: string): string[] {
	const result: string[] = [];
	if (!fs.existsSync(dir)) return result;

	for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
		const full = path.join(dir, entry.name);
		if (entry.isDirectory()) {
			result.push(...walkYml(full));
		} else if (entry.name.endsWith(".yml")) {
			result.push(full);
		}
	}
	return result;
}

/* ─── 主流程 ─── */

const MAPPING_PAIRS = [
	{ gen: "generated/buff/mappings", pub: "../public/buff/mappings" },
	{ gen: "generated/rogue/mappings", pub: "../public/rogue/mappings" },
];

const stats: Stats = { updated: 0, added: 0, skipped: 0, errored: 0 };

const STRINGIFY_OPTS = {
	indent: 2,
	lineWidth: 0,
	defaultStringType: "PLAIN" as const,
	defaultKeyType: "PLAIN" as const,
};

for (const pair of MAPPING_PAIRS) {
	const genDir = path.resolve(__dirname, pair.gen);
	const pubDir = path.resolve(__dirname, pair.pub);

	if (!fs.existsSync(genDir)) continue;
	fs.mkdirSync(pubDir, { recursive: true });

	const genFiles = walkYml(genDir);

	for (const genFile of genFiles) {
		const rel = path.relative(genDir, genFile);
		const pubFile = path.join(pubDir, rel);

		if (!fs.existsSync(pubFile)) {
			fs.mkdirSync(path.dirname(pubFile), { recursive: true });
			fs.copyFileSync(genFile, pubFile);
			stats.added++;
			continue;
		}

		try {
			const genContent = fs.readFileSync(genFile, "utf-8");
			const pubContent = fs.readFileSync(pubFile, "utf-8");

			const genDoc = parseYaml(genContent) as Record<string, unknown>;
			const pubDoc = parseYaml(pubContent) as Record<string, unknown>;

			if (!genDoc || !pubDoc) {
				stats.skipped++;
				continue;
			}

			const merged = deepMerge(pubDoc, genDoc) as Record<string, unknown>;

			const mergedYaml = stringifyYaml(merged, STRINGIFY_OPTS);
			const normalizedPub = stringifyYaml(pubDoc, STRINGIFY_OPTS);

			if (mergedYaml !== normalizedPub) {
				fs.writeFileSync(pubFile, mergedYaml, "utf-8");
				stats.updated++;
			} else {
				stats.skipped++;
			}
		} catch (err) {
			console.error(`✗ ${rel}: ${(err as Error).message}`);
			stats.errored++;
		}
	}
}

console.log(`✓ 合并完成`);
console.log(`  新增文件: ${stats.added}`);
console.log(`  更新文件: ${stats.updated}`);
console.log(`  无变化: ${stats.skipped}`);
if (stats.errored > 0)
	console.log(`  ✗ 解析失败: ${stats.errored}`);
