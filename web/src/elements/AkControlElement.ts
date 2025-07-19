import { AKElement } from "#elements/Base";

/**
 * @class - prototype for all of our hand-made input elements
 *
 * Ensures that the `data-ak-control` property is always set, so that
 * scrapers can find it easily, and adds a corresponding method for
 * extracting the value.
 *
 */
export abstract class AkControlElement<T = string | string[]> extends AKElement {
    constructor() {
        super();
        // TODO: Move this to connectedCallback.
        this.dataset.akControl = "true";
    }

    /**
     * @abstract
     * @protected
     */
    public json(): T {
        throw new Error("Controllers using this protocol must override this method");
    }

    /**
     * The JSON representation of the control.
     *
     * @todo rename to `toJSON` to support implicit casting to JSON.
     */
    public get toJson(): T {
        return this.json();
    }

    public get isValid(): boolean {
        return true;
    }
}

export function isControlElement(element: Element | HTMLElement): element is AkControlElement {
    if (!(element instanceof HTMLElement)) return false;

    if (element instanceof AkControlElement) return true;

    return "dataset" in element && element.dataset.akControl === "true";
}

declare global {
    interface HTMLElementTagNameMap {
        "[data-ak-control]": AkControlElement;
    }
}

/**
 * Serializes a collection of form elements into a JSON object.
 */
export function formatFormElementAsJSON<T = Record<string, string>>(
    inputs: Iterable<HTMLInputElement> = [],
): T {
    const record = Object.fromEntries(
        Array.from(inputs, (control) => [control.name, control.value]),
    );

    return record as T;
}
