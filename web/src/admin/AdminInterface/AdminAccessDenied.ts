import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-admin-access-denied")
export class AdminAccessDenied extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFEmptyState];
    }

    @property()
    permission?: string;

    render(): TemplateResult {
        return html`<div class="pf-c-page__main">
            <div class="pf-c-empty-state" style="height: 100%; display: flex; align-items: center; justify-content: center;">
                <div class="pf-c-empty-state__content">
                    <i class="fas fa-lock pf-c-empty-state__icon" aria-hidden="true"></i>
                    <h1 class="pf-c-title pf-m-lg">${msg("Access Denied")}</h1>
                    <div class="pf-c-empty-state__body">
                        ${msg("You do not have permission to access this page.")}
                    </div>
                    <div class="pf-c-empty-state__body">
                        ${msg("If this is unexpected, please contact your administrator.")}
                    </div>
                    ${this.permission
                        ? html`<div class="pf-c-empty-state__body">
                              <small>${msg("Required permission:")} <code>${this.permission}</code></small>
                          </div>`
                        : ""}
                    <div class="pf-c-empty-state__primary">
                        <a href="#/" class="pf-c-button pf-m-primary">
                            ${msg("Return to home")}
                        </a>
                    </div>
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-access-denied": AdminAccessDenied;
    }
}
