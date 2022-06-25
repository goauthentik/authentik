import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Form, KeyUnknown } from "../forms/Form";
import { WizardPage } from "./WizardPage";

@customElement("ak-wizard-form")
export class WizardForm extends Form<KeyUnknown> {
    viewportCheck = false;

    @property({ attribute: false })
    nextDataCallback!: (data: KeyUnknown) => Promise<boolean>;

    submit(): Promise<boolean> | undefined {
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
        return [PFBase, PFCard, PFButton, PFForm, PFAlert, PFInputGroup, PFFormControl, AKGlobal];
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

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    nextDataCallback: (data: KeyUnknown) => Promise<boolean> = async (data): Promise<boolean> => {
        return false;
    };

    renderForm(): TemplateResult {
        return html``;
    }

    firstUpdated(): void {
        this.inputCallback();
        this.host.isValid = false;
    }

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
