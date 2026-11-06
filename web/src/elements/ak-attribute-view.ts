import { AkAttributeView } from "./AttributeView/AttributeView.component";

export { AkAttributeView };

window.customElements.define("ak-attribute-view", AkAttributeView);

declare global {
    interface HTMLElementTagNameMap {
        "ak-attribute-view": AkAttributeView;
    }
}
