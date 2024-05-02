import { AKElement } from "./Base";

export class AkControlElement extends AKElement {
    constructor() {
        super();
        this.dataset.akControl = "true";
    }

    json() {
        throw new Error("Must be implemented in inheriting class.");
    }
}
