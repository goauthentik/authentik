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

    wizardTitle = msg("New application");

    wizardDescription = msg("Create a new application");

    canCancel = true;

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

    handleUpdate(
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
