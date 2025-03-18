import { AKElement } from "@goauthentik/elements/Base";
import { SlottedTemplateResult } from "@goauthentik/elements/types";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface IAggregateCard {
    icon?: string;
    header?: string;
    headerLink?: string;
    subtext?: string;
    leftJustified?: boolean;
}

/**
 * class AggregateCard
 * element ak-aggregate-card
 *
 * @slot - The main content of the card
 *
 * Card component with a specific layout for quick informational blurbs
 */
@customElement("ak-aggregate-card")
export class AggregateCard extends AKElement implements IAggregateCard {
    /**
     * If this contains an `fa-` style string, the FontAwesome icon specified will be shown next to
     * the header.
     *
     * @attr
     */
    @property()
    icon?: string;

    /**
     * The title of the card.
     *
     * @attr
     */
    @property()
    header?: string;

    /**
     * If this is non-empty, a link icon will be shown in the upper-right corner of the card.
     *
     * @attr
     */
    @property()
    headerLink?: string;

    /**
     * If this is non-empty, a small-text footer will be shown at the bottom of the card
     *
     * @attr
     */
    @property()
    subtext?: string;

    /**
     * If this is set, the contents of the card will be left-justified; otherwise they will be
     * centered by default.
     *
     * @attr
     */
    @property({ type: Boolean, attribute: "left-justified" })
    leftJustified = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFFlex].concat([
            css`
                .pf-c-card.pf-c-card-aggregate {
                    height: 100%;
                }
                .pf-c-card__header {
                    flex-wrap: nowrap;
                }
                .center-value {
                    font-size: var(--pf-global--icon--FontSize--lg);
                    text-align: center;
                }
                .subtext {
                    margin-top: var(--pf-global--spacer--sm);
                    font-size: var(--pf-global--FontSize--sm);
                }
                .pf-c-card__body {
                    overflow-x: scroll;
                    padding-left: calc(var(--pf-c-card--child--PaddingLeft) / 2);
                    padding-right: calc(var(--pf-c-card--child--PaddingRight) / 2);
                }
                .pf-c-card__header,
                .pf-c-card__title,
                .pf-c-card__body,
                .pf-c-card__footer {
                    padding-bottom: 0;
                }

                .pf-c-card {
                    --pf-c-card__title--FontSize: var(--pf-global--FontSize--xs);
                    --pf-c-card--child--PaddingLeft: var(--pf-global--spacer--md);
                    --pf-c-card--child--PaddingRight: var(--pf-global--spacer--md);
                }
            `,
        ]);
    }

    renderInner(): SlottedTemplateResult {
        return html`<slot></slot>`;
    }

    renderHeaderLink() {
        if (!this.headerLink) return nothing;

        return html`<a href="${this.headerLink}">
            <i class="fa fa-link"></i>
        </a>`;
    }

    renderHeader(): SlottedTemplateResult {
        return this.header ? html`${this.header}` : nothing;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card pf-c-card-aggregate">
            <div class="pf-c-card__header pf-l-flex pf-m-justify-content-space-between">
                <div class="pf-c-card__title">
                    ${this.icon
                        ? html`<i class="${ifDefined(this.icon)}"></i>&nbsp;`
                        : nothing}${this.renderHeader()}
                </div>
                ${this.renderHeaderLink()}
            </div>
            <div class="pf-c-card__body ${this.leftJustified ? "" : "center-value"}">
                ${this.renderInner()}
                ${this.subtext ? html`<p class="subtext">${this.subtext}</p>` : nothing}
            </div>
            <div class="pf-c-card__footer">&nbsp;</div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-aggregate-card": AggregateCard;
    }
}
