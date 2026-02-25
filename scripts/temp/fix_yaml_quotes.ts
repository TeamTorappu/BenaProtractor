/**
 * 临时脚本：修复 action_subschema/*.yml 中
 * 双引号括起来的 value 里面内部引号没有转义的问题。
 *
 * 例如:  value: "{"r":1,"g":1}"
 * 修复为: value: "{\"r\":1,\"g\":1}"
 *
 * 用法: tsx scripts/fix_yaml_quotes.ts
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const TARGET_DIRS = [
    path.join(__dirname, "../public/buff/mappings/action_subschema"),
    path.join(__dirname, "../public/buff/mappings/actions"),
    path.join(__dirname, "../public/buff/mappings"),
    path.join(__dirname, "../public/rogue/mappings"),
];

function walkYml(dir: string): string[] {
    const result: string[] = [];
    if (!fs.existsSync(dir)) return result;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            result.push(...walkYml(full));
        } else if (entry.name.endsWith(".yml")) {
            result.push(full);
        }
    }
    return result;
}

/**
 * 修复一行中 `key: "..."` 里内部未转义的双引号。
 *
 * 策略：找到 `: "` 后的首个引号和行尾的末个引号，
 * 把中间所有 `"` 转义为 `\"`（已有 `\"` 的不重复处理）。
 */
function fixLine(line: string): string {
    // 匹配 `key: "..."` 格式，其中 value 部分可能含未转义引号
    const m = line.match(/^(\s*\S+:\s*)"(.*)"(\s*)$/);
    if (!m) return line;

    const [, prefix, content, suffix] = m;

    // 如果 content 里没有任何 " 就不需要修复
    if (!content.includes('"')) return line;

    // 先把已正确转义的 \" 保护起来
    const placeholder = "\x00";
    const protected_ = content.replace(/\\"/g, placeholder);

    // 转义剩余的裸引号
    const escaped = protected_.replace(/"/g, '\\"');

    // 恢复 placeholder
    const final = escaped.replace(new RegExp(placeholder, "g"), '\\"');

    return `${prefix}"${final}"${suffix}`;
}

let fixed = 0;
let unchanged = 0;

for (const dir of TARGET_DIRS) {
    const files = walkYml(dir);
    for (const file of files) {
        const original = fs.readFileSync(file, "utf-8");
        const lines = original.split("\n");
        const newLines = lines.map(fixLine);
        const result = newLines.join("\n");

        if (result !== original) {
            fs.writeFileSync(file, result, "utf-8");
            fixed++;
            const rel = path.relative(path.join(__dirname, "generated"), file);
            console.log(`  ✓ ${rel}`);
        } else {
            unchanged++;
        }
    }
}

console.log(`\n修复完成: ${fixed} 个文件已修复, ${unchanged} 个无需修改`);
