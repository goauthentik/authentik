import { Form } from "#elements/forms/Form";

import { WizardPage } from "#admin/wizard/WizardPage";

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

    nextCallback = async (): Promise<boolean> => {
        if (!this.children.length) {
            throw new TypeError(`No child elements found in ${this.slot}.`);
        }

        const form = Array.from(this.children).find((childElement) => {
            return childElement instanceof Form;
        });

        if (!form) {
            throw new TypeError(`${this.slot} does not contain a Form element.`);
        }

        if (!form.reportValidity()) {
            return false;
        }

        const formPromise = form.submit(new SubmitEvent("submit"));

        if (!formPromise) {
            throw new TypeError("Expected a Promise from the Form.submit() method.");
        }

        return formPromise
            .then((data) => {
                this.host.state[this.slot] = data;
                this.host.canBack = false;

                return true;
            })
            .catch(() => false);
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-page-form": FormWizardPage;
    }
}
