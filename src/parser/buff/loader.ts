import { loadPublicYAML } from "@/composables/usePublic";

const pending = new Map<string, Promise<any>>();

function load(path: string): Promise<any> {
    const full = `buff/mappings/${path}`;
    if (!pending.has(full))
        pending.set(
            full,
            loadPublicYAML(full).catch(() => null),
        );
    return pending.get(full)!;
}

export const loadIndex = () => load("index.yml");
export const loadEventList = () => load("event_list.yml");
export const loadActionNodes = () => load("action_nodes.yml");
export const loadActionKeysTemplate = () => load("action_keys_template.yml");
export const loadActionKeys = () => load("action_keys.yml");
export const loadActionDef = (type: string) => load(`actions/${type}.yml`);
export const loadSubSchema = (path: string) => load(path);
