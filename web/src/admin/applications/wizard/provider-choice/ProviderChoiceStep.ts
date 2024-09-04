import { type WizardButton } from "@goauthentik/components/ak-wizard-main/types";

import { msg } from "@lit/localize";
import { html } from "lit";

import { ApplicationWizardStep } from "../types";
import "./ak-application-wizard-provider-choice.js";

export class ProviderChoiceStep implements ApplicationWizardStep {
    id = "provider-choice";
    label = msg("Provider Type");
    disabled = false;
    valid = false;

    get buttons(): WizardButton[] {
        return [
            this.valid
                ? { kind: "next", target: "provider-details" }
                : { kind: "next", disabled: true },
            { kind: "back", target: "application" },
            { kind: "cancel" },
        ];
    }

    render() {
        // prettier-ignore
        return html`<ak-application-wizard-provider-choice
          ></ak-application-wizard-provider-choice> `;
    }
}
