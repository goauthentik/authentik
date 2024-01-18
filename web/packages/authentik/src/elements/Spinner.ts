import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";

export enum PFSize {
    Small = "pf-m-sm",
    Medium = "pf-m-md",
    Large = "pf-m-lg",
    XLarge = "pf-m-xl",
}

@customElement("ak-spinner")
export class Spinner extends AKElement {
    @property()
    size: PFSize = PFSize.Medium;

    static get styles(): CSSResult[] {
        return [PFSpinner];
    }

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
