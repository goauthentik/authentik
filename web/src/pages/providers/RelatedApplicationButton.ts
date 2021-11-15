import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Provider } from "@goauthentik/api";

import "../../elements/Spinner";
import "../../elements/forms/ModalForm";
import "../../pages/applications/ApplicationForm";

@customElement("ak-provider-related-application")
export class RelatedApplicationButton extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton];
    }

    @property({ attribute: false })
    provider?: Provider;

    render(): TemplateResult {
        if (this.provider?.assignedApplicationSlug) {
            return html`<a href="#/core/applications/${this.provider.assignedApplicationSlug}">
                ${this.provider.assignedApplicationName}
            </a>`;
        }
        return html`<ak-forms-modal>
            <span slot="submit"> ${t`Create`} </span>
            <span slot="header"> ${t`Create Application`} </span>
            <ak-application-form slot="form" .provider=${this.provider?.pk}> </ak-application-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
        </ak-forms-modal>`;
    }
}
