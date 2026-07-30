import { Form } from "#elements/forms/Form";
import { WizardPage, WizardPageState } from "#elements/wizard/WizardPage";

import { customElement } from "lit/decorators.js";

export type FormWizardPageActiveCallback<S extends WizardPageState> = (
    host: FormWizardPage<S>,
) => void | Promise<void>;

/**
 * This Wizard page is used for proxy forms with the older-style
 * wizards
 */
@customElement("ak-wizard-page-form")
export class FormWizardPage<S extends WizardPageState = WizardPageState> extends WizardPage<S> {
    public activePageCallback: FormWizardPageActiveCallback<S> = async () => {
        return Promise.resolve();
    };

    public override activeCallback = async () => {
        this.host.valid = true;

        this.activePageCallback(this);
    };

    public override nextCallback = async (): Promise<boolean> => {
        if (!this.children.length) {
            throw new TypeError(`No child elements found in ${this.slot}.`);
        }

        const form = Iterator.from(this.children).find((childElement) => {
            return childElement instanceof Form;
        });

        if (!form) {
            throw new TypeError(`${this.slot} does not contain a Form element.`);
        }

        if (!form.reportValidity()) {
            return false;
        }

        return form
            .submit(new SubmitEvent("submit"))
            .then((responseData) => {
                const { slot, host } = this;

                if (!slot) {
                    this.logger.error(
                        "Cannot assign form data to wizard state: slot is undefined.",
                        {
                            formData: responseData,
                        },
                    );
                    throw new TypeError("Expected slot to be defined on WizardPage.");
                }

                Object.assign(host.state, { [this.slot]: responseData } as Partial<S>);

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
