/**
 * @file Utilities for API requests
 */

import type { APIError } from "#common/errors/network";

import type { Pagination } from "@goauthentik/api";

export interface APIResultLoading {
    loading: true;
    error: null;
}

export interface APIResultError {
    loading: false;
    error: APIError;
}

export type APIResultSucccess<T extends object = object> = T & {
    error?: null;
    loading?: false;
};

export type APIResult<T extends object> = APIResultLoading | APIResultError | APIResultSucccess<T>;

export function isAPIResultReady<T extends object>(
    result: APIResult<T> | null | undefined,
): result is APIResultSucccess<T> {
    return !!(result && result.loading !== false && result.error !== null);
}

/**
 * A generic interface for paginated API responses.
 *
 * @template T The type of the items in the results array.
 * @template A The type of the autocomplete object, if present.
 */
export interface PaginatedResponse<T, A extends object = object> {
    pagination: Pagination;
    autocomplete?: A;

    results: Array<T>;
}

/**
 * Create a {@link PaginatedResponse} from an iterable of items.
 *
 * @template T The type of the items in the results array.
 * @template A The type of the autocomplete object, if present.
 * @param input An iterable of items to include in the results array.
 */
export function createPaginatedResponse<T = unknown, A extends object = object>(
    input: Iterable<T> = [],
): PaginatedResponse<T, A> {
    const results = Array.from(input);

    return {
        pagination: {
            count: results.length,
            next: 0,
            previous: 0,
            current: 0,
            totalPages: 1,
            startIndex: 0,
            endIndex: 0,
        },
        results,
        autocomplete: {} as A,
    };
}
