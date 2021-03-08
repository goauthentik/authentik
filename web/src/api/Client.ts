export interface QueryArguments {
    page?: number;
    page_size?: number;
    [key: string]: number | string | boolean | undefined | null;
}

export interface BaseInheritanceModel {

    object_type: string;

    verbose_name: string;
    verbose_name_plural: string;

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
