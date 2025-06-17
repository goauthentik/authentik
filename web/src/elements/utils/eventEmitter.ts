import {
    AbstractLitElementConstructor,
    ConstructorWithMixin,
    LitElementConstructor,
    createMixin,
} from "@goauthentik/elements/types";
import { CustomEventDetail, isCustomEvent } from "@goauthentik/elements/utils/customEvents";

export interface CustomEventEmitterMixin<EventType extends string = string> {
    dispatchCustomEvent<D extends CustomEventDetail>(
        eventType: EventType,
        detail?: D,
        eventInit?: EventInit,
    ): void;
}

export function CustomEmitterElement<
    EventType extends string = string,
    T extends AbstractLitElementConstructor = AbstractLitElementConstructor,
>(SuperClass: T) {
    abstract class CustomEventEmmiter
        extends SuperClass
        implements CustomEventEmitterMixin<EventType>
    {
        public dispatchCustomEvent<D extends CustomEventDetail>(
            eventType: string,
            detail: D = {} as D,
            eventInit: EventInit = {},
        ) {
            let normalizedDetail: CustomEventDetail;

            if (detail && typeof detail === "object" && !Array.isArray(detail)) {
                // TODO: Is this destructuring still necessary to shallow copy the object?
                normalizedDetail = { ...detail };
            } else {
                normalizedDetail = detail;
            }

            this.dispatchEvent(
                new CustomEvent(eventType, {
                    composed: true,
                    bubbles: true,
                    ...eventInit,
                    detail: normalizedDetail,
                }),
            );
        }
    }

    return CustomEventEmmiter as unknown as ConstructorWithMixin<
        T,
        CustomEventEmitterMixin<EventType>
    >;
}

type CustomEventListener<D = unknown> = (ev: CustomEvent<D>) => void;
type EventMap<D = unknown> = WeakMap<CustomEventListener<D>, CustomEventListener<D>>;

export interface CustomEventTarget<EventType extends string = string> {
    addCustomListener<D = unknown>(eventType: EventType, handler: CustomEventListener<D>): void;
    removeCustomListener<D = unknown>(eventType: EventType, handler: CustomEventListener<D>): void;
}

/**
 * A mixin that enables Lit Elements to handle custom events in a more straightforward manner.
 *
 * @todo Can we lean on the native `EventTarget` class for this?
 * @category Mixin
 */
export const CustomListenerElement = createMixin<CustomEventTarget>(({ SuperClass }) => {
    return class ListenerElementHandler extends SuperClass implements CustomEventTarget {
        #listenHandlers = new Map<string, EventMap>();

        #getListener<D = unknown>(
            eventType: string,
            handler: CustomEventListener<D>,
        ): CustomEventListener<D> | undefined {
            const internalMap = this.#listenHandlers.get(eventType) as EventMap<D> | undefined;

            return internalMap?.get(handler);
        }

        // For every event NAME, we create a WeakMap that pairs the event handler given to us by the
        // class that uses this method to the custom, wrapped handler we create to manage the types
        // and handlings. If the wrapped handler disappears due to garbage collection, no harm done;
        // meanwhile, this allows us to remove it from the event listeners if it's still around
        // using the original handler's identity as the key.
        //
        #addListener<D = unknown>(
            eventType: string,
            handler: CustomEventListener<D>,
            internalHandler: CustomEventListener<D>,
        ) {
            let internalMap = this.#listenHandlers.get(eventType) as EventMap<D> | undefined;

            if (!internalMap) {
                internalMap = new WeakMap();

                this.#listenHandlers.set(eventType, internalMap as EventMap);
            }

            internalMap.set(handler, internalHandler);
        }

        #removeListener<D = unknown>(eventType: string, listener: CustomEventListener<D>) {
            const internalMap = this.#listenHandlers.get(eventType) as EventMap<D> | undefined;

            if (internalMap) {
                internalMap.delete(listener);
            }
        }

        addCustomListener<D = unknown>(eventType: string, listener: CustomEventListener<D>) {
            const internalHandler = (event: Event) => {
                if (!isCustomEvent<D>(event)) {
                    console.error(
                        `Received a standard event for custom event ${eventType}; event will not be handled.`,
                    );

                    return null;
                }

                return listener(event);
            };

            this.#addListener(eventType, listener, internalHandler);
            this.addEventListener(eventType, internalHandler);
        }

        removeCustomListener<D = unknown>(eventType: string, listener: CustomEventListener<D>) {
            const realHandler = this.#getListener(eventType, listener);

            if (realHandler) {
                this.removeEventListener(
                    eventType,
                    realHandler as EventListenerOrEventListenerObject,
                );
            }

            this.#removeListener<D>(eventType, listener);
        }
    };
});
