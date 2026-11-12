import { akIcon, type IconProps } from "#elements/Icon/Icon.builder";
import { Icon } from "#elements/Icon/Icon.component";

export { akIcon, Icon, type IconProps };

window.customElements.define("ak-icon", Icon);

declare global {
    interface HTMLElementTagNameMap {
        "ak-icon": Icon;
    }
}
