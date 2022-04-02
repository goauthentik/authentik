import { LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-wizard-page")
export class WizardPage extends LitElement {
    @property()
    sidebarLabel: () => string = () => {
        return "UNNAMED";
    };

    isValid(): boolean {
        return false;
    }

    activeCallback: () => Promise<void> = () => {
        return Promise.resolve();
    };
    nextCallback: () => Promise<boolean> = async () => {
        return true;
    };

    render(): TemplateResult {
        return html`<slot></slot>`;
    }
}
