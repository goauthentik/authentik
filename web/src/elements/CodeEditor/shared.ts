import { parse as parseYAML, stringify as stringifyYAML } from "yaml";

/**
 * The languages the code editor highlights, named by their Monaco language ID.
 */
export const CodeEditorMode = {
    XML: "xml",
    JavaScript: "javascript",
    JSON: "json",
    HTML: "html",
    CSS: "css",
    Python: "python",
    YAML: "yaml",
} as const satisfies Record<string, string>;

export type CodeEditorMode = (typeof CodeEditorMode)[keyof typeof CodeEditorMode];

/**
 * A JSON Schema that JSON and YAML editors validate, complete and describe their content with,
 * given as a URL or as the schema itself.
 */
export type CodeEditorSchema = string | object;

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
        case "json":
            return JSON.stringify(value, null, 2);
    }

    return String(value).toString();
}

export function parseCodeEditorSource<T = unknown>(value: string, mode: CodeEditorMode): T {
    switch (mode) {
        case CodeEditorMode.YAML:
            return parseYAML(value);
        case CodeEditorMode.JavaScript:
            return JSON.parse(value);
        // JSON is valid YAML, so this also accepts YAML pasted into a JSON field.
        case CodeEditorMode.JSON:
            return parseYAML(value);
    }

    return value as T;
}

//#endregion
