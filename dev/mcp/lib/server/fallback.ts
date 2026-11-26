/**
 * @file Minimal MCP server used until project dependencies are installed.
 */

import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createInterface } from "node:readline";
import type { Writable } from "node:stream";

import { chooseNode, describeNode, nodeBinary, withNode } from "#dev-mcp/environment/node";
import { type Progress, noProgress } from "#dev-mcp/results/progress";
import { GIT_ENV, ROOT } from "#dev/lib/git";
import { INSTALL_HINT, isLinked } from "#dev/lib/optional";

/** What the real server needs to start; the rest degrades on its own. */
const REQUIRED = ["@modelcontextprotocol/server", "zod"];
const POLL_MS = 3_000;
const INSTALL_TIMEOUT_MS = 30 * 60_000;
const HANDOVER_ID = "akdev-handover";

/** Protocol versions answered with `initialize`; the SDK's list, newest first. */
const VERSIONS = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05", "2024-10-07"];

/** Set for the real server's process, so a still-broken install can't start another fallback. */
export const NO_FALLBACK = "AKDEV_NO_FALLBACK";

/** The first 512 characters carry the rules: Codex only guarantees that much. */
export const FALLBACK_INSTRUCTIONS = `\
authentik-dev is in setup mode: this clone's dependencies aren't installed, so its checks aren't \
available yet. Tell the person, and ask whether to install them now. If they agree, call \
akdev_install: it runs \`make install\` (Node and Python packages, several minutes, network \
access). When the dependencies are in place, this server switches to its full tool set by itself, \
with no restart. akdev_status shows progress.
`;

type Message = {
    jsonrpc: "2.0";
    id?: string | number;
    method?: string;
    params?: Record<string, unknown>;
};

const TOOLS = [
    {
        name: "akdev_status",
        description:
            "Setup status of the authentik dev server: which dependencies are missing, and the " +
            "progress of an install started with akdev_install.",
        inputSchema: { type: "object", properties: {} },
        annotations: { readOnlyHint: true, destructiveHint: false, openWorldHint: false },
    },
    {
        name: "akdev_install",
        description:
            "Install authentik's development dependencies with `make install` (Node and Python " +
            "packages; takes several minutes and downloads from the network). When the active " +
            "Node doesn't fit package.json, it uses an nvm-installed one that does. Ask the " +
            "person before calling it. With a progress token, the call reports each make target " +
            "and answers when the install ends; otherwise it returns at once, and akdev_status " +
            "shows progress. When it finishes, the full authentik-dev tools appear without a " +
            "restart.",
        inputSchema: { type: "object", properties: {} },
        annotations: { readOnlyHint: false, destructiveHint: false, openWorldHint: true },
        // Claude Code asks the person every time, whatever their allow rules say.
        _meta: { "anthropic/requiresUserInteraction": true },
    },
];

interface Install {
    state: "running" | "done" | "failed";
    started: number;
    finished: number | null;
    output: string;
    exit: number | null;
    /** The make target running now, or the one that failed. */
    step: string | null;
}

