import { TemplateResult } from "lit";

import { Pagination } from "@goauthentik/api";

// Key, Label (string or TemplateResult), (optional) string to sort by. If the sort string is
// missing, it will use the label, which doesn't always work for TemplateResults).
export type DualSelectPair = [string, string | TemplateResult, string?];

export type BasePagination = Pick<
    Pagination,
    "startIndex" | "endIndex" | "count" | "previous" | "next"
>;

export type DataProvision = {
    pagination: Pagination;
    options: DualSelectPair[];
};

export type DataProvider = (page: number) => Promise<DataProvision>;
