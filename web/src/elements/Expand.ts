import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../common/styles";

@customElement("ak-expand")
export class Expand extends LitElement {

    @property({ type: Boolean })
    expanded = false;

    @property()
    textOpen = "Show less";

    @property()
    textClosed = "Show more";

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    render(): TemplateResult {
        console.log(this.expanded);
        return html`<div class="pf-c-expandable-section ${this.expanded ? "pf-m-expanded" : ""}">
            <button type="button" class="pf-c-expandable-section__toggle" aria-expanded="${this.expanded}" @click=${() => {
                this.expanded = !this.expanded;
            }}>
                <span class="pf-c-expandable-section__toggle-icon">
                    <i class="fas fa-angle-right" aria-hidden="true"></i>
                </span>
                <span class="pf-c-expandable-section__toggle-text">${gettext(this.expanded ? this.textOpen : this.textClosed)}</span>
            </button>
            <slot ?hidden=${!this.expanded} class="pf-c-expandable-section__content"></slot>
        </div>`;
    }

}
