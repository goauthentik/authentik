/**
 * @file Git plumbing for the scripts and the dev MCP server, without user or system configuration.
 *   Node built-ins only: the MCP server's setup mode imports this before `pnpm install`, and
 *   nothing here may write to stdout.
 */

import { execFile, execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { statSync } from "node:fs";
import { join, resolve } from "node:path";
import { promisify } from "node:util";

/** dev/lib/ → the repo root. */
export const ROOT = resolve(import.meta.dirname, "..", "..");
export const DEFAULT_BASE = "origin/main";

/**
 * Plumbing needs no user config, and an unreadable global config is fatal to git.
 */
export const GIT_ENV = { GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" };

/**
 * Run a git command in the repo root, optionally checking for errors.
 */
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

/**
 * The per-worktree git directory, so each worktree keeps its own results.
 */
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
 * HEAD and metadata for dirty files, used to detect changes without hashing the full tree.
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

const execFileAsync = promisify(execFile);

/**
 * Whether `filePath` has uncommitted changes. `available` is false when git couldn't run.
 */
export async function gitStatus(
    filePath: string,
    cwd = process.cwd(),
): Promise<{ clean: boolean; available: boolean }> {
    return execFileAsync("git", ["status", "--porcelain", filePath], {
        cwd,
        env: { ...process.env, ...GIT_ENV },
    })
        .then(({ stdout }) => ({ clean: !stdout.trim(), available: true }))
        .catch(() => ({ clean: false, available: false }));
}

/**
 * The root of the git repository containing `cwd`.
 *
 * @throws {Error} If git fails, such as outside a repository.
 */
export async function resolveRepoRoot(cwd = process.cwd()): Promise<string> {
    const { stdout } = await execFileAsync("git", ["rev-parse", "--show-toplevel"], {
        cwd,
        env: { ...process.env, ...GIT_ENV },
    });

    return stdout.trim();
}