/**
 * `install`'s prerequisites in the Makefile, run one at a time so each can be reported. Falls
 * back to `install` itself when it has a recipe of its own or can't be read.
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

export function serveFallback(): void {
    let initialize: Message["params"] | null = null;
    let mode: "setup" | "handover" | "proxy" = "setup";
    /** The real server's stdin, once it has taken over. */
    let child: Writable | null = null;
    let install: Install | null = null;
    const pending: string[] = [];

    function send(message: object): void {
        process.stdout.write(`${JSON.stringify(message)}\n`);
    }

    function result(id: Message["id"], value: object): void {
        send({ jsonrpc: "2.0", id, result: value });
    }

    function text(id: Message["id"], body: string, isError = false): void {
        result(id, { content: [{ type: "text", text: body }], isError });
    }

    // Read from disk each time: in-process resolution can stay stale after the install.
    const missing = () => REQUIRED.filter((pkg) => !isLinked(pkg));

    function status(): string {
        const lines = [
            `Missing: ${missing().join(", ") || "nothing"}.`,
            describeNode(chooseNode()),
        ];

        if (!install) {
            lines.push(`No install started. Call akdev_install, or: ${INSTALL_HINT}`);
        } else {
            const seconds = Math.round(((install.finished ?? Date.now()) - install.started) / 1000);

            const step = install.step ? ` (${install.step})` : "";

            lines.push(`make install: ${install.state}${step} after ${seconds}s.`);

            if (install.state !== "running") lines.push(`Output (last lines):\n${install.output}`);
        }

        return lines.join("\n");
    }

    /**
     * Run `install`'s prerequisites one at a time, calling `update` as each starts and `done`
     * when the install finishes, before any handover to the real server.
     */
    function startInstall(update: Progress = noProgress, done: () => void = () => {}): string {
        if (install?.state === "running") return "make install is already running.";

        const node = chooseNode();

        // `make install` would stop at node-preinstall; say why now instead.
        if (!node.ok && !node.switchTo) return `Not started. ${describeNode(node)}`;

        const targets = installTargets();

        const started: Install = {
            state: "running",
            started: Date.now(),
            finished: null,
            output: "",
            exit: null,
            step: null,
        };

        const keep = (chunk: Buffer) => {
            started.output = (started.output + chunk.toString()).slice(-4000);
        };

        function finish(code: number | null): void {
            started.exit = code;
            started.state = code === 0 ? "done" : "failed";
            started.finished = Date.now();

            const failed = code === 0 ? "" : `make ${started.step ?? "install"} failed`;
            update(targets.length, targets.length, failed || "installed");
            done();
            check();
        }

        function next(index: number): void {
            if (index === targets.length) return finish(0);

            const target = targets[index]!;
            started.step = target;
            update(index, targets.length, `make ${target} (${index + 1} of ${targets.length})`);

            const proc = spawn("make", [target], {
                cwd: ROOT,
                env: withNode({ ...process.env, ...GIT_ENV }, node),
                stdio: ["ignore", "pipe", "pipe"],
            });

            const timer = setTimeout(() => proc.kill("SIGTERM"), INSTALL_TIMEOUT_MS);

            proc.stdout.on("data", keep);
            proc.stderr.on("data", keep);

            proc.on("error", (error) => {
                started.output += `\n${error.message}`;
            });

            proc.on("close", (code) => {
                clearTimeout(timer);

                if (code === 0) return next(index + 1);

                finish(code);
            });
        }

        install = started;
        next(0);

        const using = node.switchTo ? ` with nvm's Node ${node.switchTo.version}` : "";

        return `Started \`make install\`${using}. Poll akdev_status; the full tools appear when it's done.`;
    }

    /**
     * With a progress token, keep the call open: report each make target, and answer with the
     * status when the install ends. Without one, answer at once and let the agent poll.
     */
    function callInstall(id: Message["id"], params: Message["params"]): void {
        const meta = params?._meta as { progressToken?: string | number } | undefined;
        const token = meta?.progressToken;

        if (token === undefined || install?.state === "running") {
            return text(id, startInstall());
        }

        const update: Progress = (progress, total, message) =>
            send({
                jsonrpc: "2.0",
                method: "notifications/progress",
                params: { progressToken: token, progress, total, message },
            });

        const before = install;
        const reply = startInstall(update, () => text(id, status(), install?.state === "failed"));

        // Refused before starting (no new install): nothing will call back, so answer now.
        if (install === before) text(id, reply);
    }

    function handle(message: Message): void {
        const { id, method } = message;

        // Notifications, and responses to requests we never send, need no reply.
        if (id === undefined || !method) return;

        switch (method) {
            case "initialize": {
                initialize = message.params ?? {};

                const asked = String(initialize.protocolVersion ?? "");

                result(id, {
                    protocolVersion: VERSIONS.includes(asked) ? asked : VERSIONS[0],
                    capabilities: { tools: { listChanged: true } },
                    serverInfo: { name: "authentik-dev", version: "0.1.0" },
                    instructions: FALLBACK_INSTRUCTIONS,
                });

                return;
            }
            case "server/discover":
                result(id, {
                    supportedVersions: VERSIONS,
                    capabilities: { tools: { listChanged: true } },
                    instructions: FALLBACK_INSTRUCTIONS,
                });

                return;
            case "ping":
                result(id, {});

                return;
            case "tools/list":
                result(id, { tools: TOOLS });

                return;
            case "tools/call": {
                const name = String(message.params?.name ?? "");

                if (name === "akdev_status") return text(id, status());

                if (name === "akdev_install") return callInstall(id, message.params);

                return text(
                    id,
                    `Unknown tool ${name}. In setup mode: akdev_status, akdev_install.`,
                    true,
                );
            }
            default:
                send({
                    jsonrpc: "2.0",
                    id,
                    error: { code: -32601, message: `${method} isn't available in setup mode` },
                });
        }
    }

    /** Start the real server, replay the handshake, then pass every message through. */
    function handover(): void {
        mode = "handover";
        process.stderr.write("authentik-dev: dependencies found, starting the full server\n");

        // The real server's checks run make and pnpm, so they need the fitting Node too.
        const node = chooseNode();

        const proc = spawn(nodeBinary(node), [join(ROOT, "dev", "mcp", "main.ts"), "serve"], {
            cwd: ROOT,
            env: withNode({ ...process.env, [NO_FALLBACK]: "1" }, node),
            stdio: ["pipe", "pipe", "inherit"],
        });

        child = proc.stdin;
        proc.on("exit", (code) => process.exit(code ?? 1));

        function proxy(): void {
            mode = "proxy";

            for (const line of pending.splice(0)) proc.stdin.write(`${line}\n`);

            send({ jsonrpc: "2.0", method: "notifications/tools/list_changed" });
        }

        createInterface({ input: proc.stdout }).on("line", (line) => {
            if (mode === "proxy") return void process.stdout.write(`${line}\n`);

            // The real server's answer to the replayed handshake; the client already has one.
            const reply = JSON.parse(line) as Message;

            if (reply.id !== HANDOVER_ID) return;

            proc.stdin.write(
                `${JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" })}\n`,
            );

            proxy();
        });

        if (initialize) {
            proc.stdin.write(
                `${JSON.stringify({ jsonrpc: "2.0", id: HANDOVER_ID, method: "initialize", params: initialize })}\n`,
            );
        } else {
            // The stateless handshake (`server/discover`) has nothing to replay.
            proxy();
        }
    }

    function check(): void {
        if (mode !== "setup" || install?.state === "running" || missing().length) return;

        handover();
    }

    const poll = setInterval(check, POLL_MS);

    createInterface({ input: process.stdin })
        .on("line", (line) => {
            if (!line.trim()) return;

            if (mode === "proxy") return void child?.write(`${line}\n`);

            if (mode === "handover") return void pending.push(line);

            let message: Message;

            try {
                message = JSON.parse(line) as Message;
            } catch {
                return send({
                    jsonrpc: "2.0",
                    id: null,
                    error: { code: -32700, message: "Parse error" },
                });
            }

            handle(message);
        })
        .on("close", () => {
            clearInterval(poll);
            child?.end();

            if (!child) process.exit(0);
        });

    process.stderr.write(
        `authentik-dev: setup mode, missing ${missing().join(", ")}. ${describeNode(chooseNode())}\n`,
    );
}
