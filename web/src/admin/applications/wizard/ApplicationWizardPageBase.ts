import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { consume } from "@lit-labs/context";
import { state } from "@lit/reactive-element/decorators/state.js";

import { styles as AwadStyles } from "./ak-application-wizard-application-details.css";

import type { WizardState } from "./ak-application-wizard-context";
import { applicationWizardContext } from "./ak-application-wizard-context-name";

export class ApplicationWizardPageBase extends CustomEmitterElement(AKElement) {
    static get styles() {
        return AwadStyles;
    }

    // @ts-expect-error
    @consume({ context: applicationWizardContext, subscribe: true })
    @state()
    public wizard!: WizardState;

    dispatchWizardUpdate(update: Partial<WizardState>) {
        this.dispatchCustomEvent("ak-wizard-update", {
            ...this.wizard,
            ...update,
        });
    }
}

export default ApplicationWizardPageBase;
