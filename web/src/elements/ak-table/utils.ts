import { TableGrouped, TableRow } from "./types";

const isTableRow = (v: unknown): v is TableRow =>
    typeof v === "object" && v !== null && "kind" in v && v.kind === "table-row";

export function groupContent(content: TemplateResult[][] | TableRow[] | TableGrouped): GroupedOptions {
    if (Array.isArray(content)) {
        if (content.length === 0) {
            return {
                kind: "table-flat",
                content: [],
            };
        }

        if (isTableRow(content[0])) {
            return {
                kind: "table-flat",
                content,
            };
        }

        // TemplateResult[][]
        return {
            kind: "table-flat",
            content: content.map((onerow) => ({
                kind: "table-row",
                content: onerow,
            })),
        };
    }

    // Must be TableGrouped already, then.
    return content;
}
