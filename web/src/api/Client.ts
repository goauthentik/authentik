export interface AKPagination {
    next?: number;
    previous?: number;

    count: number;
    current: number;
    totalPages: number;

    startIndex: number;
    endIndex: number;
}

export interface AKResponse<T> {
    pagination: AKPagination;

    results: Array<T>;
}
