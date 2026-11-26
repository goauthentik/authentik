/**
 * @file Hand a setup-mode session to the real server: start it as a child, replay the client's
 *   handshake, then pass every message through in both directions.
 */

import { spawn } from "node:child_process";
import { join } from "node:path";
import { createInterface } from "node:readline";
import type { Writable } from "node:stream";

import { chooseNode, nodeBinary, withNode } from "#dev-mcp/environment/node";
import { type Message, notify } from "#dev-mcp/setup/protocol";
import { ROOT } from "#dev/lib/git";

/**
 * Set for the real server's process, so a still-broken install can't start another setup mode.
 */
export const NO_FALLBACK = "AKDEV_NO_FALLBACK";

const HANDOVER_ID = "akdev-handover";

const line = (message: object) => `${JSON.stringify({ jsonrpc: "2.0", ...message })}\n`;

/**
 * Start the real server. `initialize` is the client's original handshake, or null after the
 * stateless `server/discover`, which leaves no handshake to replay. `ready` gets the child's stdin
 * once it's taking messages. The client is then told its tool list changed.
 */
export function handover(
    initialize: Message["params"] | null,
    ready: (child: Writable) => void,
): void {
    process.stderr.write("authentik-dev: dependencies found, starting the full server\n");

    // The real server's checks run make and pnpm, so they need the fitting Node too.
    const node = chooseNode();

    const proc = spawn(nodeBinary(node), [join(ROOT, "dev", "mcp", "main.ts"), "serve"], {
        cwd: ROOT,
        env: withNode({ ...process.env, [NO_FALLBACK]: "1" }, node),
        stdio: ["pipe", "pipe", "inherit"],
    });

    proc.on("exit", (code) => process.exit(code ?? 1));

    let proxying = false;

    const proxy = () => {
        proxying = true;
        ready(proc.stdin);
        notify("notifications/tools/list_changed");
    };

    createInterface({ input: proc.stdout }).on("line", (output) => {
        if (proxying) return void process.stdout.write(`${output}\n`);

        // The real server's answer to the replayed handshake. The client already has one.
        if ((JSON.parse(output) as Message).id !== HANDOVER_ID) return;

        proc.stdin.write(line({ method: "notifications/initialized" }));
        proxy();
    });

    if (!initialize) return proxy();

    proc.stdin.write(line({ id: HANDOVER_ID, method: "initialize", params: initialize }));
}
