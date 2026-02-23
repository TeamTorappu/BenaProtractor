import { loadPublicYAML } from "@/composables/usePublic";

async function load(path: string): Promise<any> {
    try {
        return await loadPublicYAML(`buff/mappings/${path}`);
    } catch {
        return null;
    }
}

export const loadIndex = () => load("index.yml");
export const loadEventList = () => load("event_list.yml");
export const loadActionNodes = () => load("action_nodes.yml");
export const loadActionKeysTemplate = () => load("action_keys_template.yml");
export const loadActionKeys = () => load("action_keys.yml");
export const loadActionDef = (type: string) => load(`actions/${type}.yml`);
export const loadSubSchema = (path: string) => load(path);
