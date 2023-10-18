import { consume } from "@lit-labs/context";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { state } from "@lit/reactive-element/decorators/state.js";
import { LitElement, html } from "lit";

import applicationWizardContext from "../ContextIdentity";
import type { ApplicationWizardState } from "../types";

@customElement("ak-application-context-display-for-test")
export class ApplicationContextDisplayForTest extends LitElement {
    @consume({ context: applicationWizardContext, subscribe: true })
    @state()
    private wizard!: ApplicationWizardState;

    render() {
        return html`<div><pre>${JSON.stringify(this.wizard, null, 2)}</pre></div>`;
    }
}
