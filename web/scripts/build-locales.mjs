import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import process from "process";

const localizeRules = JSON.parse(fs.readFileSync("./lit-localize.json", "utf-8"));

function compareXlfAndSrc(loc) {
    const xlf = path.join("./xliff", `${loc}.xlf`);
    const src = path.join("./src/locales", `${loc}.ts`);

    // Returns false if: the expected XLF file doesn't exist, The expected
    // generated file doesn't exist, or the XLF file is newer (has a higher date)
    // than the generated file.  The missing XLF file is important enough it
    // generates a unique error message and halts the build.

    try {
        var xlfStat = fs.statSync(xlf);
    } catch (_error) {
        console.error(`lit-localize expected '${loc}.xlf', but XLF file is not present`);
        process.exit(1);
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
    return true;
}

// For all the expected files, find out if any aren't up-to-date.

const upToDate = localizeRules.targetLocales.reduce(
    (acc, loc) => acc && compareXlfAndSrc(loc),
    true,
);

if (!upToDate) {
    const status = spawnSync("npm", ["run", "build-locales:build"], { encoding: "utf8" });

    // Count all the missing message warnings
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
