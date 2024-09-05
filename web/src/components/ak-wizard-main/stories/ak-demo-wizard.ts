import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AkWizard } from "../AkWizard";
import { WizardStep } from "../AkWizardStep";
import { WizardButton } from "../types";

type WizardStateUpdate = {
    message: string;
};

class Step1 extends WizardStep {
    id = "test-step-1";
    label = "Test Step 1";
    disabled = false;
    valid = true;
    get buttons(): WizardButton[] {
        return [{ kind: "next", destination: "test-step-2" }, { kind: "cancel" }];
    }

    render() {
        return html`<h2>This space intentionally left blank</h2>`;
    }
}

class Step2 extends WizardStep {
    id = "test-step-2";
    label = "Test Step 2";
    disabled = false;
    valid = true;
    get buttons(): WizardButton[] {
        return [{ kind: "back", destination: "test-step-1" }, { kind: "close" }];
    }
    render() {
        return html`<h2>This space also intentionally left blank</h2>`;
    }
}

@customElement("ak-demo-wizard")
export class ApplicationWizard extends AkWizard<WizardStateUpdate, WizardStep> {
    static get styles() {
        return [PFBase, PFButton, PFRadio];
    }

    constructor() {
        super(msg("Open Wizard"), msg("Demo Wizard"), msg("Run the demo wizard"));
    }

    newSteps() {
        return [new Step1(), new Step2()];
    }

    close() {
        super.close();
        this.frame.value!.open = false;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-demo-wizard": ApplicationWizard;
    }
}
