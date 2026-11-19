import Styles from "./Spinner.styles";

import { msg } from "@lit/localize";
import { html, LitElement } from "lit";
import { property } from "lit/decorators.js";

export type SpinnerSize = "sm" | "md" | "lg" | "xl";

export class Spinner extends LitElement {
    static styles = [Styles];

    @property({ type: String, reflect: true })
    public size: SpinnerSize = "md";

    render() {
        return html`<span part="spinner">
            <span part="clipper"></span>
            <span part="leading-ball"></span>
            <span part="trailing-ball"></span>
            <slot></slot>
        </span>`;
    }

    firstUpdated() {
        if (!this.hasAttribute("role")) {
            this.setAttribute("role", "progressbar");
        }

        if (!this.hasAttribute("aria-valuetext")) {
            this.setAttribute("aria-valuetext", msg("Loading..."));
        }
    }
}
