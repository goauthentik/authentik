import { LitElement, PropertyDeclaration, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Wizard } from "./Wizard";

@customElement("ak-wizard-page")
export class WizardPage extends LitElement {
    @property()
    sidebarLabel: () => string = () => {
        return "UNNAMED";
    };

    isValid(): boolean {
        return this._isValid;
    }

    get host(): Wizard {
        return this.parentElement as Wizard;
    }

    _isValid = false;

    activeCallback: () => Promise<void> = () => {
        return Promise.resolve();
    };
    nextCallback: () => Promise<boolean> = async () => {
        return true;
    };

    requestUpdate(
        name?: PropertyKey,
        oldValue?: unknown,
        options?: PropertyDeclaration<unknown, unknown>,
    ): void {
        this.querySelectorAll("*").forEach((el) => {
            if ("requestUpdate" in el) {
                (el as LitElement).requestUpdate();
            }
        });
        return super.requestUpdate(name, oldValue, options);
    }

    render(): TemplateResult {
        return html`<slot></slot>`;
    }
}
