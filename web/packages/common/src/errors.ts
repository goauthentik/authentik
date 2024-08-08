import {
    GenericError,
    GenericErrorFromJSON,
    ResponseError,
    ValidationError,
    ValidationErrorFromJSON,
} from "@goauthentik/api";

export class SentryIgnoredError extends Error {}
export class NotFoundError extends Error {}
export class RequestError extends Error {}

export type APIErrorTypes = ValidationError | GenericError;

const HTTP_BAD_REQUEST = 400;
const HTTP_FORBIDDEN = 403;
const HTTP_INTERNAL_SERVICE_ERROR = 500;

export async function parseAPIError(error: Error): Promise<APIErrorTypes> {
    if (!(error instanceof ResponseError)) {
        return error;
    }
    if (
        error.response.status < HTTP_BAD_REQUEST ||
        error.response.status >= HTTP_INTERNAL_SERVICE_ERROR
    ) {
        return error;
    }
    const body = await error.response.json();
    if (error.response.status === HTTP_BAD_REQUEST) {
        return ValidationErrorFromJSON(body);
    }
    if (error.response.status === HTTP_FORBIDDEN) {
        return GenericErrorFromJSON(body);
    }
    return body;
}
