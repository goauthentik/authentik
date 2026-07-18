import "#admin/applications/ApplicationForm";
import "#elements/Spinner";
import "#elements/forms/ModalForm";

import { AKElement } from "#elements/Base";
import { ModalInvokerButton } from "#elements/dialogs";
import { SlottedTemplateResult } from "#elements/types";

import { ApplicationForm } from "#admin/applications/ApplicationForm";

import { Provider } from "@goauthentik/api";

import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";

@customElement("ak-provider-related-application")
export class RelatedApplicationButton extends AKElement {
    static styles: CSSResult[] = [PFButton];

    @property({ attribute: false })
    public provider?: Provider | null = null;

    @property({ type: String })
    public mode: "primary" | "backchannel" = "primary";

    protected override render(): SlottedTemplateResult {
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

        return ModalInvokerButton(ApplicationForm, {
            provider: this.provider?.pk,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-related-application": RelatedApplicationButton;
    }
}
