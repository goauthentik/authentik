import { execSync } from "node:child_process";
import * as path from "node:path";

const projectRoot = execSync("git rev-parse --show-toplevel", { encoding: "utf8" }).replace(
    "\n",
    "",
);
const cmd = [
    "codespell -D -",
    `-D ${path.join(projectRoot, ".github/codespell-dictionary.txt")}`,
    `-I ${path.join(projectRoot, ".github/codespell-words.txt")}`,
    "-S './src/locales/**' ./src -s",
].join(" ");

console.log(execSync(cmd, { encoding: "utf8" }));
