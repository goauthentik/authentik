import { type WizardButton } from "@goauthentik/components/ak-wizard-main/types";

import { msg } from "@lit/localize";
import { html } from "lit";

import { ApplicationWizardStep } from "../types";
import "./ak-application-wizard-provider.js";

export class ProviderStep implements ApplicationWizardStep {
    id = "provider-details";
    label = msg("Provider Configuration");
    disabled = true;
    valid = false;
    get buttons(): WizardButton[] {
        return [
            this.valid
                ? { kind: "next", label: msg("Submit"), target: "submit" }
                : { kind: "next", label: msg("Submit"), disabled: true },
            { kind: "back", target: "provider-choice" },
            { kind: "cancel" },
        ];
    }

    render() {
        return html`<ak-application-wizard-provider></ak-application-wizard-provider>`;
    }
}
