import { type RapiDoc } from "rapidoc";

declare global {
    interface HTMLElementTagNameMap {
        "rapi-doc": RapiDoc;
    }
}
