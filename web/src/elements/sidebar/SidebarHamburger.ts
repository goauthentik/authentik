import { css, CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../common/styles";

@customElement("ak-sidebar-hamburger")
export class SidebarHamburger extends LitElement {

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(
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
