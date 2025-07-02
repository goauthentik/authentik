import { AKElement } from "#elements/Base";
import "@goauthentik/elements/EmptyState";

import { CSSResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ChallengeTypes } from "@goauthentik/api";

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

    @property({type: Boolean})
    loading = false;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFTitle,
            css`
                /* login page's icons */
                .pf-c-login__main-footer-links-item button {
                    background-color: transparent;
                    border: 0;
                    display: flex;
                    align-items: stretch;
                }
                .pf-c-login__main-footer-links-item img {
                    fill: var(--pf-c-login__main-footer-links-item-link-svg--Fill);
                    width: 100px;
                    max-width: var(--pf-c-login__main-footer-links-item-link-svg--Width);
                    height: 100%;
                    max-height: var(--pf-c-login__main-footer-links-item-link-svg--Height);
                }
            `,
        ];
    }

    render() {
        if (!this.challenge || this.loading) {
            return html`<ak-empty-state loading default-label></ak-empty-state>
                <footer class="pf-c-login__main-footer">
                    <ul class="pf-c-login__main-footer-links"></ul>
                </footer>`;
        }
        // No title if the challenge doesn't provide a title and no custom title is set
        let title = undefined;
        if (this.hasSlotted("title")) {
            title = html`<h1 class="pf-c-title pf-m-3xl"><slot name="title"></slot></h1>`;
        } else if (this.challenge.flowInfo?.title) {
            title = html`<h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo.title}</h1>`;
        }
        return html`${title
                ? html`<header class="pf-c-login__main-header">${title}</header>`
                : nothing}
            <div class="pf-c-login__main-body">
                <slot></slot>
            </div>
            <footer class="pf-c-login__main-footer">
                <slot name="footer">
                    <ul class="pf-c-login__main-footer-links"></ul>
                </slot>
                <slot name="footer-band"></slot>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-card": FlowCard;
    }
}
