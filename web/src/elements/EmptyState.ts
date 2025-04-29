import { PFSize } from "@goauthentik/common/enums.js";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Spinner";
import { type SlottedTemplateResult, type Spread } from "@goauthentik/elements/types";
import { spread } from "@open-wc/lit-helpers";
import { SlotController } from "@patternfly/pfe-core/controllers/slot-controller.js";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface IEmptyState {
    icon?: string;
    loading?: boolean;
    fullHeight?: boolean;
    header?: string;
}

@customElement("ak-empty-state")
export class EmptyState extends AKElement implements IEmptyState {
    @property({ type: String })
    icon = "";

    @property({ type: Boolean })
    loading = false;

    @property({ type: Boolean })
    fullHeight = false;

    @property()
    header?: string;

    slots = new SlotController(this, "header", "body", "primary");

    static get styles() {
        return [
            PFBase,
            PFEmptyState,
            PFTitle,
            css`
                i.pf-c-empty-state__icon {
                    height: var(--pf-global--icon--FontSize--2xl);
                    line-height: var(--pf-global--icon--FontSize--2xl);
                }
            `,
        ];
    }

    render() {
        const showHeader = this.loading || this.slots.hasSlotted("header");
        const header = () =>
            this.slots.hasSlotted("header")
                ? html`<slot name="header"></slot>`
                : html`<span>${msg("Loading")}</span>`;

        return html`<div class="pf-c-empty-state ${this.fullHeight && "pf-m-full-height"}">
            <div class="pf-c-empty-state__content">
                ${this.loading
                    ? html`<div class="pf-c-empty-state__icon">
                          <ak-spinner size=${PFSize.XLarge}></ak-spinner>
                      </div>`
                    : html`<i
                          class="pf-icon fa ${this.icon ||
                          "fa-question-circle"} pf-c-empty-state__icon"
                          aria-hidden="true"
                      ></i>`}
                ${showHeader ? html` <h1 class="pf-c-title pf-m-lg">${header()}</h1>` : nothing}
                ${this.slots.hasSlotted("body")
                    ? html` <div class="pf-c-empty-state__body">
                          <slot name="body"></slot>
                      </div>`
                    : nothing}
                ${this.slots.hasSlotted("primary")
                    ? html` <div class="pf-c-empty-state__primary">
                          <slot name="primary"></slot>
                      </div>`
                    : nothing}
            </div>
        </div>`;
    }
}

export function akEmptyState(properties: IEmptyState, content: SlottedTemplateResult = nothing) {
    const message =
        typeof content === "string" ? html`<span slot="body">${content}</span>` : content;
    return html`<ak-empty-state ${spread(properties as Spread)}>${message}</ak-empty-state>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-empty-state": EmptyState;
    }
}
