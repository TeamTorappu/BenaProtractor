import { loadPublicJSON } from "./usePublic";
import { useMemoize } from "@vueuse/core";

interface RogueData {
    itemKey: string;
    itemInfo: any;
    itemData: any;
    season: string;
}

export interface RogueItem {
    id: string;
    name: string;
    parsedName: string;
    type: string;
    data: RogueData;
}

export const typeNameMap: Record<string, string> = {
    RELIC: "藏品",
    BAND: "分队",
    RECRUIT_TICKET: "招募券",
    UPGRADE_TICKET: "进阶券",
    ACTIVE_TOOL: "支援装置",
    FEATURE: "机制",
    COPPER_BUFF: "钱",
    WRATH: "岁时",
};

async function _loadRogueSeasons(): Promise<Record<string, string>> {
    const rogue_table = await loadPublicJSON("gamedata/excel/roguelike_topic_table.json");
    return Object.fromEntries(
        Object.entries(rogue_table.topics as Record<string, { name: string }>).map(
            ([key, val]: [string, { name: string }]) => [key, val.name]
        )
    );
}

export const loadRogueSeasons = useMemoize(async () => await _loadRogueSeasons());

async function _buildRogueObjects(): Promise<RogueItem[]> {
    const rogue_table = await loadPublicJSON("gamedata/excel/roguelike_topic_table.json");
    const rogue_seasons = await loadRogueSeasons();
    const result: RogueItem[] = [];

    const details = rogue_table.details || {};
    
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
export const buildRogueObjects = useMemoize(async () => await _buildRogueObjects());