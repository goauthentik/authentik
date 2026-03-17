import "#elements/timestamp/ak-timestamp";

import { Pagination } from "@goauthentik/api";

import { html, TemplateResult } from "lit";

export interface TableLike {
    /**
     * The column name to order by, optionally prefixed with `-` to reverse the order.
     */
    order?: string;
    fetch: () => void;
}

export interface BaseTableListRequest {
    ordering?: string;
    page: number;
    pageSize: number;
    search?: string;
}

export interface PaginatedResponse<T> {
    pagination: Pagination;
    autocomplete?: { [key: string]: string };

    results: Array<T>;
}

/**
 * Render a timestamp as a human-readable string.
 *
 * @param timestamp - The timestamp to render.
 */
export function Timestamp(timestamp?: Date | null): TemplateResult {
    return html`<ak-timestamp .timestamp=${timestamp} elapsed datetime></ak-timestamp>`;
}
