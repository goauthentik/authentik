import type { SerializableControl } from "@goauthentik/elements/forms/Form";

import { AKElement } from "./Base.js";

/**
 * @class - prototype for all of our hand-made input elements
 *
 * Ensures that the `data-ak-control` property is always set, so that
 * scrapers can find it easily, and adds a corresponding method for
 * extracting the value.
 *
 */
export abstract class AkControlElement<T = string | string[]>
    extends AKElement
    implements SerializableControl<T>
{
    public connectedCallback(): void {
        super.connectedCallback();
        this.dataset.akControl = this.tagName.toLowerCase();
    }

    /**
     * Return the value of the control as a JSON-compatible object.
     *
     * Typically, this is derived from any {@linkcode HTMLInputElement} elements
     * within the control.
     */
    public abstract toJSON(): T;

    public get isValid(): boolean {
        return true;
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
