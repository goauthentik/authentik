import { AKElement } from "./Base";

/**
 * @class - prototype for all of our hand-made input elements
 *
 * Ensures that the `data-ak-control` property is always set, so that
 * scrapers can find it easily, and adds a corresponding method for
 * extracting the value.
 *
 */
export class AkControlElement extends AKElement {
    constructor() {
        super();
        this.dataset.akControl = "true";
    }

    json() {
        throw new Error("Controllers using this protocol must override this method");
    }
}
