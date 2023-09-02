import { WizardPanel } from "@goauthentik/components/ak-wizard-main/types";
import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { consume } from "@lit-labs/context";
import { query } from "@lit/reactive-element/decorators.js";

import { styles as AwadStyles } from "./BasePanel.css";

import { applicationWizardContext } from "./ak-application-wizard-context-name";
import type { WizardState, WizardStateUpdate } from "./types";

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
    public wizard!: WizardState;

    // This used to be more complex; now it just establishes the event name.
    dispatchWizardUpdate(update: WizardStateUpdate) {
        this.dispatchCustomEvent("ak-application-wizard-update", update);
    }
}

export default ApplicationWizardPageBase;
