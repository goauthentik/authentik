import { TemplateResult } from "lit";

import { Pagination } from "@goauthentik/api";

//
// - key: string
// - label (string or TemplateResult),
// - sortBy (optional) string to sort by. If the sort string is
// - localMapping: The object the key represents; used by some specific apps. API layers may use
//   this as a way to find the preset object.
//
// Note that this is a *tuple*, not a record or map!

export type DualSelectPair<T = never> = [
    key: string,
    label: string | TemplateResult,
    sortBy?: string,
    localMapping?: T,
];

export type BasePagination = Pick<
    Pagination,
    "startIndex" | "endIndex" | "count" | "previous" | "next"
>;

export type DataProvision = {
    pagination?: Pagination;
    options: DualSelectPair[];
};

export type DataProvider = (page: number, search?: string) => Promise<DataProvision>;

export interface SearchbarEventDetail {
    source: string;
    value: string;
}

export type SearchbarEvent = CustomEvent<SearchbarEventDetail>;
