import { TemplateResult } from "lit";

import { TableColumn } from "./TableColumn";

// authentik's tables (ak-basic-table, ak-select-table, ak-table) all take a tuple of two
// or three items, or a collection of groups of such tuples. In order to push dynamic checking
// around, we also allow the inclusion of a fourth component, which is just a scratchpad the
// developer can use for their own reasons.

// The displayed element for our list can be a TemplateResult. If it is, we *strongly* recommend
// that you include the `sortBy` string as well, which is used for sorting but is also used for our
// autocomplete element (ak-search-select) both for tracking the user's input and for what we
// display in the autocomplete input box.

/**
 * - key (string, option): the value to return on "click", if the table is clickable / selectable
 * - content (TemplateResult[]): The contents of the rows to be shown
 */
export type TableRow = {
    key?: string;
    content: TemplateResult[];
    expansion?: () => TemplateResult;
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
