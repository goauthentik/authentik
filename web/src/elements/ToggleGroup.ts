import { ToggleGroup } from "./ToggleGroup_impl/ToggleGroup";

export { ToggleGroup };

window.customElements.define("ak-toggle-group", ToggleGroup);

declare global {
    interface HTMLElementTagNameMap {
        "ak-toggle-group": ToggleGroup;
    }
}
