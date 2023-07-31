import { consume } from "@lit-labs/context";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { state } from "@lit/reactive-element/decorators/state.js";
import { LitElement, html } from "lit";

import type { WizardState } from "../ak-application-wizard-context";
import applicationWizardContext from "../ak-application-wizard-context-name";

@customElement("ak-application-context-display-for-test")
export class ApplicationContextDisplayForTest extends LitElement {
    @consume({ context: applicationWizardContext, subscribe: true })
    @state()
    private wizard!: WizardState;

    render() {
        return html`<div><pre>${JSON.stringify(this.wizard, null, 2)}</pre></div>`;
    }
}
