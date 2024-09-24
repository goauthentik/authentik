import { styles } from "@goauthentik/admin/applications/wizard/ApplicationWizardFormStepStyles.css.js";
import { WizardStep } from "@goauthentik/components/ak-wizard/WizardStep.js";
import {
    NavigationUpdate,
    WizardNavigationEvent,
    WizardUpdateEvent,
} from "@goauthentik/components/ak-wizard/events";
import { KeyUnknown, serializeForm } from "@goauthentik/elements/forms/Form";
import { HorizontalFormElement } from "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { property, query } from "lit/decorators.js";

import { type ApplicationWizardStateUpdate } from "./types";

export class ApplicationWizardStep extends WizardStep {
    static get styles() {
        return [...WizardStep.styles, ...styles];
    }

    @property({ type: Object, attribute: false })
    wizard!: ApplicationWizardStateUpdate;

    // As recommended in [WizardStep](../../../components/ak-wizard/WizardStep.ts), we override
    // these fields and provide them to all the child classes.
    wizardTitle = msg("New application");
    wizardDescription = msg("Create a new application");
    canCancel = true;

    // This should be overriden in the children for more precise targeting.
    @query("form")
    form!: HTMLFormElement;

    get formValues(): KeyUnknown | undefined {
        const elements = [
            ...Array.from(
                this.form.querySelectorAll<HorizontalFormElement>("ak-form-element-horizontal")
            ),
            ...Array.from(this.form.querySelectorAll<HTMLElement>("[data-ak-control=true]")),
        ];
        return serializeForm(elements as unknown as NodeListOf<HorizontalFormElement>);
    }

    // This pattern became visible during development, and the order is important: wizard updating
    // and validation must complete before navigation is attempted.
    public handleUpdate(
        update?: ApplicationWizardStateUpdate,
        destination?: string,
        enable?: NavigationUpdate
    ) {
        // Inform ApplicationWizard of content state
        if (update) {
            this.dispatchEvent(new WizardUpdateEvent(update));
        }

        // Inform WizardStepManager of steps state
        if (destination || enable) {
            this.dispatchEvent(new WizardNavigationEvent(destination, enable));
        }
    }
}
