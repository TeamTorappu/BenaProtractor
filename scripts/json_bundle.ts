import fs from "fs";
import path from "path";
import pino from "pino";
const logger = pino({
    transport: {
        target: "pino-pretty",
        options: {
            colorize: true,
        },
    },
});

interface CopyTask {
    from: string;
    to: string;
}

async function copyFile(from: string, to: string) {
    const toDir = path.dirname(to);
    if (!fs.existsSync(toDir)) {
        fs.mkdirSync(toDir, { recursive: true });
    }
    fs.copyFileSync(from, to);
    logger.info(`✓ Copied: ${from} -> ${to}`);
}

async function jsonBundle(tasks: CopyTask[]) {
    logger.info(`Start: ${tasks.length} files`);

    for (const task of tasks) {
        try {
            await copyFile(task.from, task.to);
        } catch (error) {
            logger.error(`✗ Failed to copy ${task.from}`);
            logger.error(error);
            throw error;
        }
    }

    logger.info("✓ JSON bundle completed");
}

const tasks: CopyTask[] = [
    {
        from: "ArknightsGameData/zh_CN/gamedata/battle/buff_template_data.json",
        to: "public/gamedata/battle/buff_template_data.json",
    },
    {
        from: "ArknightsGameData/zh_CN/gamedata/excel/character_table.json",
        to: "public/gamedata/excel/character_table.json",
    },
    {
        from: "ArknightsGameData/zh_CN/gamedata/excel/roguelike_topic_table.json",
        to: "public/gamedata/excel/roguelike_topic_table.json",
    },
];

jsonBundle(tasks).catch((error) => logger.error(error));
