import { TemplateResult } from "lit";

import { Pagination } from "@goauthentik/api";

export type DualSelectPair = [string, string | TemplateResult];

export type BasePagination = Pick<
    Pagination,
    "startIndex" | "endIndex" | "count" | "previous" | "next"
>;

export type DataProvision = {
    pagination: Pagination;
    options: DualSelectPair[];
}

export type DataProvider = (page: number) => Promise<DataProvision>;
