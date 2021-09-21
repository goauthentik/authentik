import { t } from "@lingui/macro";
import { CSSResult, html, LitElement, TemplateResult } from "lit";
import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";
import { customElement, property } from "lit/decorators";

export enum PFSize {
    Small = "pf-m-sm",
    Medium = "pf-m-md",
    Large = "pf-m-lg",
    XLarge = "pf-m-xl",
}

@customElement("ak-spinner")
export class Spinner extends LitElement {
    @property()
    size: PFSize = PFSize.Medium;

    static get styles(): CSSResult[] {
        return [PFSpinner];
    }

    render(): TemplateResult {
        return html`<span
            class="pf-c-spinner ${this.size.toString()}"
            role="progressbar"
            aria-valuetext="${t`Loading...`}"
        >
            <span class="pf-c-spinner__clipper"></span>
            <span class="pf-c-spinner__lead-ball"></span>
            <span class="pf-c-spinner__tail-ball"></span>
        </span>`;
    }
}
