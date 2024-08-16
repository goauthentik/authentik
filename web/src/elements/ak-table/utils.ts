import { TemplateResult, html } from "lit";

import { TableFlat, TableGrouped, TableRow } from "./types";

// TypeScript was extremely specific about due diligence here.
const isTableRows = (v: unknown): v is TableRow[] =>
    Array.isArray(v) &&
    v.length > 0 &&
    typeof v[0] === "object" &&
    v[0] !== null &&
    !("kind" in v[0]) &&
    "content" in v[0];

type RawType = string | number | TemplateResult;
type TableInputType = RawType[][] | TableRow[] | TableGrouped;
type TableType = TableGrouped | TableFlat;

export function convertContent(content: TableInputType): TableType {
    if (Array.isArray(content)) {
        if (content.length === 0) {
            return {
                kind: "table-flat",
                content: [],
            };
        }

        if (isTableRows(content)) {
            return {
                kind: "table-flat",
                content: content,
            };
        }

        return {
            kind: "table-flat",
            content: content.map((onerow) => ({
                content: onerow.map((item: string | number | TemplateResult) =>
                    typeof item === "object" ? item : html`${item}`,
                ),
            })),
        };
    }

    // Must be TableGrouped already, then.
    return content;
}
