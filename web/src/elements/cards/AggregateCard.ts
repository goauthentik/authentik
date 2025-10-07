import { SlottedTemplateResult } from "../types";

import { AKElement } from "#elements/Base";

import { css, CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface IAggregateCard {
    icon?: string | null;
    label?: string | null;
    headerLink?: string | null;
    subtext?: string | null;
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
    @property({ type: String })
    public icon: string | null = null;

    /**
     * The title of the card.
     *
     * @attr
     */
    @property({ type: String })
    public label: string | null = null;

    /**
     * If this is non-empty, a link icon will be shown in the upper-right corner of the card.
     *
     * @attr
     */
    @property({ type: String })
    public headerLink: string | null = null;

    /**
     * If this is non-empty, a small-text footer will be shown at the bottom of the card
     *
     * @attr
     */
    @property({ type: String })
    public subtext: string | null = null;

    static styles: CSSResult[] = [
        PFBase,
        PFCard,
        PFFlex,
        css`
            .pf-c-card {
                container-type: inline-size;
            }

            .pf-c-card.pf-c-card-aggregate {
                height: 100%;
            }
            .pf-c-card__header {
                padding: var(--pf-global--spacer--md);
            }
            .pf-c-card__title {
                display: flex;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
                flex: 1 1 auto;

                @container (width < 200px) {
                    font-size: var(--pf-global--FontSize--sm);
                }
            }

            .subtext {
                margin-top: var(--pf-global--spacer--sm);
                font-size: var(--pf-global--FontSize--sm);
            }
            .pf-c-card__body {
                overflow-x: auto;
                padding-left: calc(var(--pf-c-card--child--PaddingLeft) / 2);
                padding-right: calc(var(--pf-c-card--child--PaddingRight) / 2);
            }
            .status-container {
                font-size: var(--pf-global--icon--FontSize--lg);
                text-align: center;

                @container (width < 200px) {
                    font-size: var(--pf-global--icon--FontSize--md);
                }

                .status-heading {
                    display: flex;
                    gap: var(--pf-global--spacer--sm);
                    justify-content: center;
                    align-items: baseline;
                }
            }
            .pf-c-card__header,
            .pf-c-card__title,
            .pf-c-card__body,
            .pf-c-card__footer {
                padding-bottom: 0;
            }

            .pf-c-card__footer {
                min-height: 1ex;
            }
        `,
    ];

    renderInner(): SlottedTemplateResult {
        return html`<slot></slot>`;
    }

    renderHeaderLink(): SlottedTemplateResult {
        if (!this.headerLink) {
            return nothing;
        }

        return html`<a href="${this.headerLink}">
            <i aria-hidden="true" class="fa fa-link"></i>
        </a>`;
    }

    render(): SlottedTemplateResult {
        return html`<section
            class="pf-c-card pf-c-card-aggregate"
            aria-labelledby="card-title"
            part="card"
        >
            <header
                part="card-header"
                class="pf-c-card__header pf-l-flex pf-m-justify-content-space-between"
            >
                <h1 part="card-title" class="pf-c-card__title" id="card-title">
                    ${this.icon ? html`<i aria-hidden="true" class="${this.icon}"></i>` : nothing}
                    <span>${this.label || nothing}</span>${this.renderHeaderLink()}
                </h1>
            </header>
            <div part="card-body" class="pf-c-card__body">
                ${this.renderInner()}
                ${this.subtext
                    ? html`<p part="card-subtext" class="subtext">${this.subtext}</p>`
                    : nothing}
            </div>
            <div class="pf-c-card__footer"></div>
        </section>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-aggregate-card": AggregateCard;
    }
}
