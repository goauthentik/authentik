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

    @property({ type: Boolean })
    loading = false;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFTitle,
            css`
                slot[name="footer"],
                slot[name="footer-band"] {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    flex-basis: 100%;
                }
                slot[name="footer-band"] {
                    text-align: center;
                    background-color: var(--pf-c-login__main-footer-band--BackgroundColor);
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
                ${this.hasSlotted("footer")
                    ? html`<slot name="footer"></slot>`
                    : html`<ul class="pf-c-login__main-footer-links"></ul>`}
                <slot name="footer-band"></slot>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-card": FlowCard;
    }
}
