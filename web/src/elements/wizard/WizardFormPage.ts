import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";
import { WizardPage } from "#elements/wizard/WizardPage";

import { CSSResult, html, nothing, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

export abstract class WizardForm extends Form {
    viewportCheck = false;

    @property({ attribute: false })
    nextDataCallback!: (data: Record<string, unknown>) => Promise<boolean>;

    /* Override the traditional behavior of the form and instead simply serialize the form and push
     * it's contents to the next page.
     */
    async submit(): Promise<boolean | undefined> {
        const data = this.serialize();

        if (!data) return;

        const files = this.files();

        return this.nextDataCallback({
            ...data,
            ...files,
        });
    }
}

export class WizardFormPage extends WizardPage {
    static styles: CSSResult[] = [PFCard, PFButton, PFForm, PFAlert, PFInputGroup, PFFormControl];

    inputCallback(): void {
        const form = this.shadowRoot?.querySelector<HTMLFormElement>("form");

        if (!form) return;

        const state = form.checkValidity();
        this.host.isValid = state;
    }

    nextCallback = async (): Promise<boolean> => {
        const form = this.shadowRoot?.querySelector<WizardForm>("ak-wizard-form");

        if (!form) {
            console.warn("authentik/wizard: could not find form element");
            return false;
        }

        const response = await form.submit();

        return Boolean(response);
    };

    nextDataCallback: (data: Record<string, unknown>) => Promise<boolean> =
        async (): Promise<boolean> => {
            return false;
        };

    renderForm(): SlottedTemplateResult {
        return nothing;
    }

    activeCallback = async () => {
        this.inputCallback();
    };

    render(): TemplateResult {
        return html`
            <ak-wizard-form
                .nextDataCallback=${this.nextDataCallback}
                @input=${() => this.inputCallback()}
            >
                ${this.renderForm()}
            </ak-wizard-form>
        `;
    }
}
