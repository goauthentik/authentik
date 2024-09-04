import { type WizardButton } from "@goauthentik/components/ak-wizard-main/types";

import { msg } from "@lit/localize";
import { html } from "lit";

import { ApplicationWizardStep } from "../types";
import "./ak-application-wizard-submit.js";

export class SubmitStep implements ApplicationWizardStep {
    id = "submit";
    label = msg("Submit Application");
    disabled = true;
    valid = false;

    get buttons(): WizardButton[] {
        return this.valid
            ? [{ kind: "close" }]
            : [{ kind: "back", target: "provider-details" }, { kind: "cancel" }];
    }

    render() {
        return html`<ak-application-wizard-submit></ak-application-wizard-submit>`;
    }
}
