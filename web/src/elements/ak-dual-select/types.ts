import { TemplateResult } from "lit";

import { Pagination } from "@goauthentik/api";

export const DualSelectEventType = {
    AddSelected: "ak-dual-select-add",
    RemoveSelected: "ak-dual-select-remove",
    Search: "ak-dual-select-search",
    AddAll: "ak-dual-select-add-all",
    RemoveAll: "ak-dual-select-remove-all",
    DeleteAll: "ak-dual-select-remove-everything",
    AddOne: "ak-dual-select-add-one",
    RemoveOne: "ak-dual-select-remove-one",
    Move: "ak-dual-select-move",
    MoveChanged: "ak-dual-select-available-move-changed",
    Change: "ak-dual-select-change",
    NavigateTo: "ak-pagination-nav-to",
} as const satisfies Record<string, string>;

export type DualSelectEventType = (typeof DualSelectEventType)[keyof typeof DualSelectEventType];

/**
 * A tuple representing a single object in the dual select list.
 */
export type DualSelectPair<T = unknown> = [
    /**
     * The key used to identify the object in the API.
     */
    key: string,
    /**
     * A human-readable label for the object.
     */
    label: string | TemplateResult,
    /**
     * A string to sort by. If not provided, the key will be used.
     */
    sortBy: string,
    /**
     * A local mapping of the key to the object. This is used by some specific apps.
     *
     * API layers may use this as a way to find the preset object.
     */
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

export const SearchbarEventSource = {
    Available: "ak-dual-list-available-search",
    Selected: "ak-dual-list-selected-search",
} as const satisfies Record<string, string>;

export type SearchbarEventSource = (typeof SearchbarEventSource)[keyof typeof SearchbarEventSource];

export interface SearchbarEventDetail {
    source: SearchbarEventSource;
    value: string;
}
