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

export async function parseAPIError(error: Error): Promise<APIErrorTypes> {
    if (!(error instanceof ResponseError)) {
        return error;
    }
    if (error.response.status < 400 && error.response.status > 499) {
        return error;
    }
    const body = await error.response.json();
    if (error.response.status === 400) {
        return ValidationErrorFromJSON(body);
    }
    if (error.response.status === 403) {
        return GenericErrorFromJSON(body);
    }
    return body;
}
