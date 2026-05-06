import { AKElement } from "#elements/Base";
import { FormField } from "#elements/forms/form-associated-element";

/**
 * @class - prototype for all of our hand-made input elements
 *
 * Ensures that the `data-ak-control` property is always set, so that
 * scrapers can find it easily, and adds a corresponding method for
 * extracting the value.
 *
 * @deprecated At some point, in the near future, migrate all form controls to `FormAssociatedElement`
 */
export abstract class AKControlElement<T = string | string[]>
    extends AKElement
    implements FormField<T>
{
    constructor() {
        super();
        this.dataset.akControl = "true";
    }

    public abstract name: string | null;

    /**
     * Convert the value of the control to a JSON-serializable format.
     */
    public abstract toJSON(): T;

    public get valid(): boolean {
        return true;
    }
}

/**
 * Type predicate to determine if an element is a control element, i.e. has the `data-ak-control` attribute or is an instance of `AKControlElement`.
 *
 * @deprecated Use `isFormField` instead, and ensure that your form-associated element implements `FormField`.
 */
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
