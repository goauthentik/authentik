import { execSync } from "child_process";
import path from "path";

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

// eslint-disable-next-line no-console
console.log(execSync(cmd, { encoding: "utf8" }));
