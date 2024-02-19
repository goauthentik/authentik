import { Form } from "@goauthentik/elements/forms/Form";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

/**
 * This Wizard page is used for proxy forms with the older-style
 * wizards
 */
@customElement("ak-wizard-page-form")
export class FormWizardPage extends WizardPage {
    activePageCallback: (context: FormWizardPage) => Promise<void> = async () => {
        return Promise.resolve();
    };

    activeCallback = async () => {
        this.host.isValid = true;
        this.activePageCallback(this);
    };

    nextCallback = async () => {
        const form = this.querySelector<Form<unknown>>("*");
        if (!form) {
            return Promise.reject(msg("No form found"));
        }
        const formPromise = form.submit(new Event("submit"));
        if (!formPromise) {
            return Promise.reject(msg("Form didn't return a promise for submitting"));
        }
        return formPromise
            .then((data) => {
                this.host.state[this.slot] = data;
                this.host.canBack = false;
                return true;
            })
            .catch(() => {
                return false;
            });
    };
}
