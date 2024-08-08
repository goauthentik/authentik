import { execFileSync } from "child_process";
import { ESLint } from "eslint";
import fs from "fs";
import path from "path";
import process from "process";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const projectRoot = path.join(__dirname, "..");
process.chdir(projectRoot);

function changedFiles() {
    const gitStatus = execFileSync("git", ["diff", "--name-only", "HEAD"], { encoding: "utf8" });
    const gitUntracked = execFileSync("git", ["ls-files", "--others", "--exclude-standard"], {
        encoding: "utf8",
    });

    const changed = gitStatus
        .split("\n")
        .filter((line) => line.trim().substring(0, 4) === "web/")
        .filter((line) => /\.(m|c)?(t|j)s$/.test(line))
        .map((line) => line.substring(4))
        .filter((line) => fs.existsSync(line));

    const untracked = gitUntracked
        .split("\n")
        .filter((line) => /\.(m|c)?(t|j)s$/.test(line))
        .filter((line) => fs.existsSync(line));

    const sourceFiles = [...changed, ...untracked].filter((line) => /^src\//.test(line));
    const scriptFiles = [...changed, ...untracked].filter(
        (line) => /^scripts\//.test(line) || !/^src\//.test(line),
    );

    return [...sourceFiles, ...scriptFiles];
}

const hasFlag = (flags) => process.argv.length > 1 && flags.includes(process.argv[2]);

const [configFile, files] = hasFlag(["-n", "--nightmare"])
    ? [path.join(__dirname, "eslint.nightmare.mjs"), changedFiles()]
    : hasFlag(["-p", "--precommit"])
      ? [path.join(__dirname, "eslint.precommit.mjs"), changedFiles()]
      : [path.join(projectRoot, "eslint.config.mjs"), ["."]];

const eslint = new ESLint({
    overrideConfigFile: configFile,
    warnIgnored: false,
});

const results = await eslint.lintFiles(files);
const formatter = await eslint.loadFormatter("stylish");
const resultText = formatter.format(results);
const errors = results.reduce((acc, result) => acc + result.errorCount, 0);
console.log(resultText);
process.exit(errors > 1 ? 1 : 0);
