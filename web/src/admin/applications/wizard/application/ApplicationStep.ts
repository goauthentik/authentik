import { type WizardButton } from "@goauthentik/components/ak-wizard-main/types";

import { msg } from "@lit/localize";
import { html } from "lit";

import { ApplicationWizardStep } from "../types";
import "./ak-application-wizard-application-details.js";

export class ApplicationStep implements ApplicationWizardStep {
    id = "application";
    label = msg("Application Details");
    disabled = false;
    valid = false;
    get buttons(): WizardButton[] {
        return [
            this.valid
                ? { kind: "next", target: "provider-choice" }
                : { kind: "next", disabled: true },
            { kind: "cancel" },
        ];
    }
    render() {
        return html`<ak-application-wizard-application-details></ak-application-wizard-application-details>`;
    }
}
