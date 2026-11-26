/**
 * @file Shared pieces of the MCP tool definitions.
 */

import type { ToolAnnotations } from "@modelcontextprotocol/server";

export const READ_ONLY: ToolAnnotations = {
    readOnlyHint: true,
    destructiveHint: false,
    openWorldHint: false,
};

export const WRITES_TREE: ToolAnnotations = {
    readOnlyHint: false,
    destructiveHint: false,
    openWorldHint: false,
};

/** A tool result with the same data as text and as structured content. */
export function reply(data: object) {
    const structured = JSON.parse(JSON.stringify(data)) as Record<string, unknown>;
    return {
        content: [{ type: "text" as const, text: JSON.stringify(structured, null, 2) }],
        structuredContent: structured,
    };
}
