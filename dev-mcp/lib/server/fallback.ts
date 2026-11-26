/**
 * @file The setup-mode MCP server, for a clone whose dependencies aren't installed yet.
 *   Without the MCP SDK the real server can't start, and an MCP client only sees a closed
 *   connection. This speaks just enough of the protocol, with Node built-ins, to connect and say
 *   what's missing: its instructions and `akdev_status` explain, and `akdev_install` runs
 *   `make install` once the person approves. When the dependencies appear, from that tool or from
 *   a `make install` run anywhere, it starts the real server as a child, hands the session over,
 *   and tells the client its tool list changed. No restart.
 */

import { spawn } from "node:child_process";
import { join } from "node:path";
import { createInterface } from "node:readline";
import type { Writable } from "node:stream";

import { INSTALL_HINT, isInstalled } from "#dev-mcp/core/optional";
import { GIT_ENV, ROOT } from "#dev-mcp/core/repo";

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
            "packages; takes several minutes and downloads from the network). Ask the person " +
            "before calling it. Returns at once; poll akdev_status. When it finishes, the full " +
            "authentik-dev tools appear without a restart.",
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

    const missing = () => REQUIRED.filter((pkg) => !isInstalled(pkg));

    function status(): string {
        const lines = [`Missing: ${missing().join(", ") || "nothing"}.`];

        if (!install) {
            lines.push(`No install started. Call akdev_install, or: ${INSTALL_HINT}`);
        } else {
            const seconds = Math.round(((install.finished ?? Date.now()) - install.started) / 1000);

            lines.push(`make install: ${install.state} after ${seconds}s.`);

            if (install.state !== "running") lines.push(`Output (last lines):\n${install.output}`);
        }

        return lines.join("\n");
    }

    function startInstall(): string {
        if (install?.state === "running") return "make install is already running.";

        const started: Install = {
            state: "running",
            started: Date.now(),
            finished: null,
            output: "",
            exit: null,
        };

        const proc = spawn("make", ["install"], {
            cwd: ROOT,
            env: { ...process.env, ...GIT_ENV },
            stdio: ["ignore", "pipe", "pipe"],
        });

        const keep = (chunk: Buffer) => {
            started.output = (started.output + chunk.toString()).slice(-4000);
        };

        const timer = setTimeout(() => proc.kill("SIGTERM"), INSTALL_TIMEOUT_MS);

        proc.stdout.on("data", keep);
        proc.stderr.on("data", keep);

        proc.on("error", (error) => {
            started.output += `\n${error.message}`;
        });

        proc.on("close", (code) => {
            clearTimeout(timer);
            started.exit = code;
            started.state = code === 0 ? "done" : "failed";
            started.finished = Date.now();
            check();
        });

        install = started;

        return "Started `make install`. Poll akdev_status; the full tools appear when it's done.";
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

                if (name === "akdev_install") return text(id, startInstall());

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

        const proc = spawn(process.execPath, [join(ROOT, "dev-mcp", "main.ts"), "serve"], {
            cwd: ROOT,
            env: { ...process.env, [NO_FALLBACK]: "1" },
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

    process.stderr.write(`authentik-dev: setup mode, missing ${missing().join(", ")}\n`);
}
