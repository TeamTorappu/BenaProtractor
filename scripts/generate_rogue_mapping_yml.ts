import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

type PrimitiveType = "string" | "number" | "boolean" | "null" | "object" | "array";

interface FieldStat {
    types: Set<PrimitiveType>;
    values: Set<string>;
}

interface BlackboardFieldStat {
    valueTypes: Set<PrimitiveType>;
    valueStrTypes: Set<PrimitiveType>;
    pairs: Set<string>; // JSON-serialized { value, valueStr } for dedup
}

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

// ---------------------------------------------------------------------------
// Utility functions (mirroring generate_buff_mapping_yml.ts)
// ---------------------------------------------------------------------------

function getPrimitiveType(val: any): PrimitiveType {
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

function unionTypeString(types: Set<PrimitiveType>): string {
    return Array.from(types).sort().join(" | ");
}

function ensureFieldStat(target: Record<string, FieldStat>, field: string): FieldStat {
    if (!target[field]) {
        target[field] = { types: new Set(), values: new Set() };
    }
    return target[field];
}

function descFromCamelCase(field: string): string {
    return field
        .replace(/^_+/, "")
        .replace(/([A-Z])/g, " $1")
        .trim();
}

function descFromSnakeCase(field: string): string {
    return field
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
}

function toYaml(obj: any, indent = 0): string {
    const spaces = " ".repeat(indent);
    function yamlString(str: string): string {
        if (
            str === "" ||
            /[\[\]:#",\n]/.test(str) ||
            str.startsWith(" ") ||
            str.endsWith(" ") ||
            str.includes("  ") ||
            (str.includes("-") && str.trim() === "-")
            || str.includes("{") || str.includes("[") || str.includes("(")
        ) {
            return '"' + str.replace(/"/g, '\"') + '"';
        }
        return str;
    }

    if (Array.isArray(obj)) {
        return obj
            .map((item) => {
                if (typeof item === "string") {
                    return `${spaces}- ${yamlString(item)}`;
                }
                if (typeof item === "object" && item !== null) {
                    const block = toYaml(item, indent + 2);
                    return `${spaces}-\n${block}`;
                }
                return `${spaces}- ${yamlString(String(item))}`;
            })
            .join("\n");
    }

    if (typeof obj === "object" && obj !== null) {
        const lines: string[] = [];
        for (const key of Object.keys(obj)) {
            const value = obj[key];
            if (typeof value === "object" && value !== null) {
                lines.push(`${spaces}${key}:`);
                lines.push(toYaml(value, indent + 2));
            } else if (typeof value === "string") {
                lines.push(`${spaces}${key}: ${yamlString(value)}`);
            } else {
                lines.push(`${spaces}${key}: ${String(value)}`);
            }
        }
        return lines.join("\n");
    }

    if (typeof obj === "string") {
        return `${spaces}${yamlString(obj)}`;
    }
    return `${spaces}${String(obj)}`;
}

// ---------------------------------------------------------------------------
// Stat collection
// ---------------------------------------------------------------------------

const allItems = buildRogueObjects();

// itemInfo field → type + unique values
const itemInfoFieldStats: Record<string, FieldStat> = {};
// itemData.buffs[].key → unique buff keys
const buffKeySet = new Set<string>();
// itemData.buffs[].blackboard → field stats (value + valueStr pairs)
const blackboardFieldStats: Record<string, BlackboardFieldStat> = {};

for (const item of allItems) {
    // --- itemInfo ---
    const info = item.data.itemInfo;
    if (info && typeof info === "object" && !Array.isArray(info)) {
        for (const [key, val] of Object.entries(info)) {
            const stat = ensureFieldStat(itemInfoFieldStats, key);
            stat.types.add(getPrimitiveType(val));
            stat.values.add(toValueString(val));
        }
    }

    // --- itemData ---
    const buffs = item.data.itemData?.buffs;
    if (!Array.isArray(buffs)) continue;

    for (const buff of buffs) {
        if (buff.key) buffKeySet.add(buff.key);

        const blackboard = buff.blackboard;
        if (!Array.isArray(blackboard)) continue;

        for (const entry of blackboard) {
            const field = entry.key;
            if (!blackboardFieldStats[field]) {
                blackboardFieldStats[field] = {
                    valueTypes: new Set(),
                    valueStrTypes: new Set(),
                    pairs: new Set(),
                };
            }
            const stat = blackboardFieldStats[field];
            stat.valueTypes.add(getPrimitiveType(entry.value));
            stat.valueStrTypes.add(getPrimitiveType(entry.valueStr));
            stat.pairs.add(JSON.stringify({ value: entry.value, valueStr: entry.valueStr }));
        }
    }
}

// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------

const outDir = path.join(__dirname, "generated/rogue/mappings");
fs.mkdirSync(outDir, { recursive: true });

// ---- index.yml ----
const indexDoc: any = {
    itemInfo: {
        type: "object",
        description: "基础数据",
        file: "itemInfo.yml",
    },
    itemData: {
        type: "object",
        description: "buff",
        key: { file: "itemData_keys.yml" },
        value: { file: ["itemData_blackboards.yml", "itemData_blackboards_template.yml"] },
    },
};
fs.writeFileSync(path.join(outDir, "index.yml"), toYaml(indexDoc), { encoding: "utf-8", flag: "w" });

// ---- itemInfo.yml ----
const itemInfoDoc: any = {};
const itemInfoKeys = Object.keys(itemInfoFieldStats).sort();
for (const field of itemInfoKeys) {
    const stat = itemInfoFieldStats[field];
    itemInfoDoc[field] = {
        type: unionTypeString(stat.types),
        description: descFromCamelCase(field),
        // display: true,
        generated: true,
    };
}
fs.writeFileSync(path.join(outDir, "itemInfo.yml"), toYaml(itemInfoDoc), { encoding: "utf-8", flag: "w" });

// ---- itemData_keys.yml ----
const keysDoc: any = {};
const buffKeys = Array.from(buffKeySet).sort();
for (const key of buffKeys) {
    keysDoc[key] = {
        description: descFromSnakeCase(key),
        icon: null,
        // display: true,
        generated: true,
    };
}
fs.writeFileSync(path.join(outDir, "itemData_keys.yml"), toYaml(keysDoc), { encoding: "utf-8", flag: "w" });

// ---- itemData_blackboards_template.yml ----
const bbTemplateDoc: any = {};
const bbFields = Object.keys(blackboardFieldStats).sort();
for (const field of bbFields) {
    const stat = blackboardFieldStats[field];
    const typeStr = unionTypeString(stat.valueTypes);
    bbTemplateDoc[field] = {
        type: typeStr,
        description: field,
        icon: null,
        default: {
            // display: true,
            parse: {
                type: "template",
                return: "{0}({1})",
                args: ["value", "valueStr"],
                generated: true,
            },
        },
    };
}
fs.writeFileSync(
    path.join(outDir, "itemData_blackboards_template.yml"),
    toYaml(bbTemplateDoc),
    { encoding: "utf-8", flag: "w" }
);

// ---- itemData_blackboards.yml ----
const bbDoc: any = {};
for (const field of bbFields) {
    const stat = blackboardFieldStats[field];
    const typeStr = unionTypeString(stat.valueTypes);

    const sortedPairs = Array.from(stat.pairs)
        .map((s) => JSON.parse(s) as { value: any; valueStr: any })
        .sort((a, b) => {
            const aKey = toValueString(a.value) + "|" + toValueString(a.valueStr);
            const bKey = toValueString(b.value) + "|" + toValueString(b.valueStr);
            return aKey.localeCompare(bKey);
        });

    bbDoc[field] = {
        type: typeStr,
        description: field,
        values: sortedPairs.map((pair) => ({
            value: toValueString(pair.value),
            valueStr: toValueString(pair.valueStr),
            // display: false,
            parse: {
                type: "template",
                return: "{0}({1})",
                args: ["value", "valueStr"],
                generated: true,
            },
        })),
    };
}
fs.writeFileSync(path.join(outDir, "itemData_blackboards.yml"), toYaml(bbDoc), { encoding: "utf-8", flag: "w" });

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

console.log(`✓ rogue mappings 已生成: ${outDir}`);
console.log(`✓ itemInfo 字段: ${itemInfoKeys.length}`);
console.log(`✓ buff keys: ${buffKeys.length}`);
console.log(`✓ blackboard 字段: ${bbFields.length}`);

export { buildRogueObjects, loadRogueSeasons, type RogueItem };



