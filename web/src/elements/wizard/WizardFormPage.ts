import { Form } from "#elements/forms/Form";
import { WizardPage } from "#elements/wizard/WizardPage";

import { CSSResult, html, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export abstract class WizardForm extends Form {
    public override viewportCheck = false;

    @property({ attribute: false })
    public nextDataCallback!: (data: Record<string, unknown>) => Promise<boolean>;

    /* Override the traditional behavior of the form and instead simply serialize the form and push
     * it's contents to the next page.
     */
    public override async submit(): Promise<boolean | undefined> {
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
    public static override styles: CSSResult[] = [
        PFBase,
        PFCard,
        PFButton,
        PFForm,
        PFAlert,
        PFInputGroup,
        PFFormControl,
    ];

    protected inputCallback(): void {
        const form = this.shadowRoot?.querySelector<HTMLFormElement>("form");

        if (!form) return;

        const state = form.checkValidity();
        this.host.isValid = state;
    }

    public override nextCallback = async (): Promise<boolean> => {
        const form = this.shadowRoot?.querySelector<WizardForm>("ak-wizard-form");

        if (!form) {
            console.warn("authentik/wizard: could not find form element");
            return false;
        }

        const response = await form.submit();

        return Boolean(response);
    };

    protected nextDataCallback: (data: Record<string, unknown>) => Promise<boolean> =
        async (): Promise<boolean> => {
            return false;
        };

    protected renderForm(): TemplateResult {
        return html``;
    }

    public override activeCallback = async () => {
        this.inputCallback();
    };

    public override render(): TemplateResult {
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
