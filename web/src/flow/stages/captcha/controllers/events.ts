/**
 * @remarks
 *
 *   These are constructed by the vendor bundles rather than by us. Declaring them here gives
 *   listeners a typed payload at the point of use instead of casting an untyped
 *   {@linkcode Event}, and keeps the shape of each vendor's contract in one place.
 * @file Events emitted by third-party CAPTCHA widgets.
 */

export interface CapSolveDetail {
    token: string;
}

export interface CapErrorDetail {
    message: string;
}

/**
 * Emitted by a `<cap-widget>` once its proof-of-work challenge has been solved.
 */
export class CapSolveEvent extends Event {
    static readonly eventName = "solve";

    constructor(public readonly detail: CapSolveDetail) {
        super(CapSolveEvent.eventName);
    }
}

/**
 * Emitted by a `<cap-widget>` when a challenge cannot be completed.
 */
export class CapErrorEvent extends Event {
    static readonly eventName = "error";

    constructor(public readonly detail: CapErrorDetail) {
        super(CapErrorEvent.eventName);
    }
}

/**
 * The events a `<cap-widget>` adds on top of the standard element events.
 *
 * Deliberately not extending {@linkcode HTMLElementEventMap}: Cap's `error` event carries a
 * `detail` payload and is unrelated to the DOM's {@linkcode ErrorEvent}, which the standard
 * map already binds that name to.
 */
export interface CapWidgetEventMap {
    [CapSolveEvent.eventName]: CapSolveEvent;
    [CapErrorEvent.eventName]: CapErrorEvent;
}

export interface CapWidgetElement extends HTMLElement {
    addEventListener<K extends keyof CapWidgetEventMap>(
        type: K,
        listener: (this: CapWidgetElement, event: CapWidgetEventMap[K]) => unknown,
        options?: boolean | AddEventListenerOptions,
    ): void;

    // Retained so the element stays assignable to `EventTarget`/`Node`; the overload above
    // is what callers resolve against for Cap's own events.
    addEventListener(
        type: string,
        listener: EventListenerOrEventListenerObject | null,
        options?: boolean | AddEventListenerOptions,
    ): void;

    removeEventListener<K extends keyof CapWidgetEventMap>(
        type: K,
        listener: (this: CapWidgetElement, event: CapWidgetEventMap[K]) => unknown,
        options?: boolean | EventListenerOptions,
    ): void;

    removeEventListener(
        type: string,
        listener: EventListenerOrEventListenerObject | null,
        options?: boolean | EventListenerOptions,
    ): void;
}
