import { Form, KeyUnknown } from "@goauthentik/elements/forms/Form";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-wizard-form")
export abstract class WizardForm extends Form<KeyUnknown> {
    viewportCheck = false;

    @property({ attribute: false })
    nextDataCallback!: (data: KeyUnknown) => Promise<boolean>;

    /* Override the traditional behavior of the form and instead simply serialize the form and push
     * it's contents to the next page.
     */
    async submit(): Promise<boolean | undefined> {
        const data = this.serializeForm();
        if (!data) {
            return;
        }
        const files = this.getFormFiles();
        const finalData = Object.assign({}, data, files);
        return this.nextDataCallback(finalData);
    }
}

export class WizardFormPage extends WizardPage {
    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFButton, PFForm, PFAlert, PFInputGroup, PFFormControl];
    }

    inputCallback(): void {
        const form = this.shadowRoot?.querySelector<HTMLFormElement>("form");
        if (!form) {
            return;
        }
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
        if (response === undefined) {
            return false;
        }
        return response;
    };

    nextDataCallback: (data: KeyUnknown) => Promise<boolean> = async (): Promise<boolean> => {
        return false;
    };

    renderForm(): TemplateResult {
        return html``;
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
