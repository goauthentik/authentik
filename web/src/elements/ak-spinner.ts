import { akSpinner, type SpinnerProps } from "./Spinner/Spinner.builder";
import { Spinner } from "./Spinner/Spinner.component";

export { akSpinner, Spinner };
export type { SpinnerProps };

window.customElements.define("ak-spinner", Spinner);

declare global {
    interface HTMLElementTagNameMap {
        "ak-spinner": Spinner;
    }
}
