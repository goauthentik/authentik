import { WizardPanel } from "@goauthentik/components/ak-wizard-main/types";
import { AKElement } from "@goauthentik/elements/Base";
import { KeyUnknown, serializeForm } from "@goauthentik/elements/forms/Form";
import { HorizontalFormElement } from "@goauthentik/elements/forms/HorizontalFormElement";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { consume } from "@lit-labs/context";
import { query } from "@lit/reactive-element/decorators.js";

import { styles as AwadStyles } from "./BasePanel.css";

import { applicationWizardContext } from "./ContextIdentity";
import type { ApplicationWizardState, ApplicationWizardStateUpdate } from "./types";

/**
 * Application Wizard Base Panel
 *
 * All of the displays in our system inherit from this object, which supplies the basic CSS for all
 * the inputs we display, as well as the values and validity state for the form currently being
 * displayed.
 *
 */

export class ApplicationWizardPageBase
    extends CustomEmitterElement(AKElement)
    implements WizardPanel
{
    static get styles() {
        return AwadStyles;
    }

    @consume({ context: applicationWizardContext })
    public wizard!: ApplicationWizardState;

    @query("form")
    form!: HTMLFormElement;

    /**
     * Provide access to the values on the current form. Child implementations use this to craft the
     * update that will be sent using `dispatchWizardUpdate` below.
     */
    get formValues(): KeyUnknown | undefined {
        const elements = [
            ...Array.from(
                this.form.querySelectorAll<HorizontalFormElement>("ak-form-element-horizontal"),
            ),
            ...Array.from(this.form.querySelectorAll<HTMLElement>("[data-ak-control=true]")),
        ];
        return serializeForm(elements as unknown as NodeListOf<HorizontalFormElement>);
    }

    /**
     * Provide access to the validity of the current form. Child implementations use this to craft
     * the update that will be sent using `dispatchWizardUpdate` below.
     */
    get valid() {
        return this.form.checkValidity();
    }

    rendered = false;

    /**
     * Provide a single source of truth for the token used to notify the orchestrator that an event
     * happens. The token `ak-wizard-update` is used by the Wizard framework's reactive controller
     * to route "data on the current step has changed" events to the orchestrator.
     */
    dispatchWizardUpdate(update: ApplicationWizardStateUpdate) {
        this.dispatchCustomEvent("ak-wizard-update", update);
    }
}

export default ApplicationWizardPageBase;
