/**
 * @file Persist check results under the Git directory for hooks and command-line wrappers.
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { fingerprint, gitDir } from "#dev-mcp/core/repo";
import type { Result, ResultData } from "#dev-mcp/results/result";

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
