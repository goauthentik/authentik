import { WizardPanel } from "@goauthentik/components/ak-wizard-main/types";
import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { consume } from "@lit-labs/context";
import { query } from "@lit/reactive-element/decorators.js";

import { styles as AwadStyles } from "./BasePanel.css";

import { applicationWizardContext } from "./ContextIdentity";
import type { ApplicationWizardState, ApplicationWizardStateUpdate } from "./types";

export class ApplicationWizardPageBase
    extends CustomEmitterElement(AKElement)
    implements WizardPanel
{
    static get styles() {
        return AwadStyles;
    }

    @query("form")
    form!: HTMLFormElement;

    rendered = false;

    @consume({ context: applicationWizardContext })
    public wizard!: ApplicationWizardState;

    // This used to be more complex; now it just establishes the event name.
    dispatchWizardUpdate(update: ApplicationWizardStateUpdate) {
        this.dispatchCustomEvent("ak-wizard-update", update);
    }
}

export default ApplicationWizardPageBase;
