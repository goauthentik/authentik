import type { WizardStep } from "@goauthentik/components/ak-wizard-main/types";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AkWizard } from "../AkWizard";

type WizardStateUpdate = {
    message: string;
};

const dummySteps: WizardStep[] = [
    {
        id: "test-step-1",
        label: "Test Step1",
        render: () => html`<h2>This space intentionally left blank today</h2>`,
        disabled: false,
        buttons: [{ kind: "next", target: "test-step-2" }, { kind: "cancel" }],
    },
    {
        id: "test-step-2",
        label: "Test Step 2",
        render: () => html`<h2>This space also intentionally left blank</h2>`,
        disabled: false,
        buttons: [{ kind: "back", target: "test-step-1" }, { kind: "close" }],
    },
];

@customElement("ak-demo-wizard")
export class ApplicationWizard extends AkWizard<WizardStateUpdate, WizardStep> {
    static get styles() {
        return [PFBase, PFButton, PFRadio];
    }

    override canCancel = true;

    constructor() {
        super(msg("Open Wizard"), msg("Demo Wizard"), msg("Run the demo wizard"));
        this.reset(dummySteps);
    }

    close() {
        this.frame.value!.open = false;
        this.reset();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-demo-wizard": ApplicationWizard;
    }
}
