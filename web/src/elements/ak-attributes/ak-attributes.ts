import { AkAttributes } from "./ak-attributes.component.js";

export { AkAttributes };

window.customElements.define("ak-attributes", AkAttributes);

declare global {
    interface HTMLElementTagNameMap {
        "ak-attributes": AkAttributes;
    }
}
