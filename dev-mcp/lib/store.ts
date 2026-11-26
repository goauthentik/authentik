/**
 * @file Results written under the git directory, so hooks and make wrappers can read them.
 *   Hooks run as separate processes, and a make wrapper run by hand has no server, so results can't
 *   live only in the server's memory. Each result carries the tree fingerprint it was computed
 *   against; a result whose fingerprint doesn't match the current tree counts as missing.
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { fingerprint, gitDir } from "#dev-mcp/repo";
import type { Result, ResultData } from "#dev-mcp/result";

export function storeDir(...sub: string[]): string {
    const dir = join(gitDir(), "akdev", ...sub);
    mkdirSync(dir, { recursive: true });
    return dir;
}

export function save(name: string, result: Result): void {
    result.fingerprint ??= fingerprint();
    writeFileSync(join(storeDir("results"), `${name}.json`), JSON.stringify(result, null, 2));
}

export function load(name: string): ResultData | null {
    try {
        return JSON.parse(readFileSync(join(storeDir("results"), `${name}.json`), "utf8"));
    } catch {
        return null;
    }
}

export function loadCurrent(name: string): ResultData | null {
    const data = load(name);
    return data && data.fingerprint === fingerprint() ? data : null;
}
