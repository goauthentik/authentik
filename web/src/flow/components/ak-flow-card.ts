import "#elements/EmptyState";

import Styles from "./ak-flow-card.css";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import { ChallengeTypes } from "@goauthentik/api";

import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

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
    role = "presentation";

    @property({ type: Object })
    challenge?: ChallengeTypes;

    @property({ type: Boolean })
    loading = false;

    static styles: CSSResult[] = [PFLogin, PFTitle, Styles];

    render() {
        let inner = html`<slot></slot>`;
        if (!this.challenge || this.loading) {
            inner = html`<ak-empty-state loading default-label></ak-empty-state>`;
        }
        // No title if the challenge doesn't provide a title and no custom title is set
        let title: null | SlottedTemplateResult = null;
        if (this.hasSlotted("title")) {
            title = html`<h1 class="pf-c-title pf-m-3xl"><slot name="title"></slot></h1>`;
        } else if (this.challenge?.flowInfo?.title) {
            title = html`<h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo.title}</h1>`;
        }
        const footer = this.hasSlotted("footer") ? html`<slot name="footer"></slot>` : null;
        const footerBand = this.hasSlotted("footer-band")
            ? html`<slot name="footer-band"></slot>`
            : null;

        return html`${title ? html`<div class="pf-c-login__main-header">${title}</div>` : null}
            <div class="pf-c-login__main-body">${inner}</div>
            ${footer || footerBand
                ? html`<div class="pf-c-login__main-footer">${footer}${footerBand}</div>`
                : null}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-card": FlowCard;
    }
}
