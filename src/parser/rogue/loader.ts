import { loadPublicYAML } from "@/composables/usePublic";

async function load(path: string): Promise<any> {
    try {
        return await loadPublicYAML(`rogue/${path}`);
    } catch {
        return null;
    }
}

export const loadRogueIndex = () => load("index.yml");
export const loadRogueFull = () => load("full.yml");
