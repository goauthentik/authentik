import { SlottedTemplateResult } from "#elements/types";

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
    description?: SlottedTemplateResult;
    icon?: string;
    /**
     * An optional key to determine uniqueness of the message.
     *
     * Defaults to the message text.
     */
    key?: PropertyKey;
}
