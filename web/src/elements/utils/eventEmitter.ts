import type { LitElement } from "lit";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor<T = object> = new (...args: any[]) => T;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isCustomEvent = (v: any): v is CustomEvent =>
    v instanceof CustomEvent && "detail" in v;

export function CustomEmitterElement<T extends Constructor<LitElement>>(superclass: T) {
    return class EmmiterElementHandler extends superclass {
        dispatchCustomEvent(eventName: string, detail = {}, options = {}) {
            this.dispatchEvent(
                new CustomEvent(eventName, {
                    composed: true,
                    bubbles: true,
                    ...options,
                    detail: {
                        target: this,
                        ...detail,
                    },
                }),
            );
        }
    };
}

export function CustomListenerElement<T extends Constructor<LitElement>>(superclass: T) {
    return class ListenerElementHandler extends superclass {
        addCustomListener(eventName: string, handler: (ev: CustomEvent) => void) {
            this.addEventListener(eventName, (ev: Event) => {
                if (!isCustomEvent(ev)) {
                    console.error(
                        `Received a standard event for custom event ${eventName}; event will not be handled.`,
                    );
                    return;
                }
                handler(ev);
            });
        }
    };
}
