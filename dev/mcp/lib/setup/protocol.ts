/**
 * @file The subset of MCP's JSON-RPC that setup mode implements, with Node built-ins only.
 */

export interface Message {
    jsonrpc: "2.0";
    id?: string | number;
    method?: string;
    params?: Record<string, unknown>;
}

/**
 * Protocol versions answered with `initialize`; the SDK's list, newest first.
 */
export const VERSIONS = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05", "2024-10-07"];

export function send(message: object): void {
    process.stdout.write(`${JSON.stringify(message)}\n`);
}

export function notify(method: string, params?: object): void {
    send({ jsonrpc: "2.0", method, params });
}

export function result(id: Message["id"], value: object): void {
    send({ jsonrpc: "2.0", id, result: value });
}

export function error(id: Message["id"] | null, code: number, message: string): void {
    send({ jsonrpc: "2.0", id, error: { code, message } });
}

/**
 * A tool result with a single text block.
 */
export function text(id: Message["id"], body: string, isError = false): void {
    result(id, { content: [{ type: "text", text: body }], isError });
}
