import { loadPublicJSON } from "./usePublic";
import { useMemoize } from "@vueuse/core";

export const BuffCategory: Record<string, string> = {
    CHAR: "干员",
    ENEMY: "敌人",
    MODULE: "干员模组",
    UNKNOWN: "未知"
};

export interface BuffItem {
    id: string;
    parsedName: string;
    category: typeof BuffCategory[keyof typeof BuffCategory];
    data: any;
}

export const loadCharMapping = useMemoize(async (): Promise<Record<string, string>> => {
    const data = await loadPublicJSON("gamedata/excel/character_table.json");
    const mapping: Record<string, string> = {};
    for (const key in data) {
        const charData = data[key];
        const name = charData.name || "未知";
        let processedKey = key;
        if (key.includes("_")) {
            processedKey = key.split("_").slice(2).join("_");
        }
        mapping[processedKey] = name;
    }
    return mapping;
});

export const loadEnemyMapping = useMemoize(async (): Promise<Record<string, string>> => {
    const data = await loadPublicJSON("gamedata/levels/enemydata/enemy_database.json");
    const mapping: Record<string, string> = {};
    const enemies = data.enemies || [];
    for (const enemyStruct of enemies) {
        const key = enemyStruct.Key;
        const name = enemyStruct.Value?.[0]?.enemyData?.name?.m_value || "未知";
        let processedKey = key || "";
        if (processedKey.includes("_")) {
            processedKey = processedKey.split("_").slice(2).join("_");
        }
        if (processedKey) {
            mapping[processedKey] = name;
        }
    }
    return mapping;
});

function parseBuffInfo(key: string, charMapping: Record<string, string>, enemyMapping: Record<string, string>): { name: string, category: typeof BuffCategory[keyof typeof BuffCategory] } {
    // 默认分类
    let category: typeof BuffCategory[keyof typeof BuffCategory] = BuffCategory.UNKNOWN;

    // 处理敌方单位
    if (key.startsWith("enemy_")) {
        category = BuffCategory.ENEMY;
        const parts = key.slice(6).replace("[", "_[").split("_");
        let display = "";
        let rest: string[] = [];

        // 尝试匹配 _2 后缀的敌人
        const keyWith2 = `${parts[0]}_${parts[1]}`;
        if (parts.length > 1 && parts[1] === "2" && enemyMapping[keyWith2]) {
            display = `敌_${enemyMapping[keyWith2]}`;
            rest = parts.slice(2);
        } else if (parts.length > 0 && enemyMapping[parts[0]]) {
            display = `敌_${enemyMapping[parts[0]]}`;
            rest = parts.slice(1);
        }

        if (display) {
            if (rest[0] === "t") {
                display += "天赋";
                rest.shift();
            } else if (rest[0] === "s") {
                if (rest.length > 1 && ["1", "2", "3"].includes(rest[1])) {
                    display += `${rest[1]}技能`;
                    rest.splice(0, 2);
                } else {
                    display += "技能";
                    rest.shift();
                }
            }
            return { name: rest.length > 0 ? `${display}_${rest.join("_")}` : display, category };
        }
    }

    // 处理干员
    const parts = key.replace("[", "_[").split("_");
    if (charMapping[parts[0]]) {
        category = BuffCategory.CHAR;
        let display = charMapping[parts[0]];
        let rest = parts.slice(1);

        if (rest.length > 0) {
            const r0 = rest[0];
            if (r0 === "t" || r0 === "t1" || r0 === "t2") {
                const sub = r0 === "t" && ["1", "2", "3"].includes(rest[1]) ? rest[1] : (r0.length > 1 ? r0.slice(1) : "");
                display += `${sub}天赋`;
                rest.splice(0, (r0 === "t" && sub) ? 2 : 1);
            } else if (r0 === "tr" || r0 === "trait") {
                display += "特性";
                rest.shift();
            } else if (r0 === "s" || r0 === "s1" || r0 === "s2" || r0 === "s3") {
                const sub = r0 === "s" && ["1", "2", "3"].includes(rest[1]) ? rest[1] : (r0.length > 1 ? r0.slice(1) : "");
                display += `${sub}技能`;
                rest.splice(0, (r0 === "s" && sub) ? 2 : 1);
            } else if (r0 === "e") {
                category = BuffCategory.MODULE;
                const sub = rest.length > 1 ? rest[1] : "";
                display += `模组${sub}`;
                rest.splice(0, sub ? 2 : 1);
            }
        }
        return { name: rest.length > 0 ? `${display}_${rest.join("_")}` : display, category };
    }

    return { name: key, category };
}

export const buildBuffObjects = useMemoize(async (): Promise<BuffItem[]> => {
    const [buffData, charMapping, enemyMapping] = await Promise.all([
        loadPublicJSON("gamedata/battle/buff_template_data.json"),
        loadCharMapping(),
        loadEnemyMapping()
    ]);

    return Object.entries(buffData).map(([key, data]) => {
        const info = parseBuffInfo(key, charMapping, enemyMapping);
        return {
            id: key,
            parsedName: info.name,
            category: info.category,
            data
        };
    });
});
