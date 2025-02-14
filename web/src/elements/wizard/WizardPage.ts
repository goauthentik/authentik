import { AKElement } from "@goauthentik/elements/Base";
import { Wizard } from "@goauthentik/elements/wizard/Wizard";

import { CSSResult, PropertyDeclaration, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * Callback for when the page is brought into view.
 */
export type WizardPageActiveCallback = () => void | Promise<void>;

/**
 * Callback for when the next button is pressed.
 *
 * @returns `true` if the wizard can proceed to the next page, `false` otherwise.
 */
export type WizardPageNextCallback = () => boolean | Promise<boolean>;

@customElement("ak-wizard-page")
export class WizardPage extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase];
    }

    /**
     * The label to display in the sidebar for this page.
     *
     * Override this to provide a custom label.
     * @todo: Should this be a getter or static property?
     */
    @property()
    sidebarLabel = (): string => {
        return "UNNAMED";
    };

    get host(): Wizard {
        return this.parentElement as Wizard;
    }

    /**
     * Reset the page to its initial state.
     *
     * @abstract
     */
    public reset(): void | Promise<void> {
        console.debug(`authentik/wizard ${this.localName}: reset)`);
    }

    /**
     * Called when this is the page brought into view.
     */
    activeCallback: WizardPageActiveCallback = () => {
        this.host.isValid = false;
    };

    /**
     * Called when the `next` button on the wizard is pressed. For forms, results in the submission
     * of the current form to the back-end before being allowed to proceed to the next page. This is
     * sub-optimal if we want to collect multiple bits of data before finishing the whole course.
     *
     * @returns `true` if the wizard can proceed to the next page, `false` otherwise.
     */
    nextCallback: WizardPageNextCallback = () => {
        return Promise.resolve(true);
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-wizard-page": WizardPage;
    }
}
