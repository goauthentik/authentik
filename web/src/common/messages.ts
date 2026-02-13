import type { TemplateResult } from "lit";

export enum MessageLevel {
    error = "error",
    warning = "warning",
    success = "success",
    info = "info",
}

/**
 * An error message returned from an API endpoint.
 *
 * @remarks
 * This interface must align with the server-side event dispatcher.
 *
 * @see {@link ../authentik/core/templates/base/skeleton.html}
 */
export interface APIMessage {
    level: MessageLevel;
    message: string;
    description?: string | TemplateResult;
    icon?: string;
}

export class AKMessageEvent extends Event {
    static readonly eventName = "ak-message";

    constructor(public readonly message: APIMessage) {
        super(AKMessageEvent.eventName, { bubbles: true, composed: true });
    }
}

declare global {
    interface WindowEventMap {
        [AKMessageEvent.eventName]: AKMessageEvent;
    }
}
