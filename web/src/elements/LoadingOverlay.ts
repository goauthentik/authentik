import { css, CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import { PFSize } from "./Spinner";

@customElement("ak-loading-overlay")
export class LoadingOverlay extends LitElement {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            css`
                :host {
                    display: flex;
                    height: 100%;
                    width: 100%;
                    justify-content: center;
                    align-items: center;
                    position: absolute;
                    background-color: var(--pf-global--BackgroundColor--dark-transparent-100);
                    z-index: 1;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<ak-spinner size=${PFSize.XLarge}></ak-spinner>`;
    }
}
