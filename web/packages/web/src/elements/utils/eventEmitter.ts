import type { LitElement } from "lit";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor<T = object> = new (...args: any[]) => T;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isCustomEvent = (v: any): v is CustomEvent =>
    v instanceof CustomEvent && "detail" in v;

export function CustomEmitterElement<T extends Constructor<LitElement>>(superclass: T) {
    return class EmmiterElementHandler extends superclass {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        dispatchCustomEvent(eventName: string, detail: any = {}, options = {}) {
            const fullDetail =
                typeof detail === "object" && !Array.isArray(detail)
                    ? {
                          target: this,
                          ...detail,
                      }
                    : detail;
            this.dispatchEvent(
                new CustomEvent(eventName, {
                    composed: true,
                    bubbles: true,
                    ...options,
                    detail: fullDetail,
                }),
            );
        }
    };
}

/**
 * Mixin that enables Lit Elements to handle custom events in a more straightforward manner.
 *
 */

// This is a neat trick: this static "class" is just a namespace for these unique symbols. Because
// of all the constraints on them, they're legal field names in Typescript objects! Which means that
// we can use them as identifiers for internal references in a Typescript class with absolutely no
// risk that a future user who wants a name like 'addHandler' or 'removeHandler' will override any
// of those, either in this mixin or in any class that this is mixed into, past or present along the
// chain of inheritance.

class HK {
    public static readonly listenHandlers: unique symbol = Symbol();
    public static readonly addHandler: unique symbol = Symbol();
    public static readonly removeHandler: unique symbol = Symbol();
    public static readonly getHandler: unique symbol = Symbol();
}

type EventHandler = (ev: CustomEvent) => void;
type EventMap = WeakMap<EventHandler, EventHandler>;

export function CustomListenerElement<T extends Constructor<LitElement>>(superclass: T) {
    return class ListenerElementHandler extends superclass {
        private [HK.listenHandlers] = new Map<string, EventMap>();

        private [HK.getHandler](eventName: string, handler: EventHandler) {
            const internalMap = this[HK.listenHandlers].get(eventName);
            return internalMap ? internalMap.get(handler) : undefined;
        }

        // For every event NAME, we create a WeakMap that pairs the event handler given to us by the
        // class that uses this method to the custom, wrapped handler we create to manage the types
        // and handlings. If the wrapped handler disappears due to garbage collection, no harm done;
        // meanwhile, this allows us to remove it from the event listeners if it's still around
        // using the original handler's identity as the key.
        //
        private [HK.addHandler](
            eventName: string,
            handler: EventHandler,
            internalHandler: EventHandler,
        ) {
            if (!this[HK.listenHandlers].has(eventName)) {
                this[HK.listenHandlers].set(eventName, new WeakMap());
            }
            const internalMap = this[HK.listenHandlers].get(eventName);
            if (internalMap) {
                internalMap.set(handler, internalHandler);
            }
        }

        private [HK.removeHandler](eventName: string, handler: EventHandler) {
            const internalMap = this[HK.listenHandlers].get(eventName);
            if (internalMap) {
                internalMap.delete(handler);
            }
        }

        addCustomListener(eventName: string, handler: EventHandler) {
            const internalHandler = (ev: Event) => {
                if (!isCustomEvent(ev)) {
                    console.error(
                        `Received a standard event for custom event ${eventName}; event will not be handled.`,
                    );
                    return;
                }
                handler(ev);
            };
            this[HK.addHandler](eventName, handler, internalHandler);
            this.addEventListener(eventName, internalHandler);
        }

        removeCustomListener(eventName: string, handler: EventHandler) {
            const realHandler = this[HK.getHandler](eventName, handler);
            if (realHandler) {
                this.removeEventListener(
                    eventName,
                    realHandler as EventListenerOrEventListenerObject,
                );
            }
            this[HK.removeHandler](eventName, handler);
        }
    };
}
