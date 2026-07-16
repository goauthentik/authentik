/**
 * @file Barrel file and default registry ('ak-spinner') for the Spinner component
 */

import { akSpinner, Spinner, type SpinnerProps } from "./Spinner_impl/Spinner";

export { akSpinner, Spinner };
export type { SpinnerProps };

window.customElements.define("ak-spinner", Spinner);

declare global {
    interface HTMLElementTagNameMap {
        "ak-spinner": Spinner;
    }
}
