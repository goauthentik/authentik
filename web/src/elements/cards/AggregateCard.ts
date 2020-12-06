import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { ifDefined } from "lit-html/directives/if-defined";
import { COMMON_STYLES } from "../../common/styles";

@customElement("ak-aggregate-card")
export class AggregateCard extends LitElement {
    @property()
    icon?: string;

    @property()
    header?: string;

    @property()
    headerLink?: string;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat([css`
            .pf-c-card.pf-c-card-aggregate {
                height: 100%;
            }
            .center-value {
                font-size: var(--pf-global--icon--FontSize--lg);
                text-align: center;
                color: var(--pf-global--Color--100);
            }
        `]);
    }

    renderInner(): TemplateResult {
        return html`<slot></slot>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card pf-c-card-aggregate">
            <div class="pf-c-card__header pf-l-flex pf-m-justify-content-space-between">
                <div class="pf-c-card__header-main">
                    <i class="${ifDefined(this.icon)}"></i> ${this.header ? gettext(this.header) : ""}
                </div>
                ${this.headerLink ? html`<a href="${this.headerLink}">
                    <i class="fa fa-external-link-alt"> </i>
                </a>` : ""}
            </div>
            <div class="pf-c-card__body center-value">
                ${this.renderInner()}
            </div>
        </div>`;
    }

}
