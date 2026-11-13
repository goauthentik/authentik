import {
    akStructuredView,
    type StructuredViewProps,
} from "./StructuredView/StructuredView.builder";
import { StructuredView } from "./StructuredView/StructuredView.component";

export { akStructuredView, StructuredView };
export type { StructuredViewProps };

window.customElements.define("ak-structured-view", StructuredView);

declare global {
    interface HTMLElementTagNameMap {
        "ak-structured-view": StructuredView;
    }
}
