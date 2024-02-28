import { execSync } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
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
