import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";

const localizeRules = JSON.parse(fs.readFileSync("./lit-localize.json", "utf-8"));

const complete = localizeRules.targetLocales.reduce(function (acc, loc) {
    if (!acc) {
        return acc;
    }

    const xlf = path.join("./xliff", `${loc}.xlf`);
    const src = path.join("./src/locales", `${loc}.ts`);

    try {
        var xlfStat = fs.statSync(xlf);
    } catch (_error) {
        return false;
    }

    try {
        var srcStat = fs.statSync(src);
    } catch (_error) {
        return false;
    }

    // if the xlf is newer (greater) than src, it's out of date.
    if (xlfStat.mtimeMs > srcStat.mtimeMs) {
        return false;
    }
    return acc;
}, true);

if (!complete) {
    const status = spawnSync("npm", ["run", "build-locales:build"], { encoding: "utf8" });
    const counts = status.stderr.split("\n").reduce((acc, line) => {
        const match = /^([\w-]+) message/.exec(line);
        if (!match) {
            return acc;
        }
        acc.set(match[1], (acc.get(match[1]) || 0) + 1);
        return acc;
    }, new Map());

    const locales = Array.from(counts.keys());
    locales.sort();
    const report = locales
        .map((locale) => `Locale '${locale}' has ${counts.get(locale)} missing translations`)
        .join("\n");

    console.log(`Translation tables rebuilt.\n${report}\n`);
}

console.log("Locale ./src is up-to-date");
