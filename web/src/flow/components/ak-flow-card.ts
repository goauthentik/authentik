import "#elements/EmptyState";

import { AKElement } from "#elements/Base";

import { ChallengeTypes } from "@goauthentik/api";

import { css, CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * @element ak-flow-card
 * @class FlowCard
 * @slot title - Title of the card, optional, when not set uses the flow title
 * @slot - Main body of the card
 * @slot footer - Footer links, optional
 * @slot footer-band - Band in the footer, option
 *
 */
@customElement("ak-flow-card")
export class FlowCard extends AKElement {
    @property({ type: Object })
    challenge?: ChallengeTypes;

    @property({ type: Boolean })
    loading = false;

    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFTitle,
        css`
            .pf-c-login__main-footer {
                display: block;
            }

            slot[name="footer-band"] {
                text-align: center;
                background-color: var(--pf-c-login__main-footer-band--BackgroundColor);
                padding: 0;
                margin-top: 1em;
            }
            .pf-c-login__main-body:last-child {
                padding-bottom: calc(var(--pf-c-login__main-header--PaddingTop) * 1.2);
            }
        `,
    ];

    render() {
        let inner = html`<slot></slot>`;
        if (!this.challenge || this.loading) {
            inner = html`<ak-empty-state loading default-label></ak-empty-state>`;
        }
        // No title if the challenge doesn't provide a title and no custom title is set
        let title = undefined;
        if (this.hasSlotted("title")) {
            title = html`<h1 class="pf-c-title pf-m-3xl"><slot name="title"></slot></h1>`;
        } else if (this.challenge?.flowInfo?.title) {
            title = html`<h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo.title}</h1>`;
        }
        return html`${title
                ? html`<header class="pf-c-login__main-header">${title}</header>`
                : nothing}
            <div class="pf-c-login__main-body">${inner}</div>
            ${this.hasSlotted("footer") || this.hasSlotted("footer-band")
                ? html`<footer class="pf-c-login__main-footer">
                      ${this.hasSlotted("footer") ? html`<slot name="footer"></slot>` : nothing}
                      ${this.hasSlotted("footer-band")
                          ? html`<slot
                                name="footer-band"
                                class="pf-c-login__main-footer-band"
                            ></slot>`
                          : nothing}
                  </footer>`
                : nothing}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-card": FlowCard;
    }
}
