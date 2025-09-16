import { Pagination } from "@goauthentik/api";

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
