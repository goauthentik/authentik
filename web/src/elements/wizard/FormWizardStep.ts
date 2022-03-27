import { t } from "@lingui/macro";

import { TemplateResult } from "lit";

import { Form } from "../forms/Form";
import { WizardStep } from "./WizardStep";

export class FormWizardStep extends WizardStep {
    _valid = true;

    isValid(): boolean {
        return this._valid;
    }
    nextCallback = async () => {
        const form = this.host.shadowRoot?.querySelector<Form<unknown>>(
            ".pf-c-wizard__main-body > *",
        );
        if (!form) {
            return Promise.reject(t`No form found`);
        }
        const formPromise = form.submit(new Event("submit"));
        if (!formPromise) {
            return Promise.reject(t`Form didn't return a promise for submitting`);
        }
        return formPromise
            .then(() => {
                return true;
            })
            .catch(() => {
                return false;
            });
    };
    renderNavList(): TemplateResult {
        throw new Error("Method not implemented.");
    }
}
