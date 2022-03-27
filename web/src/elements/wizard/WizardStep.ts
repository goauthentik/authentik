import { TemplateResult, html } from "lit";

import { WizardStepContainer } from "./WizardStepContainer";

export abstract class WizardStep {
    host!: WizardStepContainer;

    isValid(): boolean {
        return false;
    }

    activeCallback: () => Promise<void> = () => {
        return Promise.resolve();
    };
    nextCallback: () => Promise<boolean> = async () => {
        return true;
    };

    abstract renderNavList(): TemplateResult;

    render(): TemplateResult {
        return html``;
    }
}
