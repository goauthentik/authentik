import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { ifDefined } from "lit-html/directives/if-defined";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import AKGlobal from "../../authentik.css";

@customElement("ak-aggregate-card")
export class AggregateCard extends LitElement {
    @property()
    icon?: string;

    @property()
    header?: string;

    @property()
    headerLink?: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFFlex, AKGlobal].concat([css`
            .pf-c-card.pf-c-card-aggregate {
                height: 100%;
            }
            .center-value {
                font-size: var(--pf-global--icon--FontSize--lg);
                text-align: center;
                color: var(--pf-global--Color--100);
            }
            .subtext {
                font-size: var(--pf-global--FontSize--sm);
            }
        `]);
    }

    renderInner(): TemplateResult {
        return html`<slot></slot>`;
    }

    renderHeaderLink(): TemplateResult {
        return html`${this.headerLink ? html`<a href="${this.headerLink}">
            <i class="fa fa-external-link-alt"> </i>
        </a>` : ""}`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card pf-c-card-aggregate">
            <div class="pf-c-card__header pf-l-flex pf-m-justify-content-space-between">
                <div class="pf-c-card__header-main">
                    <i class="${ifDefined(this.icon)}"></i> ${this.header ? gettext(this.header) : ""}
                </div>
                ${this.renderHeaderLink()}
            </div>
            <div class="pf-c-card__body center-value">
                ${this.renderInner()}
            </div>
        </div>`;
    }

}
