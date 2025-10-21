import "#admin/applications/ApplicationForm";
import "#elements/Spinner";
import "#elements/forms/ModalForm";

import { formatCreateMessage, formatNewMessage } from "#common/i18n/actions";
import { EntityLabel } from "#common/i18n/nouns";

import { AKElement } from "#elements/Base";

import { Provider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-provider-related-application")
export class RelatedApplicationButton extends AKElement {
    static styles: CSSResult[] = [PFBase, PFButton];

    protected entityLabel: EntityLabel = {
        singular: msg("Application"),
        plural: msg("Applications"),
    };

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
            return html`<a
                href="#/core/applications/${this.provider.assignedBackchannelApplicationSlug}"
            >
                ${this.provider.assignedBackchannelApplicationName}
            </a>`;
        }
        return html`<ak-forms-modal>
            <span slot="submit">${formatCreateMessage(this.entityLabel)}</span>
            <span slot="header">${formatNewMessage(this.entityLabel)}</span>

            <ak-application-form slot="form" .provider=${this.provider?.pk}> </ak-application-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${formatNewMessage(this.entityLabel)}
            </button>
        </ak-forms-modal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-related-application": RelatedApplicationButton;
    }
}
