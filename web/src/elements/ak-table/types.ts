import { TemplateResult } from "lit";

import { TableColumn } from "./TableColumn";

// authentik's standard tables (ak-simple-table, ak-select-table) all take a variety of types, the
// simplest of which is just an array of tuples, one for each column, along with an tuple for
// the definition of the column itself.
//
// More complex types are defined below, including those for grouped content. In he "utils"
// collection with this element you can find the [`convertContent`](./utils.ts) function, which can
// be used to create grouped content by providing a `groupBy` function, as well as selectable
// content by providing a `keyBy` function. See the documentation for `convertContent`.

/**
 * - key (string, option): the value to return on "click", if the table is clickable / selectable
 * - content (TemplateResult[]): The contents of the rows to be shown
 */
export type TableRow = {
    key?: string;
    content: TemplateResult[];
    // expansion?: () => TemplateResult;
};

/**
 * For a collection of rows without groups
 *
 */
export type TableFlat = {
    kind: "flat";
    content: TableRow[];
};

/**
 * For a single grouped collection; the name of the group and the contents.
 */
export type TableGroup = {
    kind: "group";
    group: string;
    content: TableRow[];
};

/**
 * For a grouped collection, all of the groups.
 */
export type TableGrouped = {
    kind: "groups";
    content: TableGroup[];
};

/**
 * For convenience, a table column can be defined either by the string defining its
 * content, or by a pair of strings defining the content and the sort-by header
 * used to indicate and control sortability.
 */
export type Column = TableColumn | string | [string, string?];

export type RawType = string | number | TemplateResult;
export type TableInputType = RawType[][] | TableRow[] | TableGrouped | TableFlat;
export type TableType = TableGrouped | TableFlat;

export type KeyBy = (_: RawType[]) => string;
