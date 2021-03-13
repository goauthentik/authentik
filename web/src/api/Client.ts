export interface QueryArguments {
    page?: number;
    page_size?: number;
    [key: string]: number | string | boolean | undefined | null;
}

export interface BaseInheritanceModel {

    objectType: string;

    verboseName: string;
    verboseNamePlural: string;

}

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
