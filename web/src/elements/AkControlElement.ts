import type { SerializableControl } from "@goauthentik/elements/forms/Form";

import { AKElement } from "./Base";

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
