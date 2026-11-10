import { akIcon, IconProps } from "./ak-icon.builder.js";
import { Icon } from "./ak-icon.component.js";

export { akIcon, Icon, type IconProps };

window.customElements.define("ak-icon", Icon);

declare global {
    interface HTMLElementTagNameMap {
        "ak-icon": Icon;
    }
}
