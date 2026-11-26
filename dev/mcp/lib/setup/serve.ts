/**
 * @file Setup mode: a minimal MCP server used until project dependencies are installed. It answers
 *   the handshake and two tools, and hands the session to the real server once the dependencies
 *   appear, from akdev_install or a `make install` run anywhere.
 */

import { createInterface } from "node:readline";
import type { Writable } from "node:stream";

import { chooseNode, describeNode } from "#dev-mcp/environment/node";
import { type Progress, noProgress } from "#dev-mcp/results/progress";
import { handover } from "#dev-mcp/setup/handover";
import { Installer, missingPackages } from "#dev-mcp/setup/install";
import { type Message, VERSIONS, error, notify, result, text } from "#dev-mcp/setup/protocol";
import { SETUP_CAPABILITIES, SETUP_INSTRUCTIONS, SETUP_TOOLS } from "#dev-mcp/setup/tools";

export { NO_FALLBACK } from "#dev-mcp/setup/handover";

const POLL_MS = 3_000;

export function serveFallback(): void {
    const installer = new Installer();
    let initialize: Message["params"] | null = null;
    let mode: "setup" | "handover" | "proxy" = "setup";
    let child: Writable | null = null;
    const pending: string[] = [];

    function check(): void {
        if (mode !== "setup" || installer.running || missingPackages().length) return;

        mode = "handover";

        handover(initialize, (stdin) => {
            child = stdin;
            mode = "proxy";

            for (const queued of pending.splice(0)) stdin.write(`${queued}\n`);
        });
    }

    /**
     * With a progress token, keep the call open: report each make target, and answer with the
     * status when the install ends. Without one, answer at once and let the agent poll.
     */
    function install(id: Message["id"], params: Message["params"]): void {
        const token = (params?._meta as { progressToken?: string | number } | undefined)
            ?.progressToken;

        if (token === undefined || installer.running) {
            const { message } = installer.start(noProgress, check);

            return text(id, message);
        }

        const update: Progress = (progress, total, message) =>
            notify("notifications/progress", { progressToken: token, progress, total, message });

        const { message, started } = installer.start(update, () => {
            text(id, installer.status(), installer.current?.state === "failed");
            check();
        });

        // Refused before starting: nothing will call back, so answer now.
        if (!started) text(id, message);
    }

    function handle(message: Message): void {
        const { id, method } = message;

        // Notifications, and responses to requests we never send, need no reply.
        if (id === undefined || !method) return;

        switch (method) {
            case "initialize": {
                initialize = message.params ?? {};

                const asked = String(initialize.protocolVersion ?? "");

                return result(id, {
                    protocolVersion: VERSIONS.includes(asked) ? asked : VERSIONS[0],
                    capabilities: SETUP_CAPABILITIES,
                    serverInfo: { name: "authentik-dev", version: "0.1.0" },
                    instructions: SETUP_INSTRUCTIONS,
                });
            }
            case "server/discover":
                return result(id, {
                    supportedVersions: VERSIONS,
                    capabilities: SETUP_CAPABILITIES,
                    instructions: SETUP_INSTRUCTIONS,
                });
            case "ping":
                return result(id, {});
            case "tools/list":
                return result(id, { tools: SETUP_TOOLS });
            case "tools/call": {
                const name = String(message.params?.name ?? "");

                if (name === "akdev_status") return text(id, installer.status());

                if (name === "akdev_install") return install(id, message.params);

                return text(
                    id,
                    `Unknown tool ${name}. In setup mode: akdev_status, akdev_install.`,
                    true,
                );
            }
            default:
                return error(id, -32601, `${method} isn't available in setup mode`);
        }
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
                return error(null, -32700, "Parse error");
            }

            handle(message);
        })
        .on("close", () => {
            clearInterval(poll);
            child?.end();

            if (!child) process.exit(0);
        });

    process.stderr.write(
        `authentik-dev: setup mode, missing ${missingPackages().join(", ")}. ${describeNode(chooseNode())}\n`,
    );
}
