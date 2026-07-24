/**
 * @file Barrel file and default registry ('ak-status-label') for the StatusLabel component
 */

import { akStatusLabel, StatusLabel, type StatusLabelProps } from "./StatusLabel_impl/StatusLabel";

export { akStatusLabel, StatusLabel };
export type { StatusLabelProps };

window.customElements.define("ak-status-label", StatusLabel);

declare global {
    interface HTMLElementTagNameMap {
        "ak-status-label": StatusLabel;
    }
}
