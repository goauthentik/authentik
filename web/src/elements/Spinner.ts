import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import SpinnerStyle from "@patternfly/patternfly/components/Spinner/spinner.css";

export enum SpinnerSize {
    Small = "pf-m-sm",
    Medium = "pf-m-md",
    Large = "pf-m-lg",
    XLarge = "pf-m-xl",
}

@customElement("ak-spinner")
export class Spinner extends LitElement {
    @property()
    size: SpinnerSize = SpinnerSize.Medium;

    static get styles(): CSSResult[] {
        return [SpinnerStyle];
    }

    render(): TemplateResult {
        return html`<span
                class="pf-c-spinner ${this.size.toString()}"
                role="progressbar"
                aria-valuetext="${gettext("Loading...")}">
                <span class="pf-c-spinner__clipper"></span>
                <span class="pf-c-spinner__lead-ball"></span>
                <span class="pf-c-spinner__tail-ball"></span>
            </span>`;
    }

}
