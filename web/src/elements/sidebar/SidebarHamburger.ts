import { css, CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import AKGlobal from "../../authentik.css";

@customElement("ak-sidebar-hamburger")
export class SidebarHamburger extends LitElement {

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal].concat(
            css`
                :host {
                    position: absolute;
                    top: var(--pf-c-page__main-section--PaddingTop);
                    right: var(--pf-c-page__main-section--PaddingRight);
                    z-index: 250;
                }
            `
        );
    }

    onClick(): void {
        this.dispatchEvent(
            new CustomEvent("ak-sidebar-toggle", {
                bubbles: true,
                composed: true,
            })
        );
    }

    render(): TemplateResult {
        return html`<button @click=${() => (this.onClick())} class="pf-c-button pf-m-plain" type="button">
            <i class="fas fa-bars" aria-hidden="true"></i>
        </button>`;
    }

}
