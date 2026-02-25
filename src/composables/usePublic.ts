import { readTextFile } from "@tauri-apps/plugin-fs";
import { resourceDir } from "@tauri-apps/api/path";
import { join } from "pathe";
import { useMemoize } from "@vueuse/core";
import { parse as parseYaml } from "yaml";

const isTauri = "__TAURI_INTERNALS__" in window;
const isDev = import.meta.env.DEV;

async function _loadPublicText(path: string): Promise<string> {
    if (isTauri && !isDev) {
        const resourcePath = await resourceDir();
        const filePath = join(resourcePath, path);
        try {
            return await readTextFile(filePath);
        } catch (error) {
            console.warn("读取资源目录失败，回退到 fetch：", error);
        }
    }

    const url = path.startsWith("/") ? path : `/${path}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`读取资源失败: ${response.status} ${response.statusText} (${url})`);
    }
    return await response.text();
}

async function _loadPublicJSON(path: string) {
    const text = await _loadPublicText(path);
    const data = JSON.parse(text);
    function trimStrings<T>(obj: T): T {
        if (typeof obj === "string") {
            return obj.trim() as unknown as T;
        }
        if (Array.isArray(obj)) {
            return obj.map(item => trimStrings(item)) as unknown as T;
        }
        if (obj && typeof obj === "object") {
            const res: any = {};
            for (const [k, v] of Object.entries(obj as any)) {
                res[k] = trimStrings(v as any);
            }
            return res;
        }
        return obj;
    }
    return trimStrings(data);
}

async function _loadPublicYAML(path: string) {
    const text = await _loadPublicText(path);
    return parseYaml(text, { uniqueKeys: false });
}

export const loadPublicJSON = useMemoize(async (path: string): Promise<Record<string, any>> => _loadPublicJSON(path));
export const loadPublicYAML = useMemoize(async (path: string): Promise<Record<string, any>> => _loadPublicYAML(path));