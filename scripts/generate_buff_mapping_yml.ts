import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

type PrimitiveType = "string" | "number" | "boolean" | "null" | "object" | "array";

interface FieldStat {
    types: Set<PrimitiveType>;
    values: Set<string>;
}

interface ActionFieldStatMap {
    [fieldName: string]: FieldStat;
}

interface ActionStatsMap {
    [actionType: string]: ActionFieldStatMap;
}

const buffDataPath = path.join(__dirname, "../public/gamedata/battle/buff_template_data.json");
const buffData = JSON.parse(fs.readFileSync(buffDataPath, "utf-8")) as Record<string, any>;

const baseFieldStats: Record<string, FieldStat> = {};
const eventTypes = new Set<string>();
const actionStats: ActionStatsMap = {};
const actionFieldStats: Record<string, FieldStat> = {};
const complexFieldStats: Record<string, Record<string, FieldStat>> = {}; // 复杂字段在各action中的值统计
const dynamicComplexFields = new Set<string>(); // 动态生成的复杂字段（type为object或array）

function ensureFieldStat(target: Record<string, FieldStat>, field: string) {
    if (!target[field]) {
        target[field] = { types: new Set(), values: new Set() };
    }
    return target[field];
}

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

function extractActionType(typeStr: string): string {
    const match = typeStr.match(/\+(\w+),/);
    if (match) return match[1];
    return "Unknown";
}

function sanitizeFileName(name: string): string {
    return name.replace(/[^A-Za-z0-9_\-]/g, "_");
}

function unionTypeString(types: Set<PrimitiveType>): string {
    const ordered = Array.from(types).sort();
    return ordered.join(" | ");
}

/**
 * 根据复杂字段的实际值检测应使用的 parse 函数名。
 * 含 $type → action 节点；否则按 array / object 分派。
 */
function detectParseFn(fieldName: string, actionType?: string): string {
    const sources: Iterable<string>[] = [];
    if (actionType && complexFieldStats[fieldName]?.[actionType]) {
        sources.push(complexFieldStats[fieldName][actionType].values);
    } else if (complexFieldStats[fieldName]) {
        for (const stat of Object.values(complexFieldStats[fieldName])) {
            sources.push(stat.values);
        }
    }
    for (const vals of sources) {
        for (const v of vals) {
            if (v.includes('"$type"')) {
                return v.startsWith('[') ? 'parseActionArray' : 'parseActionNode';
            }
        }
    }
    const types = actionType
        ? (actionStats[actionType]?.[fieldName]?.types ?? new Set())
        : (actionFieldStats[fieldName]?.types ?? new Set());
    return types.has('array') ? 'parseArrayDefault' : 'parseObjectDefault';
}

