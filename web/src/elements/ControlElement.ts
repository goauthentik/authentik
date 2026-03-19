import { AKElement } from "#elements/Base";

/**
 * @class - prototype for all of our hand-made input elements
 *
 * Ensures that the `data-ak-control` property is always set, so that
 * scrapers can find it easily, and adds a corresponding method for
 * extracting the value.
 *
 */
export class AKControlElement<T = string | string[]> extends AKElement {
    constructor() {
        super();
        this.dataset.akControl = "true";
    }

    /**
     * @deprecated Rename to `toJSON`
     */
    public json(): T {
        throw new Error("Controllers using this protocol must override this method");
    }

    /**
     * Convert the value of the control to a JSON-serializable format.
     */
    public toJSON(): T {
        return this.json();
    }

    public get isValid(): boolean {
        return true;
    }
}

export function isControlElement(element: Element | HTMLElement): element is AKControlElement {
    if (!(element instanceof HTMLElement)) return false;

    if (element instanceof AKControlElement) return true;

    return element.hasAttribute("data-ak-control");
}

declare global {
    interface HTMLElementTagNameMap {
        "[data-ak-control]": AKControlElement;
    }
}
