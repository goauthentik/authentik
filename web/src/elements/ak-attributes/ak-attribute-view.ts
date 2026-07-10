import { AkAttributeView } from "./ak-attribute-view.component.js";

export { AkAttributeView };

window.customElements.define("ak-attribute-view", AkAttributeView);

declare global {
    interface HTMLElementTagNameMap {
        "ak-attribute-view": AkAttributeView;
    }
}
