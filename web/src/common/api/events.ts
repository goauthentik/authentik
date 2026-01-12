/**
 * @file API event utilities.
 */

/**
 * Information about a completed API request.
 */
export interface APIRequestInfo {
    time: number;
    method: string;
    path: string;
    status: number;
}

/**
 * Event dispatched via EventMiddleware after an API request is completed.
 */
export class AKRequestPostEvent extends Event {
    public static readonly eventName = "ak-request-post";

    public readonly requestInfo: APIRequestInfo;

    constructor(requestInfo: APIRequestInfo) {
        super(AKRequestPostEvent.eventName, { bubbles: true, composed: true });

        this.requestInfo = requestInfo;
    }
}

declare global {
    interface WindowEventMap {
        [AKRequestPostEvent.eventName]: AKRequestPostEvent;
    }
}