function toYaml(obj: any, indent = 0): string {
    const spaces = " ".repeat(indent);
    function yamlString(str: string): string {
        if (str === "" || /[\[\]:#",\n]/.test(str) || str.startsWith(" ") || str.endsWith(" ") || str.includes("  ") || (str.includes("-") && str.trim() === "-")) {
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
        const keys = Object.keys(obj);
        for (const key of keys) {
            const value = obj[key];
            if (typeof value === "object" && value !== null) {
                const block = toYaml(value, indent + 2);
                lines.push(`${spaces}${key}:`);
                lines.push(block);
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

// 统计基础字段与 eventToActions
for (const value of Object.values(buffData)) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        continue;
    }

    for (const [key, fieldValue] of Object.entries(value)) {
        if (key === "templateKey") continue;
        if (key === "eventToActions") continue;
        const stat = ensureFieldStat(baseFieldStats, key);
        stat.types.add(getPrimitiveType(fieldValue));
        stat.values.add(toValueString(fieldValue));
    }

    const eventToActions = (value as any).eventToActions;
    if (!eventToActions || typeof eventToActions !== "object") continue;
    for (const [eventType, actionList] of Object.entries(eventToActions)) {
        eventTypes.add(eventType);
        if (!Array.isArray(actionList)) continue;
        for (const action of actionList) {
            if (!action || typeof action !== "object") continue;
            const actionType = extractActionType(action["$type"] || "");
            if (!actionStats[actionType]) actionStats[actionType] = {};
            for (const [fieldName, fieldValue] of Object.entries(action)) {
                if (fieldName === "$type") continue;
                const fieldType = getPrimitiveType(fieldValue);
                const isComplex = fieldType === "object" || fieldType === "array";

                if (isComplex) {
                    dynamicComplexFields.add(fieldName);
                }

                const actionFieldStat = ensureFieldStat(actionStats[actionType], fieldName);
                actionFieldStat.types.add(fieldType);
                const valStr = isComplex ? `!!action_${fieldName}` : toValueString(fieldValue);
                actionFieldStat.values.add(valStr);

                const globalStat = ensureFieldStat(actionFieldStats, fieldName);
                globalStat.types.add(fieldType);
                globalStat.values.add(valStr);

                // 复杂字段：单独统计每个字段在各action中的值
                if (isComplex) {
                    if (!complexFieldStats[fieldName]) {
                        complexFieldStats[fieldName] = {};
                    }
                    if (!complexFieldStats[fieldName][actionType]) {
                        complexFieldStats[fieldName][actionType] = { types: new Set(), values: new Set() };
                    }
                    complexFieldStats[fieldName][actionType].types.add(fieldType);
                    complexFieldStats[fieldName][actionType].values.add(toValueString(fieldValue));
                }
            }
        }
    }
}

const outDir = path.join(__dirname, "generated/buff/mappings");
const actionDir = path.join(outDir, "actions");
const subschemaDir = path.join(outDir, "action_subschema");
fs.mkdirSync(outDir, { recursive: true });
fs.mkdirSync(actionDir, { recursive: true });
fs.mkdirSync(subschemaDir, { recursive: true });

// index.yml
const indexDoc: any = {};
const baseKeys = Object.keys(baseFieldStats).sort();
for (const field of baseKeys) {
    const stat = baseFieldStats[field];
    const indexFieldDoc: any = {
        type: unionTypeString(stat.types),
        description: field
            .replace(/^_+/, "")
            .replace(/([A-Z])/g, " $1")
            .trim(),
    };

    // 如果base字段本身是object/array类型，使用schema引用
    const isBaseComplex = stat.types.has("object") || stat.types.has("array");
    if (isBaseComplex) {
        indexFieldDoc.schema = `action_subschema/${field}.yml`;
    } else {
        indexFieldDoc.values = Array.from(stat.values)
            .sort()
            .map((value) => ({
                value,
                display: false,
                parse: {
                    type: "literal",
                    return: value,
                },
            }));
    }
    indexDoc[field] = indexFieldDoc;
}
indexDoc.templateKey = {
    type: "string",
    description: "模板标识",
    display: false,
    default: {
        parse: {
            type: "fn",
            name: "parseTemplateKey",
            args: ["$input", "$ctx"],
        },
    },
};
indexDoc.eventToActions = { type: "record", key: { file: "event_list.yml" }, value: { file: ["action_keys.yml", "actions/*.yml"] } };

fs.writeFileSync(path.join(outDir, "index.yml"), toYaml(indexDoc), "utf-8");

// event_list.yml
const eventListDoc = {
    type: "string",
    values: Array.from(eventTypes)
        .sort()
        .map((evt) => ({
            value: evt,
            display: false,
            parse: {
                type: "literal",
                return: true,
            },
        })),
};
fs.writeFileSync(path.join(outDir, "event_list.yml"), toYaml(eventListDoc), "utf-8");

// action_keys.yml
const actionKeysDoc: any = {};
const actionFieldKeys = Object.keys(actionFieldStats).sort();
for (const field of actionFieldKeys) {
    const stat = actionFieldStats[field];
    const isComplex = dynamicComplexFields.has(field);
    const actionKeysFieldDoc: any = {
        type: unionTypeString(stat.types),
        description: field
            .replace(/^_+/, "")
            .replace(/([A-Z])/g, " $1")
            .trim(),
    };
    if (isComplex) {
        actionKeysFieldDoc.schema = `action_subschema/${field}.yml`;
        actionKeysFieldDoc.parse = {
            type: "fn",
            name: detectParseFn(field),
            args: ["$input", "$ctx"],
        };
    } else {
        actionKeysFieldDoc.values = Array.from(stat.values)
            .sort()
            .map((value) => ({
                value,
                display: false,
                parse: {
                    type: "literal",
                    return: value,
                },
            }));
    }
    actionKeysDoc[field] = actionKeysFieldDoc;
}
fs.writeFileSync(path.join(outDir, "action_keys.yml"), toYaml(actionKeysDoc), "utf-8");

// action_keys_template.yml - 仅包含字段类型、schema与默认解析
const actionKeysTemplateDoc: any = {};
for (const field of actionFieldKeys) {
    const stat = actionFieldStats[field];
    const isComplex = dynamicComplexFields.has(field);
    const typeString = unionTypeString(stat.types);
    const templateFieldDoc: any = {
        type: typeString,
        description: field
            .replace(/^_+/, "")
            .replace(/([A-Z])/g, " $1")
            .trim(),
        icon: null,
    };
    if (isComplex) {
        templateFieldDoc.schema = `action_subschema/${field}.yml`;
        templateFieldDoc.parse = {
            type: "fn",
            name: detectParseFn(field),
            args: ["$input", "$ctx"],
        };
    }
    if (typeString === "boolean") {
        templateFieldDoc.default = {
            display: false,
            parse: {
                type: "fn",
                name: "parseBoolean",
                args: ["$input", "$ctx"],
            },
        };
    } else if (typeString === "number") {
        templateFieldDoc.default = {
            display: false,
            parse: {
                type: "fn",
                name: "parseNumber",
                args: ["$input", "$ctx"],
            },
        };
    }
    actionKeysTemplateDoc[field] = templateFieldDoc;
}
fs.writeFileSync(path.join(outDir, "action_keys_template.yml"), toYaml(actionKeysTemplateDoc), "utf-8");

// action_nodes.yml - action 类型节点（用于树结构展示）
const actionsNodesDoc: any = {};
const actionTypesForNodes = Object.keys(actionStats).sort();
for (const actionType of actionTypesForNodes) {
    actionsNodesDoc[actionType] = {
        description: actionType.replace(/([A-Z])/g, " $1").trim(),
        icon: null,
    };
}
fs.writeFileSync(path.join(outDir, "action_nodes.yml"), toYaml(actionsNodesDoc), "utf-8");

// action_<ActionType>.yml
const actionTypes = Object.keys(actionStats).sort();
for (const actionType of actionTypes) {
    const fieldStats = actionStats[actionType];
    const doc: any = {
        actionType,
        fields: {},
    };
    const fields = Object.keys(fieldStats).sort();
    for (const field of fields) {
        const stat = fieldStats[field];
        const isComplex = dynamicComplexFields.has(field);
        const fieldDoc: any = {
            type: unionTypeString(stat.types),
            description: field
                .replace(/^_+/, "")
                .replace(/([A-Z])/g, " $1")
                .trim(),
        };
        if (isComplex) {
            fieldDoc.schema = `action_subschema/${field}.yml`;
            fieldDoc.parse = {
                type: "fn",
                name: detectParseFn(field, actionType),
                args: ["$input", "$ctx"],
            };
        } else {
            fieldDoc.values = Array.from(stat.values)
                .sort()
                .map((value) => ({
                    value,
                    display: false,
                    parse: {
                        type: "literal",
                        return: value,
                    },
                }));
        }
        doc.fields[field] = fieldDoc;
    }
    const filename = `${sanitizeFileName(actionType)}.yml`;
    fs.writeFileSync(path.join(actionDir, filename), toYaml(doc), "utf-8");
}

// 生成 action_subschema/*.yml - 复杂字段的schema定义
// 包括在action中的复杂字段，以及在base中的复杂字段
const allComplexFields = new Set<string>([
    ...dynamicComplexFields,
    ...Object.keys(baseFieldStats).filter((field) => baseFieldStats[field].types.has("object") || baseFieldStats[field].types.has("array")),
]);

for (const fieldName of allComplexFields) {
    const fieldSchemaDoc: any = {
        field: fieldName,
        type: "object",
        description: fieldName
            .replace(/^_+/, "")
            .replace(/([A-Z])/g, " $1")
            .trim(),
    };

    // 如果这个字段有在action中出现过的值
    if (complexFieldStats[fieldName]) {
        fieldSchemaDoc.actions = {};
        for (const [actionType, stat] of Object.entries(complexFieldStats[fieldName])) {
            const typeStr = unionTypeString(stat.types);
            const fnName = typeStr === "array" ? "parseArrayDefault" : `parse${fieldName.replace(/^_+/, "")}`;
            fieldSchemaDoc.actions[actionType] = {
                type: typeStr,
                values: Array.from(stat.values)
                    .sort()
                    .map((value) => ({
                        value,
                        display: false,
                        parse: {
                            type: "fn",
                            name: fnName,
                            args: ["$input", "$ctx"],
                        },
                    })),
            };
        }
    } else if (baseFieldStats[fieldName]) {
        // 否则使用base中的值
        const stat = baseFieldStats[fieldName];
        const baseTypeStr = unionTypeString(stat.types);
        const baseFnName = baseTypeStr === "array" ? "parseArrayDefault" : `parse${fieldName.replace(/^_+/, "")}`;
        fieldSchemaDoc.type = baseTypeStr;
        fieldSchemaDoc.values = Array.from(stat.values)
            .sort()
            .map((value) => ({
                value,
                display: false,
                parse: {
                    type: "fn",
                    name: baseFnName,
                    args: ["$input", "$ctx"],
                },
            }));
    }

    const filename = `${fieldName}.yml`;
    fs.writeFileSync(path.join(subschemaDir, filename), toYaml(fieldSchemaDoc), "utf-8");
}

console.log(`✓ mappings 已生成: ${outDir}`);
console.log(`✓ 复杂字段个数: ${allComplexFields.size}`);
console.log(`  - action中的复杂字段: ${dynamicComplexFields.size}`);
console.log(`  - base中的复杂字段: ${Object.keys(baseFieldStats).filter((f) => baseFieldStats[f].types.has("object") || baseFieldStats[f].types.has("array")).length}`);
