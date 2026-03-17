import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";

@customElement("ak-spinner")
export class Spinner extends AKElement {
    @property()
    size: PFSize = PFSize.Medium;

    static styles: CSSResult[] = [PFSpinner];

    render(): TemplateResult {
        return html`<span
            class="pf-c-spinner ${this.size.toString()}"
            role="progressbar"
            aria-valuetext="${msg("Loading...")}"
        >
            <span class="pf-c-spinner__clipper"></span>
            <span class="pf-c-spinner__lead-ball"></span>
            <span class="pf-c-spinner__tail-ball"></span>
        </span>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-spinner": Spinner;
    }
}
