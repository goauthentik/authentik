import {
    GenericError,
    GenericErrorFromJSON,
    ResponseError,
    ValidationError,
    ValidationErrorFromJSON,
} from "@goauthentik/api";

//#region HTTP

/**
 * Common HTTP status names used in the API and their corresponding codes.
 */
export const HTTPStatusCode = {
    BadRequest: 400,
    Forbidden: 403,
    InternalServiceError: 500,
} as const satisfies Record<string, number>;

export type HTTPStatusCode = (typeof HTTPStatusCode)[keyof typeof HTTPStatusCode];

export type HTTPErrorJSONTransformer<T = unknown> = (json: T) => APIError;

export const HTTPStatusCodeTransformer: Record<number, HTTPErrorJSONTransformer> = {
    [HTTPStatusCode.BadRequest]: ValidationErrorFromJSON,
    [HTTPStatusCode.Forbidden]: GenericErrorFromJSON,
} as const;

//#endregion

//#region Type Predicates

/**
 * Type predicate to check if a response contains a JSON body.
 *
 * This is useful to guard against parsing errors when attempting to read the response body.
 */
export function isJSONResponse(response: Response): boolean {
    return Boolean(response.headers.get("content-type")?.includes("application/json"));
}

/**
 * An error originating from an aborted request.
 *
 * @see {@linkcode isAbortError} to check if an error originates from an aborted request.
 */
export interface AbortErrorLike extends DOMException {
    name: "AbortError";
}

/**
 * Type predicate to check if an error originates from an aborted request.
 *
 * @see {@link https://developer.mozilla.org/en-US/docs/Web/API/AbortController/abort | MDN}
 */
export function isAbortError(error: unknown): error is AbortErrorLike {
    return error instanceof DOMException && error.name === "AbortError";
}

/**
 * Type predicate to check if an error originates from an aborted request.
 *
 * @see {@linkcode isAbortError} for the underlying implementation.
 */
export function isCausedByAbortError(error: unknown): error is AbortErrorLike {
    return (
        error instanceof Error &&
        // ---
        (isAbortError(error) || isAbortError(error.cause))
    );
}

//#endregion

//#region API

/**
 * An API response error, typically derived from a {@linkcode Response} body.
 *
 * @see {@linkcode parseAPIResponseError}
 */
export type APIError = ValidationError | GenericError;

/**
 * Given an error-like object, attempts to normalize it into a {@linkcode GenericError}
 * suitable for display to the user.
 */
export function createSyntheticGenericError(detail?: string): GenericError {
    const syntheticGenericError: GenericError = {
        detail: detail || ResponseErrorMessages[HTTPStatusCode.InternalServiceError].reason,
    };

    return syntheticGenericError;
}

/**
 * An error that contains a native response object.
 *
 * @see {@linkcode isResponseErrorLike} to determine if an error contains a response object.
 */
export type APIErrorWithResponse = Pick<ResponseError, "response" | "message">;

/**
 * Type guard to check if an error contains a HTTP {@linkcode Response} object.
 *
 * @see {@linkcode parseAPIResponseError} to parse the response body into a {@linkcode APIError}.
 */
export function isResponseErrorLike(errorLike: unknown): errorLike is APIErrorWithResponse {
    if (!errorLike || typeof errorLike !== "object") return false;

    return "response" in errorLike && errorLike.response instanceof Response;
}

/**
 * A descriptor to provide a human readable error message for a given HTTP status code.
 *
 * @see {@linkcode ResponseErrorMessages} for a list of fallback error messages.
 */
interface ResponseErrorDescriptor {
    headline: string;
    reason: string;
}

/**
 * Fallback error messages for HTTP status codes used when a more specific error message is not available in the response.
 */
export const ResponseErrorMessages: Record<number, ResponseErrorDescriptor> = {
    [HTTPStatusCode.BadRequest]: {
        headline: "Bad request",
        reason: "The server did not understand the request",
    },
    [HTTPStatusCode.InternalServiceError]: {
        headline: "Internal server error",
        reason: "An unexpected error occurred",
    },
} as const;

/**
 * Composes a human readable error message from a {@linkcode ResponseErrorDescriptor}.
 *
 * Note that this is kept separate from localization to lower the complexity of the error handling code.
 */
export function composeResponseErrorDescriptor(descriptor: ResponseErrorDescriptor): string {
    return `${descriptor.headline}: ${descriptor.reason}`;
}

export const ErrorFieldFallbackKeys = [
    // ---
    "detail", // OpenAPI
    "non_field_errors", // ValidationError.non_field_errors
    "message", // Error.prototype.message
    "string", // OpenAPI
] as const;

export type FallbackError = Record<(typeof ErrorFieldFallbackKeys)[number], string | undefined>;

/**
 * Attempts to pluck a human readable error message from a {@linkcode ValidationError}.
 */
export function pluckErrorDetail(validationError: ValidationError, fallback?: string): string;
/**
 * Attempts to pluck a human readable error message from a {@linkcode GenericError}.
 */
export function pluckErrorDetail(genericError: GenericError, fallback?: string): string;
/**
 * Attempts to pluck a human readable error message from an `Error` object.
 */
export function pluckErrorDetail(error: Error, fallback?: string): string;
/**
 * Attempts to pluck a human readable error message from an error-like object.
 *
 * Prioritizes the `detail` key, then the `message` key.
 *
 */
export function pluckErrorDetail(errorLike: unknown, fallback?: string): string;
export function pluckErrorDetail(errorLike: unknown, fallback?: string): string {
    fallback ||= composeResponseErrorDescriptor(
        ResponseErrorMessages[HTTPStatusCode.InternalServiceError],
    );

    if (errorLike && typeof errorLike === "string") {
        return errorLike;
    }

    if (!errorLike || typeof errorLike !== "object") {
        return fallback;
    }

    for (const fieldKey of ErrorFieldFallbackKeys) {
        if (!(fieldKey in errorLike)) continue;

        const value = (errorLike as FallbackError)[fieldKey];

        if (typeof value === "string" && value) {
            return value;
        }
    }

    return fallback;
}

/**
 * Given API error, parses the response body and transforms it into a {@linkcode APIError}.
 */
export async function parseAPIResponseError<T extends APIError = APIError>(
    error: unknown,
): Promise<T> {
    if (!isResponseErrorLike(error)) {
        const message = error instanceof Error ? error.message : String(error);

        return createSyntheticGenericError(message) as T;
    }

    const { response, message } = error;

    if (!isJSONResponse(response)) {
        return createSyntheticGenericError(message || response.statusText) as T;
    }

    return response
        .json()
        .then((body) => {
            const transformer = HTTPStatusCodeTransformer[response.status];
            const transformedBody = transformer ? transformer(body) : body;

            return transformedBody as unknown as T;
        })
        .catch((transformerError: unknown) => {
            console.error("Failed to parse response error body", transformerError);

            return createSyntheticGenericError(message || response.statusText) as T;
        });
}

//#endregion
