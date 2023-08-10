import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { consume } from "@lit-labs/context";
import { query, state } from "@lit/reactive-element/decorators.js";

import { styles as AwadStyles } from "./ApplicationWizardCss";
import type { WizardState } from "./ak-application-wizard-context";
import { applicationWizardContext } from "./ak-application-wizard-context-name";

export class ApplicationWizardPageBase extends CustomEmitterElement(AKElement) {
    static get styles() {
        return AwadStyles;
    }

    @query("form")
    form!: HTMLFormElement;

    // @ts-expect-error
    @consume({ context: applicationWizardContext, subscribe: true })
    @state()
    public wizard!: WizardState;

    dispatchWizardUpdate(update: Partial<WizardState>) {
        // TODO: Incorporate this into the message heading upward: "the current step is valid."
        console.log(this.form.reportValidity());

        this.dispatchCustomEvent("ak-application-wizard-update", {
            ...this.wizard,
            ...update,
        });
    }
}

export default ApplicationWizardPageBase;
