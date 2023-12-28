import { TemplateResult } from "lit";

import { Pagination } from "@goauthentik/api";

export type DualSelectPair = [string, string | TemplateResult];

export type BasePagination = Pick<
    Pagination,
    "startIndex" | "endIndex" | "count" | "previous" | "next"
>;
