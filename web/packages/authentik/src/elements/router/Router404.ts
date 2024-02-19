import { AKElement } from "@goauthentik/elements/Base";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-router-404")
export class Router404 extends AKElement {
    @property()
    url = "";

    static get styles(): CSSResult[] {
        return [PFBase, PFEmptyState, PFTitle];
    }

    render(): TemplateResult {
        return html`<div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <i class="fas fa-question-circle pf-c-empty-state__icon" aria-hidden="true"></i>
                <h1 class="pf-c-title pf-m-lg">${msg("Not found")}</h1>
                <div class="pf-c-empty-state__body">
                    ${msg(str`The URL "${this.url}" was not found.`)}
                </div>
                <a href="#/" class="pf-c-button pf-m-primary" type="button"
                    >${msg("Return home")}</a
                >
            </div>
        </div>`;
    }
}
