import { CSSResult, LitElement, PropertyDeclaration, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Wizard } from "./Wizard";

@customElement("ak-wizard-page")
export class WizardPage extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, AKGlobal];
    }

    @property()
    sidebarLabel: () => string = () => {
        return "UNNAMED";
    };

    get host(): Wizard {
        return this.parentElement as Wizard;
    }

    activeCallback: () => Promise<void> = () => {
        this.host.isValid = false;
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
