/**
 * @file Event Listener Decorator for LitElement
 */

import type { LitElement } from "lit";

//#region Types

const listenerDecoratorSymbol = Symbol("listener-decorator");
const abortControllerSymbol = Symbol("listener-decorator-abort-controller");

/**
 * Options for the {@linkcode listen} decorator.
 */
export interface ListenDecoratorOptions extends AddEventListenerOptions {
    /**
     * The target to attach the event listener to.
     *
     * @default window
     */
    target?: EventTarget;
}

/**
 * Internal store for the {@linkcode listen} decorator.
 */
interface ListenDecoratorStore {
    propToEventName: Map<PropertyKey, keyof WindowEventMap>;
    propToOptions: Map<PropertyKey, ListenDecoratorOptions>;
}

/**
 * Mixin interface for elements using the {@linkcode listen} decorator.
 */
interface ListenerMixin extends LitElement {
    [listenerDecoratorSymbol]?: ListenDecoratorStore;
    [abortControllerSymbol]?: AbortController | null;
}

/**
 * A type representing an Event constructor.
 */
export type EventConstructor<K extends keyof WindowEventMap = keyof WindowEventMap> = {
    eventName: K;
} & (new (...args: never[]) => WindowEventMap[K]);

// #endregion

//#region Utilities

/**
 * Type guard for EventListener-like objects.
 *
 * @remarks
 *
 * Type-safety for this is limited due to the dynamic nature of event listeners.
 */
function isEventListenerLike(input: unknown): input is EventListenerOrEventListenerObject {
    if (!input) return false;
    if (typeof input === "function") return true;

    return typeof (input as EventListenerObject).handleEvent === "function";
}

/**
 * Registers the connected and disconnected callbacks to manage event listeners.
 *
 * @see {@linkcode listen} for usage.
 *
 * @param target The target class to register the callbacks on.
 * @internal
 */
function registerEventCallbacks<T extends ListenerMixin>(target: T): ListenDecoratorStore {
    const { connectedCallback, disconnectedCallback } = target;

    // Inherit parent's listeners, if they exist.
    const parentData = target[listenerDecoratorSymbol];

    const propToEventName = new Map(parentData?.propToEventName || []);
    const propToOptions = new Map(parentData?.propToOptions || []);

    // Wrap connectedCallback to register event listeners, with AbortController for easy removal.
    target.connectedCallback = function connectedCallbackWrapped(this: T) {
        connectedCallback.call(this);

        const abortController = new AbortController();
        this[abortControllerSymbol] = abortController;

        // Register all listeners
        for (const [propKey, eventType] of propToEventName) {
            const { target = window, ...options } = propToOptions.get(propKey) || {};
            const listener = this[propKey as keyof T];

            if (!listener) {
                throw new TypeError(
                    `Listener method "${String(propKey)}" not found on component. Was it re-assigned or removed?`,
                );
            }

            if (!isEventListenerLike(listener)) {
                throw new TypeError(
                    `Listener "${String(
                        propKey,
                    )}" is not a valid event listener. It must be a function or an object with a handleEvent method.`,
                );
            }

            target.addEventListener(eventType, listener, {
                ...options,
                signal: abortController.signal,
            });
        }
    };

    // Wrap disconnectedCallback to invoke the abort controller, removing all listeners.
    target.disconnectedCallback = function disconnectedCallbackWrapped(this: T) {
        disconnectedCallback.call(this);

        this[abortControllerSymbol]?.abort();
        this[abortControllerSymbol] = null;
    };

    target[listenerDecoratorSymbol] = {
        propToEventName,
        propToOptions,
    };

    return target[listenerDecoratorSymbol];
}

//#endregion

//#region Decorator

/**
 * Type for the decorator.
 *
 * @see {@linkcode listen} for usage.
 */
export type ListenDecorator = <T extends LitElement>(target: T, propertyKey: string) => void;

/**
 * Adds an event listener to the `window` object that is automatically
 * removed when the element is disconnected.
 *
 * @param EventConstructor The event constructor to listen for.
 * @param listener The event listener callback.
 * @param options Additional options for `addEventListener`.
 */
export function listen<K extends keyof WindowEventMap>(
    EventConstructor: EventConstructor<K>,
    options?: ListenDecoratorOptions,
): ListenDecorator;
/**
 * Adds an event listener to the `window` object that is automatically
 * removed when the element is disconnected.
 *
 * @param type The event type to listen for.
 * @param listener The event listener callback.
 * @param options Additional options for `addEventListener`.
 */
export function listen<K extends keyof WindowEventMap>(
    type: K,
    options?: ListenDecoratorOptions,
): ListenDecorator;
/**
 * Adds an event listener to the `window` object that is automatically
 * removed when the element is disconnected.
 *
 * @param type The event type or constructor to listen for.
 * @param listener The event listener callback.
 * @param options Additional options for `addEventListener`.
 */
export function listen<K extends keyof WindowEventMap>(
    type: K | EventConstructor<K>,
    options: ListenDecoratorOptions = {},
): ListenDecorator {
    const eventType = typeof type === "function" ? type.eventName : type;

    return <T extends ListenerMixin>(target: T, key: string) => {
        const store = Object.hasOwn(target, listenerDecoratorSymbol)
            ? target[listenerDecoratorSymbol]!
            : registerEventCallbacks(target);

        store.propToEventName.set(key, eventType);
        store.propToOptions.set(key, options);
    };
}

//#endregion
