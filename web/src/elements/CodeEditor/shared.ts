import { parse as parseYAML, stringify as stringifyYAML } from "yaml";

/**
 * The languages the code editor highlights, named by their Monaco language ID.
 */
export const CodeEditorMode = {
    XML: "xml",
    JavaScript: "javascript",
    HTML: "html",
    CSS: "css",
    Python: "python",
    YAML: "yaml",
} as const satisfies Record<string, string>;

export type CodeEditorMode = (typeof CodeEditorMode)[keyof typeof CodeEditorMode];

//#region Serialization

export function stringifyCodeEditorSource(value: unknown, mode: CodeEditorMode): string {
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

export function parseCodeEditorSource<T = unknown>(value: string, mode: CodeEditorMode): T {
    switch (mode) {
        case CodeEditorMode.YAML:
            return parseYAML(value);
        case CodeEditorMode.JavaScript:
            return JSON.parse(value);
    }

    return value as T;
}

//#endregion
