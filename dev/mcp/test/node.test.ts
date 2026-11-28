import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, join } from "node:path";

import { chooseNode, describeNode, nodeBinary, withNode } from "#dev-mcp/environment/node";

import { afterEach, describe, expect, it } from "vitest";

const RANGE = "^24.22.3 || >=26.13.1";
const dirs: string[] = [];

/** A fake `$NVM_DIR` with these versions installed. */
function fakeNvm(versions: string[], { script = true } = {}): string {
    const dir = mkdtempSync(join(tmpdir(), "akdev-nvm-"));
    dirs.push(dir);

    if (script) writeFileSync(join(dir, "nvm.sh"), "");

    for (const version of versions) {
        const bin = join(dir, "versions", "node", `v${version}`, "bin");
        mkdirSync(bin, { recursive: true });
        writeFileSync(join(bin, "node"), "");
    }

    return dir;
}

afterEach(() => {
    for (const dir of dirs.splice(0)) rmSync(dir, { recursive: true, force: true });
});

describe("node choice", () => {
    it("keeps a Node that fits", () => {
        const choice = chooseNode({ current: "26.13.1", range: RANGE, nvmDir: fakeNvm([]) });

        expect(choice.ok).toBe(true);
        expect(withNode({ PATH: "/usr/bin" }, choice).PATH).toBe("/usr/bin");
        expect(nodeBinary(choice)).toBe(process.execPath);
    });

    it("keeps any Node when package.json sets no range", () => {
        expect(chooseNode({ current: "18.0.0", range: null }).ok).toBe(true);
    });

    it("switches to the newest nvm version that fits", () => {
        const nvmDir = fakeNvm(["22.22.3", "24.16.0", "24.22.3", "24.23.0", "26.2.0"]);
        const choice = chooseNode({ current: "26.2.0", range: RANGE, nvmDir });

        expect(choice.ok).toBe(false);
        expect(choice.switchTo?.version).toBe("24.23.0");

        const bin = join(nvmDir, "versions", "node", "v24.23.0", "bin");

        expect(withNode({ PATH: "/usr/bin" }, choice).PATH).toBe(`${bin}${delimiter}/usr/bin`);
        expect(nodeBinary(choice)).toBe(join(bin, "node"));
        expect(describeNode(choice)).toContain("nvm use 24.23.0");
    });

    it("ignores version folders without a node binary", () => {
        const nvmDir = fakeNvm(["24.16.0"]);
        mkdirSync(join(nvmDir, "versions", "node", "v26.20.0", "bin"), { recursive: true });

        expect(chooseNode({ current: "26.2.0", range: RANGE, nvmDir }).switchTo).toBeNull();
    });

    it("suggests nvm install when nothing installed fits", () => {
        const choice = chooseNode({
            current: "26.2.0",
            range: RANGE,
            nvmDir: fakeNvm(["24.16.0"]),
        });

        expect(choice.switchTo).toBeNull();
        expect(choice.hint).toContain("nvm install 26");
    });

    it("says to install Node when there's no nvm", () => {
        const nvmDir = fakeNvm([], { script: false });
        const choice = chooseNode({ current: "26.2.0", range: RANGE, nvmDir });

        expect(choice.hint).toBe(
            `Install a Node.js that fits ${RANGE}, then start the server again.`,
        );
    });
});
