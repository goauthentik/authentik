import { Form } from "#elements/forms/Form";
import { WizardPage } from "#elements/wizard/WizardPage";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

/**
 * This Wizard page is used for proxy forms with the older-style
 * wizards
 */
@customElement("ak-wizard-page-form")
export class FormWizardPage extends WizardPage {
    public activePageCallback?: (context: FormWizardPage) => Promise<void>;

    public override activeCallback = async () => {
        this.host.valid = true;
        this.activePageCallback?.(this);
    };

    public override nextCallback = (): Promise<boolean> => {
        const form = this.querySelector("*");

        if (!form) {
            throw new TypeError(msg("No child elements found in wizard page"));
        }

        if (!(form instanceof Form || form instanceof HTMLFormElement)) {
            console.warn("authentik/wizard: form inside the form slot is not a Form", form);
            throw new TypeError(msg("Wizard page doesn't contain a form"));
        }

        const validity = form.reportValidity();

        if (!validity) {
            return Promise.resolve(false);
        }

        const submitResult = form.submit(new SubmitEvent("submit"));

        return Promise.resolve(submitResult)
            .then((data) => {
                this.host.state[this.slot] = data;
                this.host.previousNavigation = false;

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
