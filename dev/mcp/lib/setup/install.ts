/**
 * @file `make install` for setup mode, one prerequisite target at a time so each can be reported.
 */

import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { chooseNode, describeNode, withNode } from "#dev-mcp/environment/node";
import { type Progress, noProgress } from "#dev-mcp/results/progress";
import { GIT_ENV, ROOT } from "#dev/lib/git";
import { INSTALL_HINT, isLinked } from "#dev/lib/optional";

/**
 * What the real server needs to start. The rest degrades on its own.
 */
const REQUIRED = ["@modelcontextprotocol/server", "zod"];
const TARGET_TIMEOUT_MS = 30 * 60_000;
const OUTPUT_LIMIT = 4000;

export interface Install {
    state: "running" | "done" | "failed";
    started: number;
    finished: number | null;
    output: string;
    exit: number | null;
    /**
     * The make target running now, or the one that failed.
     */
    step: string | null;
}

/**
 * Required packages that aren't linked yet. Read from disk on every call: in-process module
 * resolution can stay stale after an install.
 */
export function missingPackages(): string[] {
    return REQUIRED.filter((pkg) => !isLinked(pkg));
}

/**
 * `install`'s prerequisites in the Makefile. Falls back to `install` itself when it has a recipe
 * of its own or the Makefile can't be read.
 */
export function installTargets(makefile = readMakefile()): string[] {
    const match = /^install:([^#\n]*)(?:#[^\n]*)?\n(\t)?/m.exec(makefile);

    if (!match || match[2]) return ["install"];

    const targets = match[1]!.trim().split(/\s+/).filter(Boolean);

    return targets.length ? targets : ["install"];
}

function readMakefile(): string {
    try {
        return readFileSync(join(ROOT, "Makefile"), "utf8");
    } catch {
        return "";
    }
}

export class Installer {
    public current: Install | null = null;

    public get running(): boolean {
        return this.current?.state === "running";
    }

    /**
     * The missing packages, the active Node, and the install's progress.
     */
    public status(): string {
        const lines = [
            `Missing: ${missingPackages().join(", ") || "nothing"}.`,
            describeNode(chooseNode()),
        ];

        const install = this.current;

        if (!install) {
            lines.push(`No install started. Call akdev_install, or: ${INSTALL_HINT}`);

            return lines.join("\n");
        }

        const seconds = Math.round(((install.finished ?? Date.now()) - install.started) / 1000);
        const step = install.step ? ` (${install.step})` : "";

        lines.push(`make install: ${install.state}${step} after ${seconds}s.`);

        if (install.state !== "running") lines.push(`Output (last lines):\n${install.output}`);

        return lines.join("\n");
    }

    /**
     * Start the install. `update` hears each target start; `done` runs when the install ends.
     * Returns what to tell the agent, and whether an install started.
     */
    public start(
        update: Progress = noProgress,
        done: () => void = () => {},
    ): { message: string; started: boolean } {
        if (this.running) return { message: "make install is already running.", started: false };

        const node = chooseNode();

        // `make install` would stop at node-preinstall. Say why now instead.
        if (!node.ok && !node.switchTo) {
            return { message: `Not started. ${describeNode(node)}`, started: false };
        }

        const targets = installTargets();

        const install: Install = {
            state: "running",
            started: Date.now(),
            finished: null,
            output: "",
            exit: null,
            step: null,
        };

        this.current = install;

        const keep = (chunk: Buffer) => {
            install.output = (install.output + chunk.toString()).slice(-OUTPUT_LIMIT);
        };

        const finish = (code: number | null) => {
            install.exit = code;
            install.state = code === 0 ? "done" : "failed";
            install.finished = Date.now();

            const failed = code === 0 ? "" : `make ${install.step ?? "install"} failed`;

            update(targets.length, targets.length, failed || "installed");
            done();
        };

        const next = (index: number) => {
            if (index === targets.length) return finish(0);

            const target = targets[index]!;

            install.step = target;
            update(index, targets.length, `make ${target} (${index + 1} of ${targets.length})`);

            const proc = spawn("make", [target], {
                cwd: ROOT,
                env: withNode({ ...process.env, ...GIT_ENV }, node),
                stdio: ["ignore", "pipe", "pipe"],
            });

            const timer = setTimeout(() => proc.kill("SIGTERM"), TARGET_TIMEOUT_MS);

            proc.stdout.on("data", keep);
            proc.stderr.on("data", keep);

            proc.on("error", (error) => {
                install.output += `\n${error.message}`;
            });

            proc.on("close", (code) => {
                clearTimeout(timer);

                if (code === 0) return next(index + 1);

                finish(code);
            });
        };

        next(0);

        const using = node.switchTo ? ` with nvm's Node ${node.switchTo.version}` : "";

        return {
            message: `Started \`make install\`${using}. Poll akdev_status; the full tools appear when it's done.`,
            started: true,
        };
    }
}
