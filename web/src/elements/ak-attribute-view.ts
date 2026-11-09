import { akAttributeView, type AttributeViewProps } from "./AttributeView/AttributeView.builder";
import { AkAttributeView } from "./AttributeView/AttributeView.component";

export { akAttributeView, AkAttributeView };
export type { AttributeViewProps };

window.customElements.define("ak-attribute-view", AkAttributeView);

declare global {
    interface HTMLElementTagNameMap {
        "ak-attribute-view": AkAttributeView;
    }
}
