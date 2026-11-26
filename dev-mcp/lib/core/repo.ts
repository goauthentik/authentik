/**
 * @file Git helpers: repo root, changed files, and the tree fingerprint.
 */

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { statSync } from "node:fs";
import { join, resolve } from "node:path";

/** dev-mcp/lib/core/ → the repo root. */
export const ROOT = resolve(import.meta.dirname, "..", "..", "..");
export const DEFAULT_BASE = "origin/main";

/** Plumbing needs no user config, and an unreadable global config is fatal to git. */
export const GIT_ENV = { GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" };

export function git(args: string[], check = true): string {
    try {
        return execFileSync("git", args, {
            cwd: ROOT,
            encoding: "utf8",
            env: { ...process.env, ...GIT_ENV },
            stdio: ["ignore", "pipe", "pipe"],
            timeout: 30_000,
        }).trim();
    } catch (error) {
        if (check) throw error;
        return "";
    }
}

/** The per-worktree git directory, so each worktree keeps its own results. */
export function gitDir(): string {
    return git(["rev-parse", "--absolute-git-dir"]);
}

export const head = () => git(["rev-parse", "--short", "HEAD"]);
export const branch = () => git(["rev-parse", "--abbrev-ref", "HEAD"], false) || null;
export const mergeBase = (base = DEFAULT_BASE) => git(["merge-base", "HEAD", base], false) || null;

/** Files changed since the merge base with `base`: committed, staged, unstaged and untracked. */
export function changedFiles(base = DEFAULT_BASE): string[] {
    const files = new Set<string>();
    const mb = mergeBase(base);
    for (const f of git(["diff", "--name-only", mb ?? "HEAD"]).split("\n")) files.add(f);
    for (const f of git(["ls-files", "--others", "--exclude-standard"]).split("\n")) files.add(f);
    files.delete("");
    return [...files].sort();
}

export function changedSinceBase(path: string, base = DEFAULT_BASE): boolean {
    const prefix = `${path.replace(/\/$/, "")}/`;
    return changedFiles(base).some((f) => f === path || f.startsWith(prefix));
}

/**
 * HEAD, the dirty file list, and each dirty file's mtime and size.
 *
 * Hashing every file on each call would cost more than it saves, so only dirty files are stat'ed.
 */
export function fingerprint(...paths: string[]): string {
    const status = git(["status", "--porcelain", "--untracked-files=all", "--", ...paths]);
    const hash = createHash("sha256")
        .update(git(["rev-parse", "HEAD"]))
        .update(status);
    for (const line of status.split("\n")) {
        if (!line) continue;
        const name = line.slice(3).split(" -> ").at(-1)!.replace(/^"|"$/g, "");
        try {
            const st = statSync(join(ROOT, name));
            hash.update(`${name}:${st.mtimeMs}:${st.size}`);
        } catch {
            // Deleted files are covered by the status text.
        }
    }
    return hash.digest("hex").slice(0, 16);
}
