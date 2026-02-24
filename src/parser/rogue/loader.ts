import { loadPublicYAML } from "@/composables/usePublic";

async function load(path: string): Promise<any> {
    try {
        return await loadPublicYAML(`rogue/mappings/${path}`);
    } catch (error) {
        console.error(`Failed to load ${path}`, error);
    }
}

export const loadIndex = () => load("index.yml");
export const loadItemInfo = () => load("itemInfo.yml");
export const loadItemDataKeys = () => load("itemData_keys.yml");
export const loadBlackboardsTemplate = () => load("itemData_blackboards_template.yml");
export const loadBlackboards = () => load("itemData_blackboards.yml");
