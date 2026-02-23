import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import YAML from "yaml";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

interface RogueData {
    itemKey: string;
    itemInfo: any;
    itemData: any;
    season: string;
}

interface RogueItem {
    id: string;
    name: string;
    parsedName: string;
    type: string;
    data: RogueData;
}

interface BuffFieldStat {
    types: Set<string>;
    values: Set<string>;
}

const typeNameMap: Record<string, string> = {
    RELIC: "藏品",
    BAND: "分队",
    RECRUIT_TICKET: "招募券",
    UPGRADE_TICKET: "进阶券",
    ACTIVE_TOOL: "支援装置",
    FEATURE: "精通",
    COPPER_BUFF: "钱",
};

const roguePath = path.resolve(process.cwd(), "./public/gamedata/excel/roguelike_topic_table.json");
const rogueTable = JSON.parse(fs.readFileSync(roguePath, "utf-8")) as Record<string, any>;

function loadRogueSeasons(): Record<string, string> {
    return Object.fromEntries(
        Object.entries(rogueTable.topics as Record<string, { name: string }>).map(
            ([key, val]: [string, { name: string }]) => [key, val.name]
        )
    );
}

function buildRogueObjects(): RogueItem[] {
    const rogue_seasons = loadRogueSeasons();
    const result: RogueItem[] = [];

    const details = rogueTable.details || {};
    
    for (const season in details) {
        const seasonData = details[season];
        const seasonName = rogue_seasons[season] || season;
        const items = seasonData.items || {};
        const relics = seasonData.relics || {};

        for (const itemKey in items) {
            const itemInfo = items[itemKey];
            
            if (itemKey in relics) {
                const displayType = typeNameMap[itemInfo.type] || "鸽物";

                result.push({
                    id: `${season}|${itemKey}`,
                    name: itemInfo.name,
                    parsedName: `[${displayType}] ${itemInfo.name}(${seasonName.slice(0, 2)})`,
                    type: displayType,
                    data: {
                        itemKey,
                        itemInfo,
                        itemData: relics[itemKey],
                        season,
                    },
                });
            }
        }
    }

    return result;
}

function getPrimitiveType(val: any): string {
    if (val === null) return "null";
    if (Array.isArray(val)) return "array";
    const t = typeof val;
    if (t === "string") return "string";
    if (t === "number") return "number";
    if (t === "boolean") return "boolean";
    return "object";
}

function toValueString(val: any): string {
    if (val === null) return "null";
    if (val === undefined) return "undefined";
    if (typeof val === "string") return val;
    if (typeof val === "number" || typeof val === "boolean") return String(val);
    return JSON.stringify(val);
}

function unionTypeString(types: Set<string>): string {
    const ordered = Array.from(types).sort();
    return ordered.join(" | ");
}

// 统计buffs字段统计
const buffFieldStats: Record<string, BuffFieldStat> = {};
const allBuffs = buildRogueObjects();

for (const item of allBuffs) {
    const buffs = item.data.itemData.buffs;
    if (!Array.isArray(buffs)) continue;

    for (const buff of buffs) {
        const blackboard = buff.blackboard;
        if (!Array.isArray(blackboard)) continue;

        for (const entry of blackboard) {
            const field = entry.key;
            if (!buffFieldStats[field]) {
                buffFieldStats[field] = { types: new Set(), values: new Set() };
            }
            const stat = buffFieldStats[field];
            stat.types.add(getPrimitiveType(entry.value));
            stat.values.add(toValueString(entry.value));
        }
    }
}

// 生成目录结构
const outDir = path.join(__dirname, "generated/rogue");
fs.mkdirSync(outDir, { recursive: true });

// 生成 index.yml - 简化版
const indexDoc: Record<string, any> = {};
const fields = Object.keys(buffFieldStats).sort();
for (const field of fields) {
    const stat = buffFieldStats[field];
    indexDoc[field] = {
        type: unionTypeString(stat.types),
        description: field,
        icon: null,
    };
}

fs.writeFileSync(
    path.join(outDir, "index.yml"),
    YAML.stringify(indexDoc, { nullStr: "" }),
    "utf-8"
);

// 生成 full.yml - 完整版，包含所有值
const fullDoc: Record<string, any> = {};
for (const field of fields) {
    const stat = buffFieldStats[field];
    fullDoc[field] = {
        type: unionTypeString(stat.types),
        description: field,
        icon: null,
        values: Array.from(stat.values)
            .sort()
            .map((value) => ({
                value,
                display: false,
            })),
    };
}

fs.writeFileSync(
    path.join(outDir, "full.yml"),
    YAML.stringify(fullDoc, { nullStr: "" }),
    "utf-8"
);

console.log(`✓ rogue mappings 已生成: ${outDir}`);
console.log(`✓ 已统计 ${fields.length} 个buff字段`);
console.log(`  - 字段: ${fields.join(", ")}`);

export { buildRogueObjects, loadRogueSeasons, type RogueItem };



