import { AKElement } from "#elements/Base";

/**
 * @class - prototype for all of our hand-made input elements
 *
 * Ensures that the `data-ak-control` property is always set, so that
 * scrapers can find it easily, and adds a corresponding method for
 * extracting the value.
 *
 */
export class AkControlElement<T = string | string[]> extends AKElement {
    constructor() {
        super();
        this.dataset.akControl = "true";
    }

    json(): T {
        throw new Error("Controllers using this protocol must override this method");
    }

    get toJson(): T {
        return this.json();
    }

    get isValid(): boolean {
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
