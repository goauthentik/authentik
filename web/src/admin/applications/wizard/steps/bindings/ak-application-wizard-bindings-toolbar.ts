import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-application-wizard-bindings-toolbar")
export class ApplicationWizardBindingsToolbar extends AKElement {
    static get styles() {
        return [PFBase, PFButton, PFToolbar];
    }

    @property({ type: Boolean, attribute: "can-delete", reflect: true })
    canDelete = false;

    notify(eventName: string) {
        this.dispatchEvent(new Event(eventName, { bubbles: true, composed: true }));
    }

    render() {
        return html`
            <div class="pf-c-toolbar">
                <div class="pf-c-toolbar__content">
                    <div class="pf-c-toolbar__group">
                        <button
                            class="pf-c-button pf-m-primary"
                            @click=${() => this.notify("clickNew")}
                        >
                            ${msg("Bind existing policy/group/user")}
                        </button>
                    </div>
                    <button
                        class="pf-c-button pf-m-danger"
                        ?disabled=${!this.canDelete}
                        @click=${() => this.notify("clickDelete")}
                    >
                        ${msg("Delete")}
                    </button>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-bindings-toolbar": ApplicationWizardBindingsToolbar;
    }
}
