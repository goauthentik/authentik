import { parse as parseYAML, stringify as stringifyYAML } from "yaml";

export const CodeMirrorMode = {
    XML: "xml",
    JavaScript: "javascript",
    HTML: "html",
    CSS: "css",
    Python: "python",
    YAML: "yaml",
} as const satisfies Record<string, string>;

export type CodeMirrorMode = (typeof CodeMirrorMode)[keyof typeof CodeMirrorMode];

//#region Serialization

export function stringifyCodeMirrorSource(value: unknown, mode: CodeMirrorMode): string {
    if (typeof value === "string" || value instanceof String) {
        return value.toString();
    }

    switch (mode.toLowerCase()) {
        case "yaml":
            return stringifyYAML(value);
        case "javascript":
            return JSON.stringify(value);
    }

    return String(value).toString();
}

export function parseCodeMirrorSource<T = unknown>(value: string, mode: CodeMirrorMode): T {
    switch (mode) {
        case CodeMirrorMode.YAML:
            return parseYAML(value);
        case CodeMirrorMode.JavaScript:
            return JSON.parse(value);
    }

    return value as T;
}

//#endregion
