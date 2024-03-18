import { PFSize } from "@goauthentik/common/enums.js";
import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-empty-state")
export class EmptyState extends AKElement {
    @property({ type: String })
    icon = "";

    @property({ type: Boolean })
    loading = false;

    @property({ type: Boolean })
    fullHeight = false;

    @property()
    header = "";

    static get styles(): CSSResult[] {
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

    render(): TemplateResult {
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
                <h1 class="pf-c-title pf-m-lg">${this.header}</h1>
                <div class="pf-c-empty-state__body">
                    <slot name="body"></slot>
                </div>
                <div class="pf-c-empty-state__primary">
                    <slot name="primary"></slot>
                </div>
            </div>
        </div>`;
    }
}
