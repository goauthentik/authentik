import { AkDrawer } from "./ak-drawer.component.js";

export { AkDrawer };

customElements.define("ak-drawer", AkDrawer);

declare global {
    interface HTMLElementTagNameMap {
        "ak-drawer": AkDrawer;
    }
}
