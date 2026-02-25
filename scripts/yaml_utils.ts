/**
 * 共享的 YAML 序列化工具。
 * 与生成器脚本产出的格式完全一致。
 */

function yamlString(str: string): string {
    if (
        str === "" ||
        /[[\]:#",\n]/.test(str) ||
        str.startsWith(" ") ||
        str.endsWith(" ") ||
        str.includes("  ") ||
        (str.includes("-") && str.trim() === "-")
        || str.includes("{") || str.includes("[") || str.includes("(")
    ) {
        return '"' + str.replace(/"/g, '\\"') + '"';
    }
    return str;
}

export function toYaml(obj: any, indent = 0): string {
    const spaces = " ".repeat(indent);

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
