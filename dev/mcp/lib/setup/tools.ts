/**
 * @file What setup mode tells the agent: its instructions and its two tools.
 */

/**
 * The first 512 characters hold the rules: Codex only guarantees that much.
 */
export const SETUP_INSTRUCTIONS = `\
authentik-dev is in setup mode: this clone's dependencies aren't installed, so its checks aren't \
available yet. Tell the person, and ask whether to install them now. If they agree, call \
akdev_install: it runs \`make install\` (Node and Python packages, several minutes, network \
access). When the dependencies are in place, this server switches to its full tool set by itself, \
with no restart. akdev_status shows progress.
`;

export const SETUP_CAPABILITIES = { tools: { listChanged: true } };

export const SETUP_TOOLS = [
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
