/**
 * @file Form-related custom events.
 */

/**
 * Event dispatched after a form has been successfully submitted.
 */
export class AKFormSubmittedEvent<R = unknown> extends Event {
    public static readonly eventName = "ak-form-submitted";

    constructor(public readonly response: R) {
        super(AKFormSubmittedEvent.eventName, { bubbles: true, composed: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [AKFormSubmittedEvent.eventName]: AKFormSubmittedEvent;
    }
}
