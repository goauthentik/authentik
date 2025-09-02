import { Pagination } from "@goauthentik/api";

export interface TableLike {
    order?: string;
    fetch: () => void;
}

export interface PaginatedResponse<T> {
    pagination: Pagination;
    autocomplete?: { [key: string]: string };

    results: Array<T>;
}
