import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { consume } from "@lit-labs/context";
import { query, state } from "@lit/reactive-element/decorators.js";

import { styles as AwadStyles } from "./BasePanel.css";

import { applicationWizardContext } from "./ak-application-wizard-context-name";
import type { WizardState } from "./types";

export class ApplicationWizardPageBase extends CustomEmitterElement(AKElement) {
    static get styles() {
        return AwadStyles;
    }

    @query("form")
    form!: HTMLFormElement;

    rendered = false;

    // @ts-expect-error
    @consume({ context: applicationWizardContext })
    public wizard!: WizardState;

    shouldUpdate(changedProperties: Map<string, any>) {
        if (!this.rendered) {
            this.rendered = true;
            return true;
        }
        return (changedProperties.size !== 0)
    }
    
    dispatchWizardUpdate(update: Partial<WizardState>) {
        // TODO: Incorporate this into the message heading upward: "the current step is valid."

        this.dispatchCustomEvent("ak-application-wizard-update", {
            ...this.wizard,
            ...update,
        });
    }
}

export default ApplicationWizardPageBase;
