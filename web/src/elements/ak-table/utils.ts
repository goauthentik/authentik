import { groupBy as groupByProcessor } from "@goauthentik/common/utils.js";

import { html } from "lit";

import {
    KeyBy,
    RawType,
    TableFlat,
    TableGrouped,
    TableInputType,
    TableRow,
    TableType,
} from "./types";

// TypeScript was extremely specific about due diligence here.
export const isTableRows = (v: unknown): v is TableRow[] =>
    Array.isArray(v) &&
    v.length > 0 &&
    typeof v[0] === "object" &&
    v[0] !== null &&
    !("kind" in v[0]) &&
    "content" in v[0];

export const isTableGrouped = (v: unknown): v is TableGrouped =>
    typeof v === "object" && v !== null && "kind" in v && v.kind === "groups";

export const isTableFlat = (v: unknown): v is TableFlat =>
    typeof v === "object" && v !== null && "kind" in v && v.kind === "flat";

/**
 * @func convertForTable
 *
 * Takes a variety of input types and streamlines them. Can't handle every contingency; be prepared
 * to do conversions yourself as resources demand. Great for about 80% of use cases, though.
 *
 * - @param groupBy: If provided, for each item it must provide the group's name, by which the
 *   content will be grouped. The name is not a slug; it is what will be displayed.
 * - @param keyBy: If provided, for each item it must provide a key for the item, which will be the
 *   value returned.
 *
 * For content that has already been grouped or converted into a single "flat" group, providing
 * these functions will not do anything except generate a warning on the console.
 */

export function convertContent(
    content: TableInputType,
    { groupBy, keyBy }: { groupBy?: KeyBy; keyBy?: KeyBy } = {},
): TableType {
    // TableGrouped
    if (isTableGrouped(content)) {
        if (groupBy || keyBy) {
            console.warn("Passed processor function when content is already marked as grouped");
        }
        return content;
    }

    if (isTableFlat(content)) {
        if (groupBy || keyBy) {
            console.warn("Passed processor function when content is already marked as flat");
        }
        return content;
    }

    // TableRow[]
    if (isTableRows(content)) {
        if (groupBy) {
            console.warn(
                "Passed processor function when content is processed and can't be analyzed for grouping",
            );
        }
        return {
            kind: "flat",
            content: content,
        };
    }

    // TableRow or Rawtype, but empty
    if (Array.isArray(content) && content.length === 0) {
        return {
            kind: "flat",
            content: [],
        };
    }

    const templatizeAsNeeded = (rows: RawType[][]): TableRow[] =>
        rows.map((row) => ({
            ...(keyBy ? { key: keyBy(row) } : {}),
            content: row.map((item) => (typeof item === "object" ? item : html`${item}`)),
        }));

    if (groupBy) {
        const groupedContent = groupByProcessor(content, groupBy);
        return {
            kind: "groups",
            content: groupedContent.map(([group, rowsForGroup]) => ({
                kind: "group",
                group,
                content: templatizeAsNeeded(rowsForGroup),
            })),
        };
    }

    return {
        kind: "flat",
        content: templatizeAsNeeded(content),
    };
}
