import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-router-404")
export class Router404 extends LitElement {

    @property()
    url = "";

    static get styles(): CSSResult[] {
        return [PFBase, PFEmptyState, PFTitle];
    }

    render(): TemplateResult {
        return html`<div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <i class="fas fa-question-circle pf-c-empty-state__icon" aria-hidden="true"></i>
                <h1 class="pf-c-title pf-m-lg">${gettext("Not found")}</h1>
                <div class="pf-c-empty-state__body">
                    ${gettext(`The URL '${this.url}' was not found.`)}
                </div>
                <a href="#/" class="pf-c-button pf-m-primary" type="button">${gettext("Return home")}</a>
            </div>
        </div>`;
    }
}
