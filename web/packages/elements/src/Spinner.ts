import { AKElement } from "@goauthentik/elements/Base.js";
import { registerCustomElement } from "@goauthentik/elements/utils/customElement.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";

export enum PFSize {
    Small = "pf-m-sm",
    Medium = "pf-m-md",
    Large = "pf-m-lg",
    XLarge = "pf-m-xl",
}

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

registerCustomElement("ak-spinner", Spinner);
