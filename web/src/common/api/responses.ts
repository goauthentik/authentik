/**
 * @file Utilities for API requests
 */

import { APIError } from "#common/errors/network";

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
