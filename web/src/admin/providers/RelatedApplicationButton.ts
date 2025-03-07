import "@goauthentik/admin/applications/ApplicationForm";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Spinner";
import "@goauthentik/elements/forms/ModalForm";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Provider } from "@goauthentik/api";

@customElement("ak-provider-related-application")
export class RelatedApplicationButton extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton];
    }

    @property({ attribute: false })
    provider?: Provider;

    @property()
    mode: "primary" | "backchannel" = "primary";

    render(): TemplateResult {
        if (this.mode === "primary" && this.provider?.assignedApplicationSlug) {
            return html`<a href="#/core/applications/${this.provider.assignedApplicationSlug}">
                ${this.provider.assignedApplicationName}
            </a>`;
        }
        if (this.mode === "backchannel" && this.provider?.assignedBackchannelApplicationSlug) {
            return html`<a href="#/core/applications/${this.provider.assignedBackchannelApplicationSlug}">
                ${this.provider.assignedBackchannelApplicationName}
            </a>`;
        }
        return html`<ak-forms-modal>
            <span slot="submit"> ${msg("Create")} </span>
            <span slot="header"> ${msg("Create Application")} </span>
            <ak-application-form slot="form" .provider=${this.provider?.pk}> </ak-application-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
        </ak-forms-modal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-related-application": RelatedApplicationButton;
    }
}
