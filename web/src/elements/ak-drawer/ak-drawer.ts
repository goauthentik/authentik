import { Drawer } from "./ak-drawer.component.js";

export { Drawer };

window.customElements.define("ak-drawer", Drawer);

declare global {
    interface HTMLElementTagNameMap {
        "ak-drawer": Drawer;
    }
}
