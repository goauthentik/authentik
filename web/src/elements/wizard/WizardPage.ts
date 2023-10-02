import { AKElement } from "@goauthentik/elements/Base";
import { Wizard } from "@goauthentik/elements/wizard/Wizard";

import { CSSResult, PropertyDeclaration, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-wizard-page")
export class WizardPage extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase];
    }

    @property()
    sidebarLabel: () => string = () => {
        return "UNNAMED";
    };

    get host(): Wizard {
        return this.parentElement as Wizard;
    }

    /**
     * Called when this is the page brought into view
     */
    activeCallback: () => Promise<void> = async () => {
        this.host.isValid = false;
    };

    /**
     * Called when the `next` button on the wizard is pressed. For forms, results in the submission
     * of the current form to the back-end before being allowed to proceed to the next page. This is
     * sub-optimal if we want to collect multiple bits of data before finishing the whole course.
     */
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
                (el as AKElement).requestUpdate();
            }
        });
        return super.requestUpdate(name, oldValue, options);
    }

    render(): TemplateResult {
        return html`<slot></slot>`;
    }
}
