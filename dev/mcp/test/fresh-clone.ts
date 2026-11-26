#!/usr/bin/env node
/**
 * @file Fresh-clone test for setup mode: a git worktree of HEAD has no node_modules and no Python
 *   environment, like a new clone. Two runs, each driving `main.ts serve` over raw JSON-RPC:
 *
 *   1. The person installs in a terminal: the server notices and hands over.
 *   2. The agent calls akdev_install with a progress token: each make target is reported, the call
 *      answers when the install ends, and the server hands over. Both must end with
 *      `notifications/tools/list_changed` and the real tools answering, with no restart. A stand-in
 *      `make` runs the real `node-install`, which is all the server needs, and skips `web-install`
 *      and `core-install`, the slow ones. Tests HEAD: commit first. Run with `node
 *      dev/mcp/test/fresh-clone.ts`.
 */

import { execFileSync, spawn } from "node:child_process";
import { chmodSync, existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, join } from "node:path";
import { createInterface } from "node:readline";

import { GIT_ENV, ROOT } from "#dev/lib/git";

interface Message {
    id?: number;
    method?: string;
    params?: Record<string, unknown>;
    result?: Record<string, unknown>;
    error?: unknown;
}

const HANDOVER_TIMEOUT_MS = 300_000;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function assert(condition: unknown, message: string): asserts condition {
    if (!condition) throw new Error(`FAILED: ${message}`);
}

const git = (...args: string[]) =>
    execFileSync("git", args, { cwd: ROOT, env: { ...process.env, ...GIT_ENV }, stdio: "ignore" });

/** A `make` that runs the real `node-install` and stands in for the slow targets. */
function fakeMake(dir: string): string {
    const bin = join(dir, "bin");
    const make = join(bin, "make");
    const real = execFileSync("which", ["make"], { encoding: "utf8" }).trim();

    execFileSync("mkdir", ["-p", bin]);

    writeFileSync(
        make,
        `#!/bin/sh
case "$1" in
    web-install|core-install) echo "fresh-clone test: skipping $1"; exit 0 ;;
esac
exec "${real}" "$@"
`,
    );

    chmodSync(make, 0o755);

    return bin;
}

class Session {
    private next = 1;
    private readonly waiting = new Map<number, (message: Message) => void>();
    public readonly notifications: Message[] = [];
    private readonly proc;

    constructor(cwd: string, path: string) {
        this.proc = spawn(process.execPath, ["dev/mcp/main.ts", "serve"], {
            cwd,
            env: { ...process.env, PATH: path },
            stdio: ["pipe", "pipe", "pipe"],
        });

        this.proc.stderr.on("data", (chunk: Buffer) => {
            process.stdout.write(`    [server] ${chunk.toString().trim()}\n`);
        });

        createInterface({ input: this.proc.stdout }).on("line", (line) => {
            const message = JSON.parse(line) as Message;
            const resolve = message.id === undefined ? undefined : this.waiting.get(message.id);

            if (resolve) {
                this.waiting.delete(message.id!);
                resolve(message);

                return;
            }

            if (message.method) this.notifications.push(message);
        });
    }

    public send(message: object): void {
        this.proc.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", ...message })}\n`);
    }

    public call(method: string, params: object = {}): Promise<Message> {
        const id = this.next++;

        return new Promise((resolve) => {
            this.waiting.set(id, resolve);
            this.send({ id, method, params });
        });
    }

    public async tools(): Promise<string[]> {
        const reply = await this.call("tools/list");

        const tools = (reply.result?.tools ?? []) as { name: string }[];

        return tools.map((tool) => tool.name);
    }

    public async text(name: string, args: object = {}, meta?: object): Promise<string> {
        const reply = await this.call("tools/call", { name, arguments: args, _meta: meta });
        const content = reply.result?.content as { text: string }[] | undefined;

        return content?.[0]?.text ?? JSON.stringify(reply.error);
    }

    public async listChanged(): Promise<number> {
        const started = Date.now();

        while (Date.now() - started < HANDOVER_TIMEOUT_MS) {
            if (this.notifications.some((n) => n.method === "notifications/tools/list_changed")) {
                return Math.round((Date.now() - started) / 1000);
            }

            await sleep(250);
        }

        throw new Error(`FAILED: no tools/list_changed within ${HANDOVER_TIMEOUT_MS / 1000}s`);
    }

    public async close(): Promise<void> {
        this.proc.stdin.end();
        await sleep(500);
        this.proc.kill();
    }
}

async function connect(cwd: string, path: string): Promise<Session> {
    const session = new Session(cwd, path);

    const init = await session.call("initialize", {
        protocolVersion: "2025-11-25",
        capabilities: {},
        clientInfo: { name: "fresh-clone-test", version: "0" },
    });

    const instructions = String(init.result?.instructions ?? "");

    assert(instructions.includes("setup mode"), "the server starts in setup mode");
    session.send({ method: "notifications/initialized" });

    const tools = await session.tools();

    assert(
        tools.join() === "akdev_status,akdev_install",
        `setup mode offers status and install, got ${tools}`,
    );

    return session;
}

async function handedOver(session: Session): Promise<string> {
    const seconds = await session.listChanged();
    const tools = await session.tools();

    assert(tools.includes("akdev_lint"), `the real tools appear, got ${tools}`);

    const skill = await session.text("akdev_skill", { name: "testing" });

    assert(skill.includes("name: testing"), "a real tool answers after the handover");

    return `handed over ${seconds}s after the install, tools: ${tools.join(", ")}`;
}

async function installedInTerminal(cwd: string, path: string): Promise<string> {
    const session = await connect(cwd, path);

    try {
        execFileSync("pnpm", ["install", "--frozen-lockfile"], {
            cwd,
            env: { ...process.env, PATH: path },
            stdio: "ignore",
        });

        return await handedOver(session);
    } finally {
        await session.close();
    }
}

async function installedByAgent(cwd: string, path: string): Promise<string> {
    const session = await connect(cwd, path);

    try {
        const answer = await session.text("akdev_install", {}, { progressToken: "install" });

        const progress = session.notifications
            .filter((n) => n.method === "notifications/progress")
            .map((n) => String(n.params?.message));

        assert(answer.includes("make install: done"), `the install finishes, got: ${answer}`);

        assert(
            progress.some((m) => m.includes("node-install")),
            `progress names each make target, got ${progress.join(" | ")}`,
        );

        return `${progress.length} progress updates (${progress.join(" | ")}); ${await handedOver(session)}`;
    } finally {
        await session.close();
    }
}

const scratch = mkdtempSync(join(tmpdir(), "akdev-fresh-clone-"));
const worktree = join(scratch, "authentik");
const path = [fakeMake(scratch), process.env.PATH].join(delimiter);

git("worktree", "add", "--detach", worktree, "HEAD");

try {
    assert(!existsSync(join(worktree, "node_modules")), "the worktree starts without node_modules");

    console.log("1. installed in a terminal");
    console.log(`   ok: ${await installedInTerminal(worktree, path)}`);

    rmSync(join(worktree, "node_modules"), { recursive: true, force: true });

    console.log("2. installed by the agent with akdev_install");
    console.log(`   ok: ${await installedByAgent(worktree, path)}`);
} finally {
    git("worktree", "remove", "--force", worktree);
    rmSync(scratch, { recursive: true, force: true });
}
