import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";
import { BackStep, CancelWizard, CloseWizard, NextStep } from "../commonWizardButtons";
import { msg } from "@lit/localize";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { WizardStep } from "@goauthentik/components/ak-wizard-main/types";
import { AkWizard } from "../AkWizard";

type WizardStateUpdate = {
    message: string;
};

const dummySteps: WizardStep[] = [
    {
        label: "Test Step1",
        render: () => html`<h2>This space intentionally left blank today</h2>`,
        disabled: false,
        buttons: [NextStep, CancelWizard],
    },
    {
        label: "Test Step 2",
        render: () => html`<h2>This space also intentionally left blank</h2>`,
        disabled: false,
        buttons: [BackStep, CloseWizard],
    },
];

@customElement("ak-demo-wizard")
export class ApplicationWizard extends AkWizard<WizardStateUpdate, WizardStep> {
    static get styles() {
        return [PFBase, PFButton, PFRadio];
    }

    constructor() {
        super(msg("Open Wizard"), msg("Demo Wizard"), msg("Run the demo wizard"));
        this.steps = [...dummySteps];
    }

    close() {
        this.frame.value!.open = false;
    }

}
